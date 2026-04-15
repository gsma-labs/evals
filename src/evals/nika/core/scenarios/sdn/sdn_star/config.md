# SDN Star Topology

## Overview

A **star** topology: one central switch (switch_0) connected to four edge switches (switch_1–4); each edge switch has one host. All switches are OpenFlow (kathara/sdn) and are controlled by a **Ryu controller** (kathara/nika-ryu). The controller connects to every switch over a shared `switch_controller` network.

```
                    controller (Ryu)
                           |
                    switch_controller
                    /  |  |  |  \
              switch_0 (center)
              /   |   |   \
        switch_1 switch_2 switch_3 switch_4
           |        |        |        |
         host_1   host_2   host_3   host_4
```

## Configuration

### Network Layers

| Component | Count | Role |
|-----------|-------|------|
| Center Switch | 1 (switch_0) | OpenFlow switch; links to switch_1–4 and controller |
| Edge Switches | 4 (switch_1–4) | OpenFlow switch; one host each, link to switch_0 and controller |
| Hosts | 4 (host_1–4) | kathara/nika-base |
| Controller | 1 (controller) | kathara/nika-ryu, bridged |

**Total:** 10 machines. size_m and size_l scale the star (more arms/hosts) via lab_generator.

### Protocols

- **OpenFlow:** All switches connect to the Ryu controller; forwarding is controller-driven.
- **Controller:** Ryu; single point of control for the whole star.

### Links

- switch_0 ↔ switch_1, switch_2, switch_3, switch_4; switch_0 ↔ controller.
- switch_i ↔ host_i; switch_i ↔ controller (i=1..4).

## Directory Structure

```
sdn_star/
├── config.md
├── lab_generator.py
├── size_s/
│   ├── compose.yaml
│   └── topology/
│       ├── lab.conf
│       ├── switch_0.startup .. switch_4.startup
│       ├── host_1.startup .. host_4.startup
│       └── controller.startup
├── size_m/
│   └── ...
└── size_l/
    └── ...
```

## Testing Commands

### Connectivity (from host)
```bash
ping -c 4 <other_host_ip>
```

### Controller
Ensure Ryu is running and switches show connected; host-to-host traffic should use controller-installed flows.
