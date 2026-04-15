# Campus OSPF Enterprise DHCP Topology

## Overview

An enterprise hierarchical network using FRR OSPF with a core–distribution–access structure. Hosts receive addresses via DHCP from a central DHCP server. The server farm includes a DNS server (Bind), multiple web servers, a load balancer (Nginx) with backend web servers, and a DHCP server. All routing is OSPF; hosts and servers use static/DHCP addressing.

```
                    ┌──────────────┐
                    │router_core_1│
                    │  (Area 0)   │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
   ┌────┴────┐       ┌─────┴─────┐      ┌──────┴────┐
   │router_  │       │router_    │      │router_    │
   │core_2   │       │core_3     │      │core_1     │
   └────┬────┘       └─────┬─────┘      └────┬─────┘
        │                  │                  │
   ┌────┴────┐             │             ┌────┴────┐
   │router_  │             │             │router_  │
   │dist_1_1 │             │             │dist_2_1 │
   └────┬────┘             │             └────┬────┘
        │                  │                  │
   ┌────┴────┐             │             ┌────┴────┐
   │switch_  │             │             │switch_  │
   │access_  │             │             │access_  │
   │1_1_1    │             │             │2_1_1    │
   └────┬────┘             │             └────┬────┘
        │                  │                  │
   host_1_1_1_1       server_access_router    host_2_1_1_1
   (DHCP client)      (Area 0)                (DHCP client)
                            │
        ┌───────────────────┼───────────────────┐
        │   │   │   │   │   │   │   │
     dns  web0 web1 web2 web3 lb  dhcp  backend_web_0/1/2
     _server
```

## Configuration

### Network Layers

| Layer | Count (size_s) | Protocol / Role |
|-------|----------------|-----------------|
| Core Routers | 3 | OSPF Area 0 |
| Distribution Routers | 2 (dist_1_1, dist_2_1) | OSPF Area 1 |
| Access Switches | 2 (switch_access_1_1_1, 2_1_1) | L2 bridge |
| Hosts | 2 (host_1_1_1_1, host_2_1_1_1) | DHCP client |
| Server Access Router | 1 | OSPF Area 0 |
| DNS Server | 1 | BIND, static IP |
| Web Servers | 4 (web_server_0–3) | Apache, static |
| Load Balancer | 1 | Nginx (kathara/nika-nginx) |
| Backend Web | 3 (backend_web_0–2) | Behind LB |
| DHCP Server | 1 | DHCP server |

**Total (size_s):** 20 machines. size_m and size_l scale up distribution, access, and hosts via lab_generator.

### IP Addressing Scheme

- **P2P infrastructure (172.16.0.0/16):** /31 for router–router links.
- **Host networks:** Subnets per (core, dist); hosts get IPs via DHCP from `dhcp_server`.
- **Server farm:** Server access router connects dns_server, web_server_0–3, load_balancer, dhcp_server; load_balancer has a separate link to backend_web_0/1/2 (lb_backend_link).

### OSPF Areas

- **Area 0:** Core routers (mesh) and server_access_router.
- **Area 1:** Distribution routers (dist_1_1, dist_2_1) connected to core1 and core2.

### Services

- **DNS:** BIND on `dns_server`; zone and records as configured in topology.
- **Web:** Apache on web_server_0–3 and backend_web_0/1/2; Nginx load balancer in front of backend_web_*.
- **DHCP:** Central `dhcp_server`; hosts use DHCP for address and default gateway.

## Directory Structure

```
campus_dhcp/
├── config.md
├── lab_generator.py
├── size_s/
│   ├── compose.yaml
│   └── topology/
│       ├── lab.conf
│       ├── router_core_*.startup, router_dist_*.startup
│       ├── switch_access_*.startup, host_*.startup
│       ├── server_access_router/, dns_server/, web_server_*/,
│       ├── load_balancer/, dhcp_server/, backend_web_*/
│       └── .../etc/frr/, etc/bind/, etc/nginx/, ...
├── size_m/
│   └── ...
└── size_l/
    └── ...
```

## Testing Commands

### OSPF
```bash
vtysh -c "show ip ospf neighbor"
vtysh -c "show ip route"
```

### DHCP (from host after boot)
```bash
ip addr show
ip route show
```

### DNS
```bash
dig @<dns_server_ip> <record>
nslookup <name> <dns_server_ip>
```

### HTTP / Load balancer
```bash
curl http://<lb_ip>/
curl http://<web_server_ip>/
```

### Connectivity
```bash
ping -c 4 <gateway_or_server>
traceroute <target>
```
