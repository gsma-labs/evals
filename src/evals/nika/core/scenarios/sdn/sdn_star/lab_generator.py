#!/usr/bin/env python3
"""
Standalone lab generator for SDN Star topology.
Generates Kathara-compatible lab configuration WITHOUT Kathara dependency.
Output: topology/ folder containing lab.conf and *.startup.
"""

import os
from dataclasses import dataclass, field
from ipaddress import IPv4Network
from typing import Literal

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


@dataclass
class SwitchMeta:
    name: str
    eth_index: int = 0
    cmd_list: list[str] = field(default_factory=list)
    image: str = "kathara/sdn"
    cpus: float = 0.5
    mem: str = "256m"
    links: list[tuple[int, str]] = field(default_factory=list)


@dataclass
class HostMeta:
    name: str
    eth_index: int = 0
    cmd_list: list[str] = field(default_factory=list)
    image: str = "kathara/nika-base"
    cpus: float = 0.5
    mem: str = "256m"
    links: list[tuple[int, str]] = field(default_factory=list)


@dataclass
class ControllerMeta:
    name: str
    cmd_list: list[str] = field(default_factory=list)
    image: str = "kathara/nika-ryu"
    cpus: float = 0.5
    mem: str = "256m"
    links: list[tuple[int, str]] = field(default_factory=list)
    bridged: bool = True


def generate_sdn_star_topology(
    topo_size: Literal["s", "m", "l"] = "s",
    output_dir: str | None = None,
) -> str:
    """
    Generate Kathara-compatible lab configuration for SDN Star topology.
    Returns the absolute path to the output directory.
    """
    if output_dir is None:
        output_dir = os.path.join(SCRIPT_DIR, "topology")

    if topo_size == "s":
        SWITCH_NUM = 4  # 1 center + 3 leaf
    elif topo_size == "m":
        SWITCH_NUM = 8
    elif topo_size == "l":
        SWITCH_NUM = 16
    else:
        raise ValueError("topo_size should be 's', 'm', or 'l'.")

    tot_switch_list: list[SwitchMeta] = []
    for i in range(SWITCH_NUM + 1):
        switch_name = f"switch_{i}"
        tot_switch_list.append(SwitchMeta(name=switch_name))

    tot_host_list: list[HostMeta] = []
    for host_id in range(SWITCH_NUM):
        host_name = f"host_{host_id + 1}"
        tot_host_list.append(HostMeta(name=host_name))

    controller = ControllerMeta(name="controller")

    for switch_meta in tot_switch_list:
        switch_meta.cmd_list.append(
            "/usr/share/openvswitch/scripts/ovs-ctl --system-id=random start"
        )
        switch_meta.cmd_list.append(f"ovs-vsctl add-br {switch_meta.name}")
        switch_meta.cmd_list.append(f"ovs-vsctl set-fail-mode {switch_meta.name} secure")

    host_pool = list(IPv4Network("10.0.0.0/24").hosts())
    for i in range(SWITCH_NUM):
        host_meta = tot_host_list[i]
        switch_meta = tot_switch_list[i + 1]
        link_name = f"{host_meta.name}_{switch_meta.name}"
        host_meta.links.append((0, link_name))
        switch_meta.links.append((switch_meta.eth_index, link_name))
        host_ip = str(host_pool[i])
        host_meta.cmd_list.append(f"ip addr add {host_ip}/24 dev eth0")
        switch_meta.cmd_list.append(
            f"ovs-vsctl add-port {switch_meta.name} eth{switch_meta.eth_index}"
        )
        switch_meta.eth_index += 1

    center = tot_switch_list[0]
    for leaf in tot_switch_list[1:]:
        link_name = f"{center.name}_{leaf.name}"
        center.links.append((center.eth_index, link_name))
        leaf.links.append((leaf.eth_index, link_name))
        center.cmd_list.append(f"ip link set eth{center.eth_index} up")
        center.cmd_list.append(f"ovs-vsctl add-port {center.name} eth{center.eth_index}")
        center.eth_index += 1
        leaf.cmd_list.append(f"ip link set eth{leaf.eth_index} up")
        leaf.cmd_list.append(f"ovs-vsctl add-port {leaf.name} eth{leaf.eth_index}")
        leaf.eth_index += 1

    controller_ip = "20.0.0.100"
    infra_network = list(IPv4Network("20.0.0.0/24").hosts())
    for switch_meta in tot_switch_list:
        switch_meta.links.append((switch_meta.eth_index, "switch_controller"))
        switch_ip = str(infra_network.pop(0))
        switch_meta.cmd_list.append(f"ip addr add {switch_ip}/24 dev eth{switch_meta.eth_index}")
        switch_meta.cmd_list.append(
            f"ovs-vsctl set-controller {switch_meta.name} tcp:{controller_ip}:6633"
        )
        switch_meta.eth_index += 1
    controller.links.append((0, "switch_controller"))
    controller.cmd_list = [
        "ip addr add 20.0.0.100/24 dev eth0",
        "ip link set eth0 up",
        "ryu-manager ryu.app.simple_switch &",
    ]

    out_path = os.path.abspath(output_dir)
    os.makedirs(out_path, exist_ok=True)

    lab_conf_lines = [
        'LAB_NAME="sdn_star"',
        'LAB_DESCRIPTION="SDN star topology"',
        "",
    ]
    for meta in tot_switch_list + tot_host_list:
        for eth_idx, cd in meta.links:
            lab_conf_lines.append(f'{meta.name}[{eth_idx}]="{cd}"')
        lab_conf_lines.append(f'{meta.name}[image]="{meta.image}"')
        lab_conf_lines.append(f"{meta.name}[cpus]={meta.cpus}")
        lab_conf_lines.append(f'{meta.name}[mem]="{meta.mem}"')
        lab_conf_lines.append("")
    for eth_idx, cd in controller.links:
        lab_conf_lines.append(f'{controller.name}[{eth_idx}]="{cd}"')
    lab_conf_lines.append(f'{controller.name}[image]="{controller.image}"')
    lab_conf_lines.append(f"{controller.name}[cpus]={controller.cpus}")
    lab_conf_lines.append(f'{controller.name}[mem]="{controller.mem}"')
    lab_conf_lines.append(f"{controller.name}[bridged]={'true' if controller.bridged else 'false'}")
    lab_conf_lines.append("")

    with open(os.path.join(out_path, "lab.conf"), "w", encoding="utf-8") as f:
        f.write("\n".join(lab_conf_lines))

    for meta in tot_switch_list + tot_host_list:
        with open(os.path.join(out_path, f"{meta.name}.startup"), "w", encoding="utf-8") as f:
            f.write("\n".join(meta.cmd_list))
    with open(os.path.join(out_path, f"{controller.name}.startup"), "w", encoding="utf-8") as f:
        f.write("\n".join(controller.cmd_list))

    return out_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Kathara lab config for SDN Star")
    parser.add_argument("-s", "--size", choices=["s", "m", "l"], default="s", help="Topology size")
    parser.add_argument("-o", "--output", default=None, help="Output directory")
    args = parser.parse_args()
    if args.output is None:
        args.output = os.path.join(SCRIPT_DIR, f"size_{args.size}", "topology")
    if not os.path.exists(args.output):
        os.makedirs(args.output, exist_ok=True)
    out = generate_sdn_star_topology(
        topo_size=args.size,
        output_dir=args.output,
    )
    print(f"Lab configuration generated at: {out}")
