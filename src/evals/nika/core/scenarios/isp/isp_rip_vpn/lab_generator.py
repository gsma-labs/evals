#!/usr/bin/env python3
"""
Standalone lab generator for RIP Small Internet VPN topology.
Generates Kathara-compatible lab configuration WITHOUT Kathara dependency.
Output: by default size_s/size_m/size_l/topology/ containing lab.conf, *.startup, and host config subfolders.
"""

import os
from collections import defaultdict
from dataclasses import dataclass, field
from ipaddress import IPv4Interface, IPv4Network
from typing import Literal

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RIP_UTILS = os.path.join(SCRIPT_DIR, "../../_utils/rip")
WIREGUARD_KEYS_PATH = os.path.join(SCRIPT_DIR, "../../_utils/wireguard", "keys.txt")
WG_VPN_NET = "172.16.1.0/24"
WG_SERVER_IP = "172.16.1.1"


# Apache: listen only on VPN IP so web is reachable only via VPN (for VPN-connected web servers)
def _apache_ports_listen_vpn_only(vpn_ip: str) -> str:
    return f"Listen {vpn_ip}:80\n"


WG_SERVER_PORT = 51820
WG_SERVER_ENDPOINT_IP = "20.0.0.2"  # vpn_server_1 in zone 20.0.0.0/24


def assign_p2p_ips(subnet: IPv4Network) -> tuple[str, str]:
    base = subnet.network_address
    ip0 = IPv4Interface(f"{base}/31")
    ip1 = IPv4Interface(f"{base + 1}/31")
    return str(ip0), str(ip1)


FRR_BASE_TEMPLATE_RIP = """
!
! FRRouting configuration file
!
!
!  RIP CONFIGURATION
!
router rip
network 192.168.0.0/16
network {network}
redistribute static
!
log file /var/log/frr/frr.log
"""


@dataclass
class RouterMeta:
    name: str
    eth_index: int = 0
    cmd_list: list[str] = field(default_factory=list)
    host_network: IPv4Network | None = None
    image: str = "kathara/frr"
    cpus: float = 0.5
    mem: str = "256m"
    links: list[tuple[int, str]] = field(default_factory=list)
    extra_files: dict[str, str] = field(default_factory=dict)


@dataclass
class HostMeta:
    name: str
    eth_index: int = 0
    cmd_list: list[str] = field(default_factory=list)
    image: str = "kathara/nika-wireguard"
    cpus: float = 0.5
    mem: str = "256m"
    links: list[tuple[int, str]] = field(default_factory=list)
    extra_files: dict[str, str] = field(default_factory=dict)


def _read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _copy_dir_to_extra_files(dir_path: str, prefix: str = "/") -> dict[str, str]:
    result = {}
    if not os.path.isdir(dir_path):
        return result
    for root, _dirs, files in os.walk(dir_path):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, dir_path)
            result[prefix + rel] = _read_file(full)
    return result


def _load_wireguard_keys(keys_path: str) -> list[tuple[str, str]]:
    """Load key pairs from file. One line per key pair: private_key,public_key."""
    if not os.path.isfile(keys_path):
        raise FileNotFoundError(
            f"WireGuard keys file not found: {keys_path}. "
            "Create _utils/wireguard/keys.txt with one line per key pair: private_key,public_key"
        )
    pairs = []
    with open(keys_path, encoding="utf-8") as f:
        for line_f in f:
            line = line_f.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",", 1)]
            if len(parts) != 2:
                continue
            pairs.append((parts[0], parts[1]))
    return pairs


def _wg_conf_server(
    server_private: str,
    peers: list[tuple[str, str, str]],
) -> str:
    """Build wg0.conf for VPN server. peers: [(comment, public_key, allowed_ips), ...]."""
    lines = [
        "[Interface]",
        f"Address = {WG_SERVER_IP}/24",
        f"ListenPort = {WG_SERVER_PORT}",
        f"PrivateKey = {server_private}",
        "",
    ]
    for comment, pub, allowed in peers:
        lines.append(f"# {comment}")
        lines.append("[Peer]")
        lines.append(f"PublicKey = {pub}")
        lines.append(f"AllowedIPs = {allowed}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _wg_conf_client(
    client_private: str,
    server_public: str,
    client_address: str,
) -> str:
    """Build wg0.conf for VPN client (host or web_server)."""
    return "\n".join(
        [
            "[Interface]",
            f"Address = {client_address}/24",
            f"PrivateKey = {client_private}",
            "",
            "[Peer]",
            f"PublicKey = {server_public}",
            f"Endpoint = {WG_SERVER_ENDPOINT_IP}:{WG_SERVER_PORT}",
            f"AllowedIPs = {WG_VPN_NET}",
        ]
    )


