# Scenario Catalog

This directory contains the runnable network environments used by NIKA tasks.
Each scenario provides one or more Kathara labs (usually `size_s`, `size_m`, `size_l`) and corresponding `compose.yaml` files.

## Supported Scenario Categories

- `campus`: enterprise campus-style OSPF topologies.
- `data_center`: Clos-like data center fabrics with BGP and optional services.
- `isp`: provider-style routing and VPN environments.
- `sdn`: OpenFlow + controller based topologies.
- `p4`: programmable data-plane (BMv2/P4) topologies.

## Supported Scenarios

| Category | Scenario | Sizes | Summary |
|----------|----------|-------|---------|
| `campus` | `campus_static` | `s`, `m`, `l` | OSPF campus hierarchy with static host addressing and server farm (DNS/web). |
| `campus` | `campus_dhcp` | `s`, `m`, `l` | OSPF campus hierarchy with DHCP clients and service stack (DNS/web/LB/DHCP). |
| `data_center` | `dc_clos_worker` | `s`, `m`, `l` | BGP-only 3-tier Clos fabric focused on routing/connectivity troubleshooting. |
| `data_center` | `dc_clos_service` | `s`, `m`, `l` | Clos fabric with added DNS/web/external clients for service-plane failures. |
| `isp` | `isp_rip_vpn` | `s`, `m`, `l` | RIP-based ISP-like topology with WireGuard VPN and VPN-reachable services. |
| `sdn` | `sdn_clos` | `s`, `m`, `l` | Spine-leaf OpenFlow fabric controlled by Ryu. |
| `sdn` | `sdn_star` | `s`, `m`, `l` | Star OpenFlow topology with a central switch and Ryu controller. |
| `p4` | `p4_counter` | fixed | P4/BMv2 multi-switch topology for forwarding/counter behavior. |
| `p4` | `p4_int` | fixed | P4 INT topology with collector for telemetry reporting paths. |
| `p4` | `p4_mpls` | fixed | P4 MPLS multi-switch topology for label push/swap/pop behavior. |
| `p4` | `p4_bloom_filter` | fixed | Minimal P4 topology for bloom-filter/set-membership style behavior. |

## Scenario Config References

Detailed topology and testing docs are available in:

- `campus/config.md`
- `campus/campus_static/config.md`
- `campus/campus_dhcp/config.md`
- `data_center/dc_clos_worker/config.md`
- `data_center/dc_clos_service/config.md`
- `isp/isp_rip_vpn/config.md`
- `sdn/sdn_clos/config.md`
- `sdn/sdn_star/config.md`
- `p4/p4_counter/config.md`
- `p4/p4_int/config.md`
- `p4/p4_mpls/config.md`
- `p4/p4_bloom_filter/config.md`

## Compose Inventory

Current compose coverage in this directory:

- 7 scenarios with `size_s` / `size_m` / `size_l` variants.
- 4 fixed-size P4 scenarios with a single `compose.yaml`.

Use these compose paths in dataset sandbox definitions (for example `sandbox: [kathara, "sdn/sdn_clos/size_s/compose.yaml"]`).
