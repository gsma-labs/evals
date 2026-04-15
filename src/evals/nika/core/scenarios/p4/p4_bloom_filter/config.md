# P4 Bloom Filter Topology

## Overview

Minimal topology for **P4 Bloom filter** or similar in-switch data structures: two hosts and two P4 switches sharing a common segment (C). Used for testing Bloom filter or set-membership logic in the data plane.

```
   host_1 (A) ---- switch_1 ----+---- switch_2 ---- host_2 (B)
                                 C
```

Networks: A (host_1–switch_1), B (host_2–switch_2), C (switch_1–switch_2).

## Configuration

### Devices

| Device | Image | Role |
|--------|-------|------|
| host_1, host_2 | kathara/base | Hosts |
| switch_1, switch_2 | kathara/p4 | P4/BMv2 switches |

**Total:** 4 machines (2 hosts, 2 switches).

### Protocols / Data Plane

- **P4:** Switches run a Bloom filter (or related) P4 program; packet processing and filter state are defined by the P4 pipeline and BMv2.

### Links

- host_1 ↔ A ↔ switch_1; host_2 ↔ B ↔ switch_2; switch_1 ↔ C ↔ switch_2.

## Directory Structure

```
p4_bloom_filter/
├── config.md
├── lab_generator.py
├── compose.yaml
└── topology/
    ├── lab.conf
    ├── host_1.startup, host_2.startup
    └── switch_1.startup, switch_2.startup
```

## Testing Commands

### From host
```bash
ping -c 4 <other_host>
```

### Bloom filter / P4
- Behavior depends on the P4 program (e.g. membership test, drop/forward based on filter); use BMv2 CLI or inspect tools if available.
