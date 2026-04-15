# P4 Counter Topology

## Overview

A simple topology with **P4-capable switches** (BMv2, kathara/p4) and three hosts. Used for P4 pipeline and counter behavior (e.g. packet counting, stats). No size variants; single fixed topology.

```
   pc1 (A) ---- s1 ----+---- s2 ---- s4 ---- pc2 (F)
                |      |     |       |
                |      B     D       |
                +---- s3 ----+       |
                     |              |
                     C              E
                     |              |
                     +------ s4 ----+---- pc3 (G)
```

Networks (collision domains): A, B, C, D, E, F, G. s1 connects A,B,C; s2 B,D; s3 C,E; s4 D,E,F,G.

## Configuration

### Devices

| Device | Image | Role |
|--------|-------|------|
| pc1, pc2, pc3 | kathara/base | Hosts |
| s1, s2, s3, s4 | kathara/p4 | P4/BMv2 switches |

**Total:** 7 machines (3 hosts, 4 switches).

### Protocols / Data Plane

- **P4:** Switches run a P4 program (e.g. counter or simple forwarding); pipeline and counters are defined by the P4 code and BMv2.
- No control-plane routing; forwarding and counters are defined in the P4 pipeline.

### Links (lab.conf)

- pc1 ↔ A; pc2 ↔ F; pc3 ↔ G.
- s1 ↔ A, B, C; s2 ↔ B, D; s3 ↔ C, E; s4 ↔ D, E, F, G.

## Directory Structure

```
p4_counter/
├── config.md
├── lab_generator.py
├── compose.yaml
└── topology/
    ├── lab.conf
    ├── pc1.startup, pc2.startup, pc3.startup
    └── s1.startup .. s4.startup (and P4 pipeline / BMv2 config as used)
```

## Testing Commands

### From host
```bash
ping -c 4 <other_host>
```

### P4 / BMv2 (if CLI or runtime API exposed)
- Counter readouts, table entries, etc., depend on the P4 program and runtime (e.g. simple_switch_CLI or inspect tools).
