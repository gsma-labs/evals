#!/usr/bin/env python3
"""
Standalone lab generator for P4 Counter topology.
Generates Kathara-compatible lab configuration WITHOUT Kathara dependency.
Output: topology/ folder containing lab.conf, *.startup, and switch config files.
No topology size input - fixed topology (3 hosts, 4 switches).
"""

import os
from dataclasses import dataclass, field

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
P4_UTILS = os.path.join(SCRIPT_DIR, "../../_utils/p4")


@dataclass
class MachineMeta:
    name: str
    eth_index: int = 0
    cmd_list: list[str] = field(default_factory=list)
    image: str = "kathara/p4"
    cpus: float = 0.5
    mem: str = "256m"
    links: list[tuple[int, str]] = field(default_factory=list)
    extra_files: dict[str, str] = field(default_factory=dict)


def _read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def generate_p4_counter_topology(output_dir: str | None = None) -> str:
    """
    Generate Kathara-compatible lab configuration for P4 Counter.
    Returns the absolute path to the output directory.
    """
    if output_dir is None:
        output_dir = os.path.join(SCRIPT_DIR, "topology")

    pc1 = MachineMeta(name="pc1", image="kathara/base")
    pc2 = MachineMeta(name="pc2", image="kathara/base")
    pc3 = MachineMeta(name="pc3", image="kathara/base")
    s1 = MachineMeta(name="s1", image="kathara/p4")
    s2 = MachineMeta(name="s2", image="kathara/p4")
    s3 = MachineMeta(name="s3", image="kathara/p4")
    s4 = MachineMeta(name="s4", image="kathara/p4")

    # Topology from lab.py
    pc1.links.append((0, "A"))
    s1.links.append((0, "A"))
    s1.links.append((1, "B"))
    s2.links.append((0, "B"))
    s1.links.append((2, "C"))
    s3.links.append((0, "C"))
    s2.links.append((1, "D"))
    s4.links.append((0, "D"))
    s3.links.append((1, "E"))
    s4.links.append((1, "E"))
    pc2.links.append((0, "F"))
    s4.links.append((2, "F"))
    pc3.links.append((0, "G"))
    s4.links.append((3, "G"))

    # Host startup
    for i, pc in enumerate([pc1, pc2, pc3], start=1):
        cmd_list = [
            "sysctl net.ipv4.conf.all.arp_ignore=8",
            "sysctl net.ipv4.conf.default.arp_ignore=8",
            "sysctl net.ipv4.conf.all.arp_announce=8",
            "sysctl net.ipv4.conf.default.arp_announce=8",
            f"ip link set eth0 address 00:00:0a:00:00:0{i}",
            f"ip addr add 10.0.0.{i}/24 dev eth0",
        ]
        for j in range(1, 4):
            if j != i:
                cmd_list.append(f"arp -s 10.0.0.{j} 00:00:0a:00:00:0{j}")
        pc.cmd_list = cmd_list

    # Switch startup: s1 has 3 intf, s2/s3 have 2, s4 has 4
    p4_file = "l2_basic_forwarding_counter.p4"
    s1.cmd_list = [
        "sysctl net.ipv4.conf.all.arp_ignore=8",
        "sysctl net.ipv4.conf.default.arp_ignore=8",
        "sysctl net.ipv4.conf.all.arp_announce=8",
        "sysctl net.ipv4.conf.default.arp_announce=8",
        f"p4c {p4_file}",
        "simple_switch -i 1@eth0 -i 2@eth1 -i 3@eth2 --log-console l2_basic_forwarding_counter.json >> sw.log &",
        "while [[ $(pgrep simple_switch) -eq 0 ]]; do sleep 1; done",
        'until simple_switch_CLI <<< "help"; do sleep 1; done',
        "simple_switch_CLI <<< $(cat commands.txt)",
    ]
    s2.cmd_list = s3.cmd_list = [
        "sysctl net.ipv4.conf.all.arp_ignore=8",
        "sysctl net.ipv4.conf.default.arp_ignore=8",
        "sysctl net.ipv4.conf.all.arp_announce=8",
        "sysctl net.ipv4.conf.default.arp_announce=8",
        f"p4c {p4_file}",
        "simple_switch -i 1@eth0 -i 2@eth1 --log-console l2_basic_forwarding_counter.json >> sw.log &",
        "while [[ $(pgrep simple_switch) -eq 0 ]]; do sleep 1; done",
        'until simple_switch_CLI <<< "help"; do sleep 1; done',
        "simple_switch_CLI <<< $(cat commands.txt)",
    ]
    s4.cmd_list = [
        "sysctl net.ipv4.conf.all.arp_ignore=8",
        "sysctl net.ipv4.conf.default.arp_ignore=8",
        "sysctl net.ipv4.conf.all.arp_announce=8",
        "sysctl net.ipv4.conf.default.arp_announce=8",
        f"p4c {p4_file}",
        "simple_switch -i 1@eth0 -i 2@eth1 -i 3@eth2 -i 4@eth3 --log-console l2_basic_forwarding_counter.json >> sw.log &",
        "while [[ $(pgrep simple_switch) -eq 0 ]]; do sleep 1; done",
        'until simple_switch_CLI <<< "help"; do sleep 1; done',
        "simple_switch_CLI <<< $(cat commands.txt)",
    ]

    for i, sw in enumerate([s1, s2, s3, s4], start=1):
        sw.extra_files[p4_file] = _read_file(os.path.join(SCRIPT_DIR, "p4_src", p4_file))
        sw.extra_files["commands.txt"] = _read_file(os.path.join(SCRIPT_DIR, f"cmds/s{i}.txt"))
        if os.path.exists(os.path.join(P4_UTILS, "sswitch_thrift_API.py")):
            sw.extra_files["usr/local/lib/python3.11/site-packages/sswitch_thrift_API.py"] = (
                _read_file(os.path.join(P4_UTILS, "sswitch_thrift_API.py"))
            )
        if os.path.exists(os.path.join(P4_UTILS, "thrift_API.py")):
            sw.extra_files["usr/local/lib/python3.11/site-packages/thrift_API.py"] = _read_file(
                os.path.join(P4_UTILS, "thrift_API.py")
            )

    all_machines = [pc1, pc2, pc3, s1, s2, s3, s4]
    return _write_lab(output_dir, all_machines, "p4_counter", "P4 Counter - 3 hosts, 4 switches")


