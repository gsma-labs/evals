# Data Center CLOS Service Topology

## Overview

A 3-tier CLOS fabric using EBGP for routing, extended with DNS and HTTP services for service-layer troubleshooting tasks.

```
                    ┌─────────────────┐     ┌─────────────────┐
                    │ super_spine_0   │     │ super_spine_1   │
                    │   (AS 65000)    │     │   (AS 65000)    │
                    │   eth8:external │     │   eth8:external │
                    └────────┬────────┘     └────────┬────────┘
                             │                       │
                        ┌────┴────┐             ┌────┴────┐
                        │client_0 │             │client_1 │
                        │192.168. │             │192.168. │
                        │  0.2    │             │  1.2    │
                        └─────────┘             └─────────┘
                             │                       │
         ┌───────┬───────┬───┴───┬───────┬───────┬───┴───┬───────┐
         │       │       │       │       │       │       │       │
    ┌────┴───┐ ┌─┴──┐ ┌──┴─┐ ┌───┴──┐ ┌──┴───┐ ┌─┴──┐ ┌──┴─┐ ┌───┴──┐
    │spine   │ │    │ │    │ │      │ │      │ │    │ │    │ │spine │
    │ 0_0    │ │0_1 │ │0_2 │ │ 0_3  │ │ 1_0  │ │1_1 │ │1_2 │ │ 1_3  │
    └────┬───┘ └─┬──┘ └──┬─┘ └───┬──┘ └──┬───┘ └─┬──┘ └──┬─┘ └───┬──┘
         │       │       │       │       │       │       │       │
    ┌────┴───┐ ┌─┴──┐ ┌──┴─┐ ┌───┴──┐ ┌──┴───┐ ┌─┴──┐ ┌──┴─┐ ┌───┴──┐
    │leaf    │ │    │ │    │ │      │ │      │ │    │ │    │ │leaf  │
    │ 0_0    │ │0_1 │ │0_2 │ │ 0_3  │ │ 1_0  │ │1_1 │ │1_2 │ │ 1_3  │
    └────┬───┘ └─┬──┘ └──┬─┘ └───┬──┘ └──┬───┘ └─┬──┘ └──┬─┘ └───┬──┘
         │       │       │       │       │       │       │       │
     ┌───┴───┐   │       │       │   ┌───┴───┐   │       │       │
     │dns_0  │   │       │       │   │dns_1  │   │       │       │
     │10.0.0.│   │       │       │   │10.1.0.│   │       │       │
     │  100  │   │       │       │   │  100  │   │       │       │
     └───────┘   │       │       │   └───────┘   │       │       │
         │       │       │       │       │       │       │       │
     ┌───┴───┐ ┌─┴──┐ ┌──┴─┐ ┌───┴──┐ ┌──┴───┐ ┌─┴──┐ ┌──┴─┐ ┌───┴──┐
     │web_0_0│ │web │ │web │ │web   │ │web   │ │web │ │web │ │web   │
     │10.0.0.│ │0_1 │ │0_2 │ │ 0_3  │ │ 1_0  │ │1_1 │ │1_2 │ │ 1_3  │
     │  10   │ │    │ │    │ │      │ │      │ │    │ │    │ │      │
     └───────┘ └────┘ └────┘ └──────┘ └──────┘ └────┘ └────┘ └──────┘
         │       │       │       │       │       │       │       │
     ┌───┴───┐ ┌─┴──┐ ┌──┴─┐ ┌───┴──┐ ┌──┴───┐ ┌─┴──┐ ┌──┴─┐ ┌───┴──┐
     │pc_0_0 │ │pc  │ │pc  │ │pc    │ │pc    │ │pc  │ │pc  │ │pc    │
     │10.0.0.│ │0_1 │ │0_2 │ │ 0_3  │ │ 1_0  │ │1_1 │ │1_2 │ │ 1_3  │
     │  2    │ │    │ │    │ │      │ │      │ │    │ │    │ │      │
     └───────┘ └────┘ └────┘ └──────┘ └──────┘ └────┘ └────┘ └──────┘
```

## Configuration

### Routing Layer (26 machines)