def generate_rip_vpn_topology(
    topo_size: Literal["s", "m", "l"] = "s",
) -> str:
    """
    Generate Kathara-compatible lab configuration for RIP Small Internet VPN.
    WireGuard keys are read from wireguard_keys_path (default: _utils/wireguard/keys.txt),
    format: one line per key pair: private_key,public_key. Needs at least 4 key pairs
    (vpn_server_1, host_1, web_server_1_1, web_server_1_2).
    Returns the absolute path to the output directory.
    """
    output_dir = os.path.join(SCRIPT_DIR, f"size_{topo_size}", "topology")
    rip_utils = RIP_UTILS
    key_pairs = _load_wireguard_keys(WIREGUARD_KEYS_PATH)
    if len(key_pairs) < 4:
        raise ValueError(
            f"WireGuard keys file must contain at least 4 key pairs (got {len(key_pairs)}). "
            "Required: vpn_server_1, host_1, web_server_1_1, web_server_1_2."
        )

    match topo_size:
        case "s":
            internal_router_num, host_num, ext_router_num, ext_server_num = 2, 2, 1, 2
        case "m":
            internal_router_num, host_num, ext_router_num, ext_server_num = 4, 4, 2, 4
        case "l":
            internal_router_num, host_num, ext_router_num, ext_server_num = 8, 8, 4, 8
        case _:
            raise ValueError("topo_size should be one of 's', 'm', 'l'.")

    infra_pool = list(IPv4Network("192.168.0.0/16").subnets(new_prefix=31))

    internal_router_list: list[RouterMeta] = []
    for i in range(1, internal_router_num + 1):
        internal_router_list.append(RouterMeta(name=f"router{i}"))

    tot_host_list: list[HostMeta] = []
    for host_idx in range(1, host_num + 1):
        tot_host_list.append(HostMeta(name=f"host_{host_idx}"))

    gateway_router_meta = RouterMeta(name="gateway_router")

    external_routers: list[RouterMeta] = []
    for i in range(1, ext_router_num + 1):
        external_routers.append(RouterMeta(name=f"external_router_{i}"))

    external_server_dict: dict[str, list[HostMeta]] = defaultdict(list)
    for i in range(1, ext_router_num + 1):
        for server_idx in range(1, ext_server_num + 1):
            external_server_dict[f"external_router_{i}"].append(HostMeta(name=f"web_server_{i}_{server_idx}"))

    vpn_server_meta = HostMeta(name="vpn_server_1")

    # Connect internal routers full mesh
    for i in range(internal_router_num):
        for j in range(i + 1, internal_router_num):
            r_a = internal_router_list[i]
            r_b = internal_router_list[j]
            link_name = f"{r_a.name}_{r_b.name}"
            r_a.links.append((r_a.eth_index, link_name))
            r_b.links.append((r_b.eth_index, link_name))
            subnet = infra_pool.pop(0)
            a_ip, b_ip = assign_p2p_ips(subnet)
            r_a.cmd_list.append(f"ip addr add {a_ip} dev eth{r_a.eth_index}")
            r_a.eth_index += 1
            r_b.cmd_list.append(f"ip addr add {b_ip} dev eth{r_b.eth_index}")
            r_b.eth_index += 1

    # Connect first two internal routers to gateway
    for i in range(min(2, internal_router_num)):
        r_internal = internal_router_list[i]
        link_name = f"{r_internal.name}_{gateway_router_meta.name}"
        r_internal.links.append((r_internal.eth_index, link_name))
        gateway_router_meta.links.append((gateway_router_meta.eth_index, link_name))
        subnet = infra_pool.pop(0)
        a_ip, b_ip = assign_p2p_ips(subnet)
        r_internal.cmd_list.append(f"ip addr add {a_ip} dev eth{r_internal.eth_index}")
        r_internal.eth_index += 1
        gateway_router_meta.cmd_list.append(f"ip addr add {b_ip} dev eth{gateway_router_meta.eth_index}")
        gateway_router_meta.eth_index += 1

    # Connect internal hosts to internal routers
    for i in range(host_num):
        router_meta = internal_router_list[i]
        host_meta = tot_host_list[i]
        link_name = f"{router_meta.name}_{host_meta.name}"
        router_meta.links.append((router_meta.eth_index, link_name))
        host_meta.links.append((0, link_name))
        subnet = IPv4Network(f"10.0.{i}.0/24")
        router_ip = str(IPv4Interface(f"{subnet.network_address + 1}/24"))
        pc_ip = str(IPv4Interface(f"{subnet.network_address + 2}/24"))
        router_meta.cmd_list.append(f"ip addr add {router_ip} dev eth{router_meta.eth_index}")
        router_meta.eth_index += 1
        router_meta.host_network = subnet
        host_meta.cmd_list.append(f"ip addr add {pc_ip} dev eth{host_meta.eth_index}")
        host_meta.eth_index += 1
        host_meta.cmd_list.append(f"ip route add default via {router_ip.split('/')[0]}")

    # Connect external routers to gateway
    for ext_router in external_routers:
        link_name = f"{ext_router.name}_{gateway_router_meta.name}"
        ext_router.links.append((ext_router.eth_index, link_name))
        gateway_router_meta.links.append((gateway_router_meta.eth_index, link_name))
        subnet = infra_pool.pop(0)
        a_ip, b_ip = assign_p2p_ips(subnet)
        ext_router.cmd_list.append(f"ip addr add {a_ip} dev eth{ext_router.eth_index}")
        ext_router.eth_index += 1
        gateway_router_meta.cmd_list.append(f"ip addr add {b_ip} dev eth{gateway_router_meta.eth_index}")
        gateway_router_meta.eth_index += 1

    # Connect web servers and VPN server to external routers (bridged)
    for ext_idx, ext_router in enumerate(external_routers):
        ext_router.cmd_list.append("brctl addbr br0")
        ext_router.cmd_list.append("ip link set dev br0 up")
        zone_network = IPv4Network(f"20.0.{ext_idx}.0/24")
        ext_router.host_network = zone_network
        zone_ip_base = list(zone_network.hosts())
        ext_router_ip = str(IPv4Interface(f"{zone_ip_base[0]}/24"))
        ext_router.cmd_list.append(f"ip addr add {ext_router_ip} dev br0")
        ip_idx = 1

        if ext_idx == 0:
            link_name = f"{ext_router.name}_{vpn_server_meta.name}"
            ext_router.links.append((ext_router.eth_index, link_name))
            vpn_server_meta.links.append((0, link_name))
            ext_router.cmd_list.append(f"brctl addif br0 eth{ext_router.eth_index}")
            ext_router.eth_index += 1
            vpn_server_ip = str(IPv4Interface(f"{zone_ip_base[ip_idx]}/24"))
            ip_idx += 1
            vpn_server_meta.cmd_list.append(f"ip addr add {vpn_server_ip} dev eth{vpn_server_meta.eth_index}")
            vpn_server_meta.cmd_list.append(f"ip route add default via {ext_router_ip.split('/')[0]}")
            vpn_server_meta.eth_index += 1

        for server_meta in external_server_dict[ext_router.name]:
            link_name = f"{ext_router.name}_{server_meta.name}"
            ext_router.links.append((ext_router.eth_index, link_name))
            server_meta.links.append((0, link_name))
            ext_router.cmd_list.append(f"brctl addif br0 eth{ext_router.eth_index}")
            ext_router.eth_index += 1
            server_ip = str(IPv4Interface(f"{zone_ip_base[ip_idx]}/24"))
            ip_idx += 1
            server_meta.cmd_list.append(f"ip addr add {server_ip} dev eth{server_meta.eth_index}")
            server_meta.cmd_list.append(f"ip route add default via {ext_router_ip.split('/')[0]}")
            server_meta.eth_index += 1

    # Router FRR config and startup
    daemons_content = _read_file(os.path.join(rip_utils, "daemons"))
    vtysh_content = _read_file(os.path.join(rip_utils, "vtysh.conf"))
    all_routers = internal_router_list + [gateway_router_meta] + external_routers
    for router_meta in all_routers:
        router_meta.extra_files["/etc/frr/daemons"] = daemons_content
        router_meta.extra_files["/etc/frr/vtysh.conf"] = vtysh_content
        network_str = str(router_meta.host_network) if router_meta.host_network else ""
        router_meta.extra_files["/etc/frr/frr.conf"] = FRR_BASE_TEMPLATE_RIP.format(network=network_str)
        router_meta.cmd_list.append("service frr start")

    # WireGuard: key index 0=vpn_server_1, 1=host_1, 2=web_server_1_1, 3=web_server_1_2
    server_priv, server_pub = key_pairs[0][0], key_pairs[0][1]
    wg_server_peers = [
        ("host_1", key_pairs[1][1], "172.16.1.11/32"),
        ("web_server_1_1", key_pairs[2][1], "172.16.1.21/32"),
        ("web_server_1_2", key_pairs[3][1], "172.16.1.22/32"),
    ]
    vpn_server_meta.extra_files["/etc/wireguard/wg0.conf"] = _wg_conf_server(server_priv, wg_server_peers)
    vpn_server_meta.cmd_list.append("wg-quick up wg0")

    # Host configs
    for host in tot_host_list:
        if host.name == "host_1":
            host.extra_files["/etc/wireguard/wg0.conf"] = _wg_conf_client(key_pairs[1][0], server_pub, "172.16.1.11")
            host.cmd_list.append("wg-quick up wg0")

    for ext_router in external_routers:
        for server_meta in external_server_dict[ext_router.name]:
            if server_meta.name == "web_server_1_1":
                server_meta.extra_files.update(
                    _copy_dir_to_extra_files(os.path.join(SCRIPT_DIR, "confs", server_meta.name))
                )
                server_meta.extra_files["/etc/wireguard/wg0.conf"] = _wg_conf_client(
                    key_pairs[2][0], server_pub, "172.16.1.21"
                )
                server_meta.extra_files["/etc/apache2/ports.conf"] = _apache_ports_listen_vpn_only("172.16.1.21")
                server_meta.cmd_list.append("wg-quick up wg0")
                server_meta.cmd_list.append("ping -c 3 172.16.1.1")
            elif server_meta.name == "web_server_1_2":
                server_meta.extra_files.update(
                    _copy_dir_to_extra_files(os.path.join(SCRIPT_DIR, "confs", server_meta.name))
                )
                server_meta.extra_files["/etc/wireguard/wg0.conf"] = _wg_conf_client(
                    key_pairs[3][0], server_pub, "172.16.1.22"
                )
                server_meta.extra_files["/etc/apache2/ports.conf"] = _apache_ports_listen_vpn_only("172.16.1.22")
                server_meta.cmd_list.append("wg-quick up wg0")
                server_meta.cmd_list.append("ping -c 3 172.16.1.1")
            server_meta.cmd_list.append("service apache2 start")

    all_machines: list[RouterMeta | HostMeta] = (
        internal_router_list + [gateway_router_meta] + external_routers + tot_host_list + [vpn_server_meta]
    )
    for _ext_router in external_routers:
        all_machines.extend(external_server_dict[_ext_router.name])

    out_path = os.path.abspath(output_dir)
    os.makedirs(out_path, exist_ok=True)

    lab_conf_lines = [
        'LAB_NAME="rip_small_internet_vpn"',
        'LAB_DESCRIPTION="RIP Small Internet VPN - generated by lab_generator"',
        "",
    ]
    for meta in all_machines:
        for eth_idx, cd in meta.links:
            lab_conf_lines.append(f'{meta.name}[{eth_idx}]="{cd}"')
        lab_conf_lines.append(f'{meta.name}[image]="{meta.image}"')
        lab_conf_lines.append(f"{meta.name}[cpus]={meta.cpus}")
        lab_conf_lines.append(f'{meta.name}[mem]="{meta.mem}"')
        lab_conf_lines.append("")

    with open(os.path.join(out_path, "lab.conf"), "w", encoding="utf-8") as f:
        f.write("\n".join(lab_conf_lines))

    for meta in all_machines:
        with open(os.path.join(out_path, f"{meta.name}.startup"), "w", encoding="utf-8") as f:
            f.write("\n".join(meta.cmd_list))
        if meta.extra_files:
            host_dir = os.path.join(out_path, meta.name)
            for file_path, content in meta.extra_files.items():
                rel_path = file_path.lstrip("/")
                full_path = os.path.join(host_dir, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

    return out_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Kathara lab config for RIP Small Internet VPN")
    parser.add_argument("-s", "--size", choices=["s", "m", "l"], default="s", help="Topology size")

    args = parser.parse_args()
    out = generate_rip_vpn_topology(
        topo_size=args.size,
    )
    print(f"Lab configuration generated at: {out}")
