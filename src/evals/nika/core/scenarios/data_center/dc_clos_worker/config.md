# Data Center CLOS Worker (BGP-Only) Topology

## Overview

A 3-tier CLOS fabric with EBGP routing only: super-spine → spine → leaf → host PCs. No DNS, web servers, or external clients. Used for link-failure and misconfiguration tasks where only routing and connectivity matter. Referenced in dataset as **dc_clos_worker** (BGP-only topology).

```
                    ┌─────────────────┐
                    │ super_spine_0   │  (AS 65000)
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────┴────┐    ┌─────┴─────┐  ┌────┴────┐
         │spine    │    │spine      │  │spine    │  (AS 651xx)
         │ 0_0     │    │ 0_1       │  │ ...     │
         └────┬────┘    └─────┬─────┘  └────┬────┘
              │               │             │
         ┌────┴────┐    ┌─────┴─────┐  ┌────┴────┐
         │leaf     │    │leaf       │  │leaf     │  (AS 652xx)
         │ 0_0     │    │ 0_1       │  │ ...     │
         └────┬────┘    └─────┬─────┘  └────┬────┘
              │               │             │
           pc_0_0          pc_0_1         pc_X_Y   (static)
```

## Configuration

### Network Layers

| Layer | Count (size_s / size_m / size_l) | Routing Protocol |
|-------|----------------------------------|------------------|
| Super-spine | 1 / 2 / 4 | EBGP (AS 65000) |
| Spine | 2 / 8 / 32 | EBGP (AS 65100–65113 etc.) |
| Leaf | 2 / 8 / 32 | EBGP (AS 65200–65243 etc.) |
| Hosts (pc_X_Y) | 2 / 8 / 32 | Static default via leaf |

**Total machines:** size_s ≈ 8, size_m ≈ 26, size_l ≈ 74 (router + host counts from lab_generator).

### IP Addressing Scheme

- **P2P infrastructure (172.16.0.0/16):** /31 subnets for all router–router links.
- **Host networks (10.X.Y.0/24):** Leaf is gateway `10.X.Y.1`, host `pc_X_Y` is `10.X.Y.2`.

### BGP

- Each router runs FRR with a distinct AS; EBGP between super-spine, spine, and leaf.
- No BGP policies beyond basic neighbor and network advertisement; used for pure connectivity and routing tests.

## Directory Structure

```
dc_clos_worker/
├── config.md
├── lab_generator.py
├── size_s/
│   ├── compose.yaml
│   └── topology/
│       ├── lab.conf
│       ├── super_spine_router_*.startup
│       ├── spine_router_*_*.startup
│       ├── leaf_router_*_*.startup
│       ├── pc_*_*.startup
│       └── .../etc/frr/ (daemons, frr.conf, vtysh.conf)
├── size_m/
│   └── ...
└── size_l/
    └── ...
```

## Testing Commands

### BGP and routing

```bash
# From any router
vtysh -c "show ip bgp summary"
vtysh -c "show ip bgp neighbors"
vtysh -c "show ip route"
```

### Connectivity

```bash
# From a host
ping -c 4 10.X.Y.1   # gateway
ping -c 4 10.0.0.2   # another host (if in same or routed net)
```

## Task Families

This topology is used as **dc_clos_worker** in dataset for:

- **link_failure:** link_down, link_flap, link_detach, link_fragmentation_disabled, baseline.
- **misconfiguration:** host_static_blackhole, bgp_asn_misconfig, bgp_missing_route_advertisement, bgp_blackhole_route_leak, bgp_hijacking, baseline.