def _write_lab(
    out_path: str,
    all_machines: list[MachineMeta],
    lab_name: str,
    lab_description: str,
) -> str:
    out_path = os.path.abspath(out_path)
    os.makedirs(out_path, exist_ok=True)

    lab_conf_lines = [
        f'LAB_NAME="{lab_name}"',
        f'LAB_DESCRIPTION="{lab_description}"',
        "",
    ]
    for meta in all_machines:
        for eth_idx, collision_domain in meta.links:
            lab_conf_lines.append(f'{meta.name}[{eth_idx}]="{collision_domain}"')
        lab_conf_lines.append(f'{meta.name}[image]="{meta.image}"')
        lab_conf_lines.append(f"{meta.name}[cpus]={meta.cpus}")
        lab_conf_lines.append(f'{meta.name}[mem]="{meta.mem}"')
        lab_conf_lines.append("")

    with open(os.path.join(out_path, "lab.conf"), "w", encoding="utf-8") as f:
        f.write("\n".join(lab_conf_lines))

    for meta in all_machines:
        startup_path = os.path.join(out_path, f"{meta.name}.startup")
        with open(startup_path, "w", encoding="utf-8") as f:
            f.write("\n".join(meta.cmd_list))
        if meta.extra_files:
            machine_dir = os.path.join(out_path, meta.name)
            for file_path, content in meta.extra_files.items():
                full_path = os.path.join(machine_dir, file_path.lstrip("/"))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

    return out_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Kathara lab config for P4 Counter")
    parser.add_argument(
        "-o", "--output", default=None, help="Output directory (default: topology/)"
    )
    args = parser.parse_args()
    out = generate_p4_counter_topology(
        output_dir=args.output or os.path.join(SCRIPT_DIR, "topology")
    )
    print(f"Lab configuration generated at: {out}")
