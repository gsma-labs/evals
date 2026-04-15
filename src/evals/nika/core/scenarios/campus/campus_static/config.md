# Campus OSPF Enterprise Static Topology

## Overview

An enterprise hierarchical network using FRR OSPF with multiple areas. Three core routers form the backbone (area 0) with /31 infrastructure links from 172.16.0.0/16. Core1 and Core2 connect to distribution routers, which in turn bridge to access switches. User hosts are statically addressed in subnets `10.<core>.<dist>.0/24` with their default gateway on the distribution switch and DNS pointed to a central DNS server. A server farm in `10.200.0.0/24` hangs off a dedicated OSPF router (area 0) and hosts one Bind DNS server for the `local` zone plus several Apache web servers published as `web0.local`…`web3.local`, all reachable end-to-end via OSPF.

```
                    ┌──────────────┐
                    │router_core_1 │
                    │  (Area 0)    │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────┴────┐       ┌─────┴─────┐      ┌────┴────┐
   │router_  │       │router_    │      │router_  │
   │core_2   │       │core_3     │      │core_1   │
   │(Area 0) │       │(Area 0)   │      │(Area 0) │
   └────┬────┘       └─────┬─────┘      └────┬────┘
        │                  │                  │
   ┌────┴────┐             │             ┌────┴────┐
   │switch_  │             │             │switch_  │
   │dist_1_1 │             │             │dist_1_2 │
   │(Area 1) │             │             │(Area 1) │
   └────┬────┘             │             └────┬────┘
        │                  │                  │
   ┌────┴────┐             │             ┌────┴────┐
   │switch_  │             │             │switch_  │
   │access_  │             │             │access_  │
   │1_1_1    │             │             │1_2_1    │
   └────┬────┘             │             └────┬────┘
        │                  │                  │
   ┌────┴────┐             │             ┌────┴────┐
   │host_    │             │             │host_    │
   │1_1_1_1  │             │             │1_2_1_1  │
   │10.1.1.2 │             │             │10.1.2.2 │
   └─────────┘             │             └─────────┘
                           │
                    ┌──────┴───────┐
                    │switch_server │
                    │  _access     │
                    │  (Area 0)    │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────┴────┐       ┌─────┴─────┐      ┌────┴────┐
   │dns_     │       │web_       │      │web_     │
   │server   │       │server_0   │      │server_1 │
   │10.200.0.│       │10.200.0.3 │      │10.200.0.│
   │2        │       │           │      │4        │
   └─────────┘       └───────────┘      └─────────┘
```

## Configuration

### Network Layers

| Layer | Count | Routing Protocol | Area |
|-------|-------|------------------|------|
| Core Routers | 3 | OSPF | Area 0 |
| Distribution Routers | 4 (2 per core 1-2) | OSPF | Area 1 |
| Access Switches | 8 (2 per dist) | Bridge (L2) | - |
| Hosts | 16 (2 per access) | Static | - |
| Server Access Switch | 1 | OSPF | Area 0 |
| DNS Server | 1 | Static | - |
| Web Servers | 4 | Static | - |

**Total: 37 machines (medium size topology)**

### IP Addressing Scheme

#### P2P Infrastructure Links (172.16.0.0/16)
- /31 subnets for router-to-router connections
- Core-to-core links in Area 0
- Core-to-distribution links in Area 1
- Core3-to-server-access link in Area 0

#### Host Networks (10.<core>.<dist>.0/24)
- Distribution router gateway: `10.<core>.<dist>.1/24`
- Host IPs: `10.<core>.<dist>.2` onwards
- Example: `10.1.1.0/24` for core1, dist1

#### Server Farm Network (10.200.0.0/24)
- Server access switch gateway: `10.200.0.1/24`
- DNS server: `10.200.0.2/24`
- Web servers: `10.200.0.3` - `10.200.0.6`

### OSPF Areas

- **Area 0 (Backbone)**: Core routers (1-2-3 mesh) and server access switch
- **Area 1**: Distribution routers connected to core1 and core2

### DNS Configuration

- **Zone**: `local`
- **DNS Server**: `dns_server` at `10.200.0.2`
- **Records**:
  - `ns1.local` -> `10.200.0.2`
  - `web0.local` -> `10.200.0.3`
  - `web1.local` -> `10.200.0.4`
  - `web2.local` -> `10.200.0.5`
  - `web3.local` -> `10.200.0.6`

### Web Servers

All web servers run Apache HTTP server on port 80, serving unique content identifying each server.

## Directory Structure

```
campus_static/
├── config.md
├── lab_generator.py
├── size_s/
│   ├── compose.yaml
│   └── topology/
│       ├── lab.conf
│       ├── router_core_X.startup, switch_dist_X_Y.startup, ...
│       ├── switch_server_access/, dns_server/, web_server_X/
│       └── .../etc/frr/, etc/bind/, var/www/html/
├── size_m/
│   └── ...
└── size_l/
    └── ...
```

## Testing Commands

### OSPF Verification
```bash
# From any router
vtysh -c "show ip ospf neighbor"
vtysh -c "show ip ospf route"
vtysh -c "show ip route"
```

### DNS Testing
```bash
# From any host
dig @10.200.0.2 web0.local
nslookup web1.local 10.200.0.2
```

### HTTP Testing
```bash
# Direct by IP
curl http://10.200.0.3/
# Via DNS (if resolv.conf configured)
curl http://web0.local/
```

### Connectivity Testing
```bash
# From host to server
ping -c 4 10.200.0.2
traceroute 10.200.0.3
```
