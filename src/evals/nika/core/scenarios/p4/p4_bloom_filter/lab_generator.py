#!/usr/bin/env python3
"""
Standalone lab generator for P4 Bloom Filter topology.
Generates Kathara-compatible lab configuration WITHOUT Kathara dependency.
Output: topology/ folder containing lab.conf, *.startup, and switch config files.
No topology size input - fixed topology (2 hosts, 2 switches).
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


def generate_p4_bloom_filter_topology(output_dir: str | None = None) -> str:
    """
    Generate Kathara-compatible lab configuration for P4 Bloom Filter.
    Returns the absolute path to the output directory.
    """
    if output_dir is None:
        output_dir = os.path.join(SCRIPT_DIR, "topology")

    host_1 = MachineMeta(name="host_1", image="kathara/base")
    host_2 = MachineMeta(name="host_2", image="kathara/base")
    switch_1 = MachineMeta(name="switch_1", image="kathara/p4")
    switch_2 = MachineMeta(name="switch_2", image="kathara/p4")

    # Topology: host_1 - switch_1 - switch_2 - host_2
    host_1.links.append((0, "A"))
    switch_1.links.append((0, "A"))
    host_2.links.append((0, "B"))
    switch_2.links.append((0, "B"))
    switch_1.links.append((1, "C"))
    switch_2.links.append((1, "C"))

    # Host startup
    for i in range(1, 3):
        cmd_list = [
            "sysctl net.ipv4.conf.all.arp_ignore=8",
            "sysctl net.ipv4.conf.default.arp_ignore=8",
            "sysctl net.ipv4.conf.all.arp_announce=8",
            "sysctl net.ipv4.conf.default.arp_announce=8",
            f"ip link set eth0 address 00:00:0a:00:00:0{i}",
            f"ip addr add 10.0.0.{i}/24 dev eth0",
        ]
        for j in range(1, 3):
            if j != i:
                cmd_list.append(f"arp -s 10.0.0.{j} 00:00:0a:00:00:0{j}")
        if i == 1:
            host_1.cmd_list = cmd_list
        else:
            host_2.cmd_list = cmd_list

    # Switch startup and files
    switch_startup_base = [
        "sysctl net.ipv4.conf.all.arp_ignore=8",
        "sysctl net.ipv4.conf.default.arp_ignore=8",
        "sysctl net.ipv4.conf.all.arp_announce=8",
        "sysctl net.ipv4.conf.default.arp_announce=8",
        "p4c bloom_filter.p4",
        "simple_switch -i 1@eth0 -i 2@eth1 --log-console bloom_filter.json >> sw.log &",
        "while [[ $(pgrep simple_switch) -eq 0 ]]; do sleep 1; done",
        'max_tries=5; count=0; until simple_switch_CLI <<< "help"; do sleep 1; count=$((count+1)); if [ "$count" -ge "$max_tries" ]; then echo "simple_switch_CLI not ready" >&2; exit 1; fi; done',
        "simple_switch_CLI <<< $(cat commands.txt)",
    ]
    switch_1.cmd_list = switch_startup_base.copy()
    switch_2.cmd_list = switch_startup_base.copy()

    switch_1.extra_files["bloom_filter.p4"] = _read_file(
        os.path.join(SCRIPT_DIR, "p4_src/bloom_filter.p4")
    )
    switch_1.extra_files["commands.txt"] = _read_file(os.path.join(SCRIPT_DIR, "cmds/switch_1.txt"))
    switch_2.extra_files["bloom_filter.p4"] = _read_file(
        os.path.join(SCRIPT_DIR, "p4_src/bloom_filter.p4")
    )
    switch_2.extra_files["commands.txt"] = _read_file(os.path.join(SCRIPT_DIR, "cmds/switch_2.txt"))

    if os.path.exists(os.path.join(P4_UTILS, "sswitch_thrift_API.py")):
        switch_1.extra_files["usr/local/lib/python3.11/site-packages/sswitch_thrift_API.py"] = (
            _read_file(os.path.join(P4_UTILS, "sswitch_thrift_API.py"))
        )
        switch_2.extra_files["usr/local/lib/python3.11/site-packages/sswitch_thrift_API.py"] = (
            _read_file(os.path.join(P4_UTILS, "sswitch_thrift_API.py"))
        )
    if os.path.exists(os.path.join(P4_UTILS, "thrift_API.py")):
        switch_1.extra_files["usr/local/lib/python3.11/site-packages/thrift_API.py"] = _read_file(
            os.path.join(P4_UTILS, "thrift_API.py")
        )
        switch_2.extra_files["usr/local/lib/python3.11/site-packages/thrift_API.py"] = _read_file(
            os.path.join(P4_UTILS, "thrift_API.py")
        )

    all_machines = [host_1, host_2, switch_1, switch_2]
    return _write_lab(
        output_dir, all_machines, "p4_bloom_filter", "P4 Bloom Filter - 2 hosts, 2 switches"
    )


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

    parser = argparse.ArgumentParser(description="Generate Kathara lab config for P4 Bloom Filter")
    parser.add_argument(
        "-o", "--output", default=None, help="Output directory (default: topology/)"
    )
    args = parser.parse_args()
    out = generate_p4_bloom_filter_topology(
        output_dir=args.output or os.path.join(SCRIPT_DIR, "topology")
    )
    print(f"Lab configuration generated at: {out}")