| Layer | Count | AS Numbers | Routing |
|-------|-------|------------|---------|
| Super-spine | 2 | AS 65000 | EBGP |
| Spine | 8 | AS 65100-65113 | EBGP |
| Leaf | 8 | AS 65200-65243 | EBGP |
| Hosts | 8 | - | Static |

### Service Layer (12 machines)

| Component | Count | IP Range | Service |
|-----------|-------|----------|---------|
| DNS Servers | 2 | 10.X.0.100 | BIND9 |
| Web Servers | 8 | 10.X.Y.10 | Python HTTP |
| External Clients | 2 | 192.168.X.2 | Test clients |

**Total: 38 machines**

## IP Addressing Scheme

### P2P Links (172.16.0.0/16)
- /31 subnets for router-to-router connections
- Same as dc_clos_worker

### Host Networks (10.X.Y.0/24)
| Device | IP Address | Gateway |
|--------|------------|---------|
| pc_X_Y | 10.X.Y.2/24 | 10.X.Y.1 |
| dns_0 | 10.0.0.100/24 | 10.0.0.1 |
| dns_1 | 10.1.0.100/24 | 10.1.0.1 |
| web_X_Y | 10.X.Y.10/24 | 10.X.Y.1 |

### External Client Networks (192.168.X.0/24)
| Device | IP Address | Gateway |
|--------|------------|---------|
| client_0 | 192.168.0.2/24 | 192.168.0.1 (super_spine_0) |
| client_1 | 192.168.1.2/24 | 192.168.1.1 (super_spine_1) |

## DNS Configuration

### Zones
- `pod0.dc` - Served by dns_0 (10.0.0.100)
- `pod1.dc` - Served by dns_1 (10.1.0.100)
- `dc` - Top-level zone

### DNS Records

**pod0.dc zone:**
```
web0.pod0.dc  -> 10.0.0.10
web1.pod0.dc  -> 10.0.1.10
web2.pod0.dc  -> 10.0.2.10
web3.pod0.dc  -> 10.0.3.10
```

**pod1.dc zone:**
```
web0.pod1.dc  -> 10.1.0.10
web1.pod1.dc  -> 10.1.1.10
web2.pod1.dc  -> 10.1.2.10
web3.pod1.dc  -> 10.1.3.10
```

## Web Servers

All web servers run Python HTTP server on port 80:
```bash
python3 -m http.server 80
```

Each serves a unique index.html identifying the server.

## Directory Structure

```
assets/
├── lab.conf                           # Kathara lab configuration
├── config.md                          # This documentation
│
├── # Routing Layer (from dc_clos_worker)
├── super_spine_router_X.startup       # 2 super-spine routers
├── super_spine_router_X/etc/frr/      # FRR configs
├── spine_router_X_Y.startup           # 8 spine routers
├── spine_router_X_Y/etc/frr/          # FRR configs
├── leaf_router_X_Y.startup            # 8 leaf routers
├── leaf_router_X_Y/etc/frr/           # FRR configs
├── pc_X_Y.startup                     # 8 host PCs
│
├── # DNS Servers (new)
├── dns_0.startup                      # DNS server startup
├── dns_0/etc/bind/named.conf          # BIND9 config
├── dns_0/etc/bind/db.*.dc             # Zone files
├── dns_1.startup
├── dns_1/etc/bind/                    # DNS 1 configs
│
├── # Web Servers (new)
├── web_X_Y.startup                    # 8 web server startups
├── web_X_Y/var/www/html/index.html    # Web content
│
└── # External Clients (new)
    ├── client_0.startup               # External client 0
    └── client_1.startup               # External client 1
```

## Testing Commands

### DNS Testing
```bash
# From any client
dig @10.0.0.100 web0.pod0.dc
nslookup web1.pod1.dc 10.1.0.100
```

### HTTP Testing
```bash
# Direct by IP
curl http://10.0.0.10/
# Via DNS (if resolv.conf configured)
curl http://web0.pod0.dc/
```

### Connectivity Testing
```bash
# From external client
ping -c 4 10.0.0.10
traceroute 10.1.2.10
```

## Task Family

This environment is used by the `service_failure` task family which tests:
- DNS server failures
- DNS misconfiguration
- Web server failures
- Routing failures affecting services
- Baseline healthy service verification

See: `nika/tasks/service_failure/`
