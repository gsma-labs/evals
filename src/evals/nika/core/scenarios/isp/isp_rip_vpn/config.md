# ISP RIP Small Internet VPN Topology

## Overview

A small “internet-like” topology with two site routers (router1, router2) and a gateway router between them and an external zone. Routing is done with **RIP** (FRR). Hosts and external services use **WireGuard VPN**; the VPN server and web servers are reachable over the VPN (172.16.1.0/24). Used for VPN and routing troubleshooting.

```
     host_1 (WG)          router1          gateway_router         external_router_1
         |                   |                    |                      |
     router1_host_1  ---- router1_router2  ---- router1_gateway  ---- external_router_1_gateway
                              |                    |                      |
                         router2_router1     router2_gateway             |
                              |                    |                     +-- vpn_server_1 (WG)
     host_2 (WG)          router2                 |                     +-- web_server_1_1 (WG)
         |                   |                    |                     +-- web_server_1_2 (WG)
     router2_host_2  ---- router2_gateway  ---- ...
```

## Configuration

### Network Layers

| Component | Count | Protocol / Role |
|-----------|-------|-----------------|
| Site Routers | 2 (router1, router2) | FRR RIP; connect to gateway and to local host |
| Gateway Router | 1 | FRR RIP; connects site routers and external_router_1 |
| External Router | 1 | FRR RIP; connects gateway, VPN server, web servers |
| Hosts | 2 (host_1, host_2) | WireGuard client (kathara/nika-wireguard) |
| VPN Server | 1 (vpn_server_1) | WireGuard server; VPN subnet 172.16.1.0/24 |
| Web Servers | 2 (web_server_1_1, web_server_1_2) | Apache on VPN IP; reachable only via VPN |

**Total (size_s):** 9 machines. size_m and size_l add more routers/hosts/servers via lab_generator.

### Routing

- **RIP** on all FRR routers; networks 192.168.0.0/16 and site-specific networks; static redistribution.
- **WireGuard:** VPN server (vpn_server_1) at 20.0.0.2 (WG endpoint); VPN net 172.16.1.0/24; web servers listen on VPN IP only.

### IP Addressing

- P2P router links: /31 from 192.168.x.x or allocated pool.
- Host networks: per-site subnets off router1/router2.
- VPN: 172.16.1.0/24; server 172.16.1.1; WG server endpoint 20.0.0.2.

## Directory Structure

```
isp_rip_vpn/
├── config.md
├── lab_generator.py
├── size_s/
│   ├── compose.yaml
│   └── topology/
│       ├── lab.conf
│       ├── router1.startup, router2.startup, gateway_router.startup, external_router_1.startup
│       ├── host_1.startup, host_2.startup
│       ├── vpn_server_1.startup, web_server_1_1.startup, web_server_1_2.startup
│       └── (WireGuard keys from ../../_utils/wireguard, RIP utils from ../../_utils/rip)
├── size_m/
│   └── ...
└── size_l/
    └── ...
```

## Testing Commands

### RIP
```bash
# From any FRR router
vtysh -c "show ip rip"
vtysh -c "show ip route"
```

### VPN and HTTP (from host after WG up)
```bash
ping 172.16.1.1
curl http://172.16.1.x/   # web server on VPN
```

### Connectivity
```bash
ping -c 4 <gateway_or_peer>
traceroute <target>
```
