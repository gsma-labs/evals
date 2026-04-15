# P4 MPLS Topology

## Overview

A multi-switch topology with **P4 MPLS** (label switching in the data plane): three hosts and seven P4 switches in a graph. Used for MPLS label push/swap/pop and path forwarding tests.

```
   host_1 ---- switch_1 ----+---- switch_2 ----+
                |    \                         |
                |     \                        |
                +---- switch_3 ----+---- switch_4 ----+---- switch_5 ---- switch_7 ---- host_2
                                   |                  |                      |
                                   |                  +---- switch_6 ----+---+
                                   |                                       |
                                   +---------------------------------------+
                                                                          host_3
```

Links (from lab.conf): host_1–switch_1; switch_1–switch_2, switch_1–switch_3; switch_2–switch_4; switch_3–switch_4; switch_4–switch_5, switch_4–switch_6; switch_5–switch_7; switch_6–switch_7; switch_7–host_2, switch_7–host_3.

## Configuration

### Devices

| Device | Image | Role |
|--------|-------|------|
| host_1, host_2, host_3 | kathara/base | Hosts |
| switch_1 .. switch_7 | kathara/p4 | P4/BMv2 MPLS switches |

**Total:** 10 machines (3 hosts, 7 switches).

### Protocols / Data Plane

- **P4 MPLS:** Switches run an MPLS P4 program (push/swap/pop labels); forwarding is label-based along the path.

### Links

- host_1 ↔ host_1_to_switch_1 ↔ switch_1.
- switch_1 ↔ switch_1_to_switch_2 ↔ switch_2; switch_1 ↔ switch_1_to_switch_3 ↔ switch_3.
- switch_2 ↔ switch_2_to_switch_4 ↔ switch_4; switch_3 ↔ switch_3_to_switch_4 ↔ switch_4.
- switch_4 ↔ switch_4_to_switch_5 ↔ switch_5; switch_4 ↔ switch_4_to_switch_6 ↔ switch_6.
- switch_5 ↔ switch_5_to_switch_7 ↔ switch_7; switch_6 ↔ switch_6_to_switch_7 ↔ switch_7.
- switch_7 ↔ switch_7_to_host_2 ↔ host_2; switch_7 ↔ switch_7_to_host_3 ↔ host_3.

## Directory Structure

```
p4_mpls/
├── config.md
├── lab_generator.py
├── compose.yaml
└── topology/
    ├── lab.conf
    ├── host_1.startup, host_2.startup, host_3.startup
    └── switch_1.startup .. switch_7.startup
```

## Testing Commands

### From host
```bash
ping -c 4 <other_host>
traceroute <target>
```

### MPLS (if CLI/API exposed)
- Inspect MPLS table entries, labels; verify push/swap/pop along path.
