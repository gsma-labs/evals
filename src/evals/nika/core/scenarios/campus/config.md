# Campus Scenarios (Overview)

Campus scenarios are enterprise hierarchical networks using FRR OSPF (core–distribution–access) with optional DHCP and server farm (DNS, web, load balancer).

| Scenario | Description | Config |
|----------|-------------|--------|
| **campus_static** | OSPF multi-area; hosts with static IPs; server farm with DNS (Bind) and Apache web servers. | [campus_static/config.md](campus_static/config.md) |
| **campus_dhcp** | OSPF; hosts get IPs via DHCP; server farm with DNS, web servers, Nginx load balancer, DHCP server. | [campus_dhcp/config.md](campus_dhcp/config.md) |

Each scenario has size variants: `size_s`, `size_m`, `size_l` (see `scenario.yaml` and per-scenario `config.md` for topology and testing).
