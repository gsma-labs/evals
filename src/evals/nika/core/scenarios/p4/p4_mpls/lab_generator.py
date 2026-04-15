#!/usr/bin/env python3
"""
Standalone lab generator for P4 MPLS topology.
Generates Kathara-compatible lab configuration WITHOUT Kathara dependency.
Output: topology/ folder containing lab.conf, *.startup, and switch config files.
No topology size input - fixed topology (3 hosts, 7 switches).
"""

import os
from dataclasses import dataclass, field

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
P4_UTILS = os.path.join(SCRIPT_DIR, "p4_utils")
STARTUPS_DIR = os.path.join(SCRIPT_DIR, "startups")
CMDS_DIR = os.path.join(SCRIPT_DIR, "cmds")


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


def _add_link(machines: dict, device_a: str, device_b: str):
    link_name = f"{device_a}_to_{device_b}"
    if device_a.startswith("host_"):
        machines[device_a].links.append((0, link_name))
    else:
        machines[device_a].links.append((machines[device_a].eth_index, link_name))
        machines[device_a].eth_index += 1
    if device_b.startswith("host_"):
        machines[device_b].links.append((0, link_name))
    else:
        machines[device_b].links.append((machines[device_b].eth_index, link_name))
        machines[device_b].eth_index += 1


def generate_p4_mpls_topology() -> str:
    """
    Generate Kathara-compatible lab configuration for P4 MPLS.
    Returns the absolute path to the output directory.
    """

    machines = {}
    for i in range(1, 4):
        machines[f"host_{i}"] = MachineMeta(name=f"host_{i}", image="kathara/base")
    for i in range(1, 8):
        machines[f"switch_{i}"] = MachineMeta(
            name=f"switch_{i}", image="kathara/p4", cpus=0.5, mem="256m"
        )

    # Topology from lab.py
    _add_link(machines, "host_1", "switch_1")
    _add_link(machines, "switch_1", "switch_2")
    _add_link(machines, "switch_1", "switch_3")
    _add_link(machines, "switch_2", "switch_4")
    _add_link(machines, "switch_3", "switch_4")
    _add_link(machines, "switch_4", "switch_5")
    _add_link(machines, "switch_4", "switch_6")
    _add_link(machines, "switch_5", "switch_7")
    _add_link(machines, "switch_6", "switch_7")
    _add_link(machines, "switch_7", "host_2")
    _add_link(machines, "switch_7", "host_3")

    # Host startups from startups/ folder
    for i in range(1, 4):
        machines[f"host_{i}"].cmd_list = (
            _read_file(os.path.join(STARTUPS_DIR, f"host_{i}.startup")).strip().split("\n")
        )

    # Switch startups and files from startups/ folder
    for i in range(1, 8):
        sw = machines[f"switch_{i}"]
        sw.cmd_list = (
            _read_file(os.path.join(STARTUPS_DIR, f"switch_{i}.startup")).strip().split("\n")
        )
        sw.extra_files["mpls.p4"] = _read_file(os.path.join(SCRIPT_DIR, "p4_src", "mpls.p4"))
        sw.extra_files["commands.txt"] = _read_file(
            os.path.join(CMDS_DIR, f"switch_{i}", "commands.txt")
        )
        if os.path.exists(os.path.join(P4_UTILS, "sswitch_thrift_API.py")):
            sw.extra_files["usr/local/lib/python3.11/site-packages/sswitch_thrift_API.py"] = (
                _read_file(os.path.join(P4_UTILS, "sswitch_thrift_API.py"))
            )
        if os.path.exists(os.path.join(P4_UTILS, "thrift_API.py")):
            sw.extra_files["usr/local/lib/python3.11/site-packages/thrift_API.py"] = _read_file(
                os.path.join(P4_UTILS, "thrift_API.py")
            )

    all_machines = [machines[f"host_{i}"] for i in range(1, 4)] + [
        machines[f"switch_{i}"] for i in range(1, 8)
    ]
    return _write_lab(
        os.path.join(SCRIPT_DIR, "topology"),
        all_machines,
        "p4_mpls",
        "P4 MPLS - 3 hosts, 7 switches",
    )


def _write_lab(
    output_dir: str,
    all_machines: list[MachineMeta],
    lab_name: str,
    lab_description: str,
) -> str:
    out_path = os.path.abspath(output_dir)
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

    parser = argparse.ArgumentParser(description="Generate Kathara lab config for P4 MPLS")
    args = parser.parse_args()
    out = generate_p4_mpls_topology()
    print(f"Lab configuration generated at: {out}")
