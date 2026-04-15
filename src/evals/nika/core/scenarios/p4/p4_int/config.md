# P4 INT (In-band Network Telemetry) Topology

## Overview

A small spine–leaf style path with **P4 INT** (In-band Network Telemetry): two hosts (pc1, pc2), two spine and two leaf P4 switches, and a **collector** (InfluxDB, kathara/nika-influxdb) that receives INT reports. Packets can be mirrored or reported along the path for telemetry.

```
   pc1 (A) ---- leaf1 ----+---- spine1 ----+
                |    \     B        E      |
                |     \                     |
                C      +---- spine2 ----+---- leaf2 ---- D ---- pc2
                |           F                |    |
                |                            G    collector
                +----------------------------+
```

Networks: A (pc1–leaf1), B (leaf1–spine1), C (leaf1–spine2), D (leaf2–pc2), E (spine1–leaf2), F (spine2–leaf2), G (leaf2–collector).

## Configuration

### Devices

| Device | Image | Role |
|--------|-------|------|
| pc1, pc2 | kathara/base | Hosts |
| leaf1, leaf2 | kathara/p4 | P4 leaf switches |
| spine1, spine2 | kathara/p4 | P4 spine switches |
| collector | kathara/nika-influxdb | INT report collector |

**Total:** 7 machines (2 hosts, 4 switches, 1 collector).

### Protocols / Data Plane

- **P4 INT:** Switches run an INT-capable P4 program; telemetry data is sent to the collector (e.g. over network G).
- **Collector:** InfluxDB for storing/querying telemetry.

### Links

- pc1 ↔ A ↔ leaf1; leaf1 ↔ B ↔ spine1, leaf1 ↔ C ↔ spine2.
- spine1 ↔ E ↔ leaf2; spine2 ↔ F ↔ leaf2; leaf2 ↔ D ↔ pc2; leaf2 ↔ G ↔ collector.

## Directory Structure

```
p4_int/
├── config.md
├── lab_generator.py
├── compose.yaml
└── topology/
    ├── lab.conf
    ├── pc1.startup, pc2.startup
    ├── leaf1.startup, leaf2.startup, spine1.startup, spine2.startup
    └── collector.startup
```

## Testing Commands

### From host
```bash
ping -c 4 <other_host>
```

### INT / collector
- Send test traffic; verify telemetry reports in InfluxDB or via INT tools (depends on P4 INT app and collector config).
