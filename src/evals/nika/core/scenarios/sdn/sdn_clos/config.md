# SDN Clos (Spine–Leaf) Topology

## Overview

A small spine–leaf fabric where **switches** run as OpenFlow switches (kathara/sdn) and are controlled by a **Ryu controller** (kathara/nika-ryu). Hosts attach to leaf switches; spine connects leaves and the controller. All forwarding is controlled by the SDN controller; no traditional routing on switches.

```
                    controller (Ryu)
                           |
                    switch_controller (shared link)
                    /        |        \
              spine_1   (optional)   ...
                 /  \
           leaf_1   leaf_2
            /   \     /   \
       host_1_1 host_1_2  host_2_1 host_2_2
```

## Configuration

### Network Layers

| Component | Count (size_s) | Role |
|-----------|----------------|------|
| Spine | 1 (spine_1) | OpenFlow switch; connects to leaf switches and controller |
| Leaf | 2 (leaf_1, leaf_2) | OpenFlow switch; connects to spine, controller, hosts |
| Hosts | 4 (host_1_1, host_1_2, host_2_1, host_2_2) | kathara/nika-base |
| Controller | 1 (controller) | kathara/nika-ryu, bridged |

**Total (size_s):** 8 machines. size_m and size_l scale spines/leaves/hosts via lab_generator.

### Protocols

- **OpenFlow:** Switches (kathara/sdn) connect to the Ryu controller over the `switch_controller` network.
- **Controller:** Runs Ryu; installs flow entries for L2/L3 forwarding as per application.

### Links

- spine_1 ↔ leaf_1, leaf_2; spine_1 ↔ controller.
- leaf_1 ↔ host_1_1, host_1_2; leaf_2 ↔ host_2_1, host_2_2; leaf_1, leaf_2 ↔ controller.

## Directory Structure

```
sdn_clos/
├── config.md
├── lab_generator.py
├── size_s/
│   ├── compose.yaml
│   └── topology/
│       ├── lab.conf
│       ├── spine_1.startup, leaf_1.startup, leaf_2.startup
│       ├── host_1_1.startup, host_1_2.startup, host_2_1.startup, host_2_2.startup
│       └── controller.startup
├── size_m/
│   └── ...
└── size_l/
    └── ...
```

## Testing Commands

### Controller / flows (if Ryu CLI or API exposed)
```bash
# Depends on Ryu app; e.g. list flows via controller API or logs
```

### Connectivity (from host)
```bash
ping -c 4 <other_host_ip>
arping, traceroute
```

### Switch connectivity
Ensure controller is up and switches have connected; then host-to-host traffic should follow installed flows.
