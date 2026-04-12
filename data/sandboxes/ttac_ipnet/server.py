import json
import logging
import os
import re

from flask import Flask, request, jsonify

# === 0. Initialization & Logging Configuration ===
app = Flask(__name__)
TXT_FILE_DIRECTORY = os.environ.get("TXT_FILE_DIRECTORY", "./devices_outputs")
LOG_FILE = "agent_errors.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.WARNING,
    format="%(asctime)s - [AGENT_ERROR] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# === 0.1 Preload all command outputs into memory on startup ===
# key: "{question_dir}/{device_name}/{safe_filename}.txt"  value: file content string
# question_dir is the question number (e.g., "2") or "others"
COMMAND_CACHE = {}
QUESTION_DIRS = set()  # Record question directory names existing under devices_outputs


def _preload_command_outputs(base_dir):
    """Load all .txt files under devices_outputs/{N|others}/{device_name}/ into memory dictionary at once"""
    count = 0
    if not os.path.exists(base_dir):
        return count
    for question_dir_name in os.listdir(base_dir):
        question_dir = os.path.join(base_dir, question_dir_name)
        if not os.path.isdir(question_dir):
            continue
        QUESTION_DIRS.add(question_dir_name)
        for device_name in os.listdir(question_dir):
            device_dir = os.path.join(question_dir, device_name)
            if not os.path.isdir(device_dir):
                continue
            for filename in os.listdir(device_dir):
                if not filename.endswith(".txt"):
                    continue
                filepath = os.path.join(device_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    cache_key = f"{question_dir_name}/{device_name}/{filename}"
                    COMMAND_CACHE[cache_key] = f.read()
                    count += 1
    return count

_loaded_files = _preload_command_outputs(TXT_FILE_DIRECTORY)
print(f"[*] Preloaded {_loaded_files} command output files into memory (Question directories: {len(QUESTION_DIRS)})")


# === GENERATED: QUESTION_LIMITS_CONFIG BEGIN ===
_QUESTION_LIMITS_CONFIG = {}
_qlc_path = os.environ.get("QUESTION_LIMITS_CONFIG", os.path.join(os.path.dirname(os.path.abspath(__file__)), "question_limits_config.json"))
if os.path.exists(_qlc_path):
    with open(_qlc_path, "r", encoding="utf-8") as _qlc_f:
        _QUESTION_LIMITS_CONFIG = json.load(_qlc_f)
    print(f"[*] Loaded question_limits_config.json ({len(_QUESTION_LIMITS_CONFIG)} questions)")
# === GENERATED: QUESTION_LIMITS_CONFIG END ===


# === 1. Device and Vendor Mapping Dictionary ===
DEVICE_VENDOR_MAP = {

    "Janus-Prime-01": "huawei",
    "Janus-Prime-02": "huawei",
    "Aegis-Prime-01": "huawei",
    "Aegis-Prime-02": "huawei",
    "Demeter-Prime-01": "huawei",
    "Demeter-Prime-02": "huawei",
    "Atlas-Prime-01": "huawei",
    "Atlas-Prime-02": "huawei",
    "Hermes-Prime-01": "huawei",
    "Hermes-Prime-02": "huawei",
    "Eon-Node-01": "huawei",
    "Gaia-Node-01": "huawei",
    "Aegis-Node-01": "huawei",
    "Janus-Node-01": "huawei",
    "Janus-Node-02": "huawei",
    "Atlas-Node-01": "huawei",
    "Atlas-Node-02": "huawei",
    "Demeter-Node-01": "huawei",
    "Demeter-Node-02": "huawei",
    "Hermes-Node-02": "huawei",
    "Hermes-Node-01": "huawei",
    "PX1": "huawei",

    # 32-node financial network devices (network_3)
    "Alpha-Center-01": "huawei",
    "Alpha-Center-02": "huawei",
    "Beta-Portal-01": "huawei",
    "Beta-Portal-02": "huawei",
    "Beta-Aegis-01": "huawei",
    "Beta-Aegis-02": "huawei",
    "Beta-Axis-01": "huawei",
    "Beta-Axis-02": "huawei",
    "Beta-Node-01": "huawei",
    "Beta-Node-02": "huawei",
    "Beta-Node-03": "huawei",
    "Beta-Node-04": "huawei",
    "Gamma-Portal-01": "huawei",
    "Gamma-Portal-02": "huawei",
    "Gamma-Aegis-01": "huawei",
    "Gamma-Aegis-02": "huawei",
    "Gamma-Axis-01": "huawei",
    "Gamma-Axis-02": "huawei",
    "Gamma-Node-01": "huawei",
    "Gamma-Node-02": "huawei",
    "Gamma-Node-03": "huawei",
    "Gamma-Node-04": "huawei",
    "Delta-Portal-01": "huawei",
    "Delta-Portal-02": "huawei",
    "Delta-Aegis-01": "huawei",
    "Delta-Aegis-02": "huawei",
    "Delta-Axis-01": "huawei",
    "Delta-Axis-02": "huawei",
    "Delta-Node-01": "huawei",
    "Delta-Node-02": "huawei",
    "Delta-Node-03": "huawei",
    "Delta-Node-04": "huawei",

    "PSS": "cisco"
}

# === 2. Fully supported CLI regex rules dictionary (Whitelist) ===
SUPPORTED_COMMANDS = {
    "huawei": [
        r"^display current-configuration$", r"^display logbuffer$", r"^display alarm active$",
        r"^display memory-usage$", r"^display lldp neighbor brief$", r"^ping -a \S+ \S+$",
        r"^tracert -a \S+ \S+$", r"^display interface brief$", r"^display interface description$",
        r"^display eth-trunk \S+$", r"^display vlan$", r"^display mac-address$",
        r"^display stp brief$", r"^display stp interface brief$", r"^display stp interface \S+$",  # Added: Specify interface STP
        r"^display ip interface brief$", r"^display ipv6 interface \S+( \S+)?$",  # Compatible with 1 or 2 parameters
        r"^display arp$", r"^display ipv6 neighbors$",
        r"^display ip routing-table$", r"^display ip routing-table vpn-instance \S+$",
        r"^display ipv6 routing-table$", r"^display ospf peer$", r"^display ospf routing$",
        r"^display ospf lsdb$", r"^display bgp evpn all routing-table$", r"^display bgp vpnv4 all routing-table$",
        r"^display vxlan tunnel$", r"^display vxlan troubleshooting$", r"^display vrrp verbose$",
        r"^display bfd session all$", r"^display ip pool$", r"^display srv6-te policy status$",
        r"^display srv6-te policy$", r"^display segment-routing ipv6 local-sid end forwarding$",
        r"^display segment-routing ipv6 local-sid end-x forwarding$", r"^display ip vpn-instance \S+$"
    ],
    "cisco": [
        r"^show running-config$", r"^show logging$", r"^show facility-alarm status$",
        r"^show processes memory$", r"^show lldp neighbors$", r"^ping \S+ source \S+$",
        r"^traceroute \S+ source \S+$", r"^(show ip int brief|show int status)$",
        r"^show interface description$", r"^show etherchannel summary$", r"^show vlan brief$",
        r"^show mac address-table$", r"^show spanning-tree brief$", r"^show spanning-tree interface \S+$",
        r"^show ip interface brief$", r"^show ipv6 interface \S+( \S+)?$", r"^show ip arp$",
        r"^show ipv6 neighbors$", r"^show ip route$", r"^show ip route vrf \S+$",
        r"^show ipv6 route$", r"^show ip ospf neighbor$", r"^show ip route ospf$",
        r"^show ip ospf database$", r"^show bgp l2vpn evpn$", r"^show bgp vpnv4 unicast all$",
        r"^(show nve vni|show nve peers)$", r"^show nve.*$", r"^show vrrp detail$",
        r"^show bfd neighbors$", r"^show ip dhcp pool$", r"^show segment-routing srv6 policy$",
        r"^show segment-routing srv6 sid$", r"^show ip vrf \S+$"
    ],
    "h3c": [
        r"^display current-configuration$", r"^display logbuffer$", r"^display alarm active$",
        r"^display memory$", r"^display lldp neighbor-list$", r"^ping -a \S+ \S+$",
        r"^tracert -a \S+ \S+$", r"^display interface brief$", r"^display interface description$",
        r"^display link-aggregation summary$", r"^display vlan$", r"^display mac-address$",
        r"^display stp brief$", r"^display stp interface brief$", r"^display stp interface \S+$",
        r"^display ip interface brief$", r"^display ipv6 interface \S+( \S+)?$",
        r"^display arp all$", r"^display ipv6 neighbor$",
        r"^display ip routing-table$", r"^display ip routing-table vpn-instance \S+$",
        r"^display ipv6 routing-table$", r"^display ospf peer$", r"^display ospf routing$",
        r"^display ospf lsdb$", r"^display bgp l2vpn evpn$", r"^display bgp vpnv4 all routing-table$",
        r"^display vxlan tunnel$", r"^display vxlan troubleshooting$", r"^display vrrp verbose$",
        r"^display bfd session all$", r"^display ip pool$", r"^display segment-routing ipv6 te policy$",
        r"^display segment-routing ipv6 local-sid$", r"^display ip vpn-instance \S+$"
    ]
}

# === 3. Vendor-specific valid keywords ===
VENDOR_KEYWORDS = {
    "huawei": {
        "display", "ping", "tracert", "-a", "current-configuration", "logbuffer", "alarm", "active",
        "memory-usage", "lldp", "neighbor", "brief", "interface", "description", "eth-trunk", "vlan",
        "mac-address", "stp", "ip", "ipv6", "arp", "all", "neighbors", "routing-table", "vpn-instance",
        "ospf", "peer", "routing", "lsdb", "bgp", "evpn", "vpnv4", "vxlan", "tunnel", "troubleshooting",
        "vrrp", "verbose", "bfd", "session", "pool", "srv6-te", "policy", "status", "segment-routing",
        "local-sid", "end", "forwarding", "end-x"
    },
    "cisco": {
        "show", "ping", "traceroute", "source", "running-config", "logging", "facility-alarm", "status",
        "processes", "memory", "lldp", "neighbors", "ip", "int", "brief", "interface", "description",
        "etherchannel", "summary", "vlan", "mac", "address-table", "spanning-tree", "ipv6", "arp",
        "route", "vrf", "ospf", "neighbor", "database", "bgp", "l2vpn", "evpn", "vpnv4", "unicast",
        "all", "nve", "vni", "peers", "vrrp", "detail", "bfd", "dhcp", "pool", "segment-routing", "srv6", "policy",
        "sid"
    },
    "h3c": {
        "display", "ping", "tracert", "-a", "current-configuration", "logbuffer", "alarm", "active",
        "memory", "lldp", "neighbor-list", "interface", "brief", "description", "link-aggregation",
        "summary", "vlan", "mac-address", "stp", "ip", "ipv6", "arp", "all", "neighbor", "routing-table",
        "vpn-instance", "ospf", "peer", "routing", "lsdb", "bgp", "l2vpn", "evpn", "vpnv4", "vxlan",
        "tunnel", "troubleshooting", "vrrp", "verbose", "bfd", "session", "pool", "segment-routing",
        "te", "policy", "local-sid"
    }
}


def generate_cli_error(vendor, device_name, command):
    """
    Syntax and spelling error engine (Handles invalid commands)
    """
    prompt = f"<{device_name}>" if vendor in ["huawei", "h3c"] else f"{device_name}#"
    full_command_line = f"{prompt} {command}"

    words = command.split()
    if not words:
        return f"{prompt}\n"

    valid_words = VENDOR_KEYWORDS.get(vendor, set())
    vendor_rules = SUPPORTED_COMMANDS.get(vendor, [])

    error_word = words[-1]
    error_type = "incomplete"

    for i in range(len(words) - 1, 0, -1):
        prefix_cmd = " ".join(words[:i])
        if any(re.match(rule, prefix_cmd, re.IGNORECASE) for rule in vendor_rules):
            error_word = words[i]
            error_type = "too_many_parameters"
            break
    else:
        previous_word = None
        for word in words:
            word_lower = word.lower()
            if word_lower in valid_words:
                previous_word = word_lower
                continue

            matched_kws = [kw for kw in valid_words if kw.startswith(word_lower)]
            if len(matched_kws) == 1:
                previous_word = matched_kws[0]
                continue
            elif len(matched_kws) > 1:
                error_word = word
                error_type = "ambiguous"
                break

            if previous_word in ["interface", "int", "eth-trunk", "vlan"]:
                if not re.search(r'[0-9]', word):
                    error_word = word
                    error_type = "wrong_parameter"
                    break
                else:
                    previous_word = "<CONSUMED_PARAM>"
                    continue
            elif previous_word in ["vpn-instance", "vrf", "policy", "source"]:
                previous_word = "<CONSUMED_PARAM>"
                continue
            elif re.search(r'[0-9\./:-]', word):
                previous_word = "<CONSUMED_PARAM>"
                continue
            else:
                error_word = word
                error_type = "unrecognized"
                break

        if error_type not in ["ambiguous", "unrecognized", "wrong_parameter", "too_many_parameters"]:
            error_word = words[-1]
            error_type = "incomplete"

    try:
        match = re.search(r'\b' + re.escape(error_word) + r'\b', command)
        cmd_index = match.start() if match else command.find(error_word)
    except:
        cmd_index = command.find(error_word)

    if cmd_index == -1:
        cmd_index = len(command) - len(error_word)

    padding_length = len(prompt) + 1 + cmd_index
    pointer_line = " " * padding_length + "^"

    error_msg = ""
    if error_type == "ambiguous":
        if vendor == "cisco":
            pointer_line = ""
            error_msg = f'% Ambiguous command:  "{command}"'
        else:
            error_msg = f"Error: Ambiguous command found at '^' position." if vendor == "huawei" else f"% Ambiguous command found at '^' position."
    elif error_type == "unrecognized":
        error_msg = f"% Invalid input detected at '^' marker." if vendor == "cisco" else (
            f"Error: Unrecognized command found at '^' position." if vendor == "huawei" else f"% Unrecognized command found at '^' position.")
    elif error_type == "wrong_parameter":
        error_msg = f"% Invalid input detected at '^' marker." if vendor == "cisco" else (
            f"Error: Wrong parameter found at '^' position." if vendor == "huawei" else f"% Wrong parameter found at '^' position.")
    elif error_type == "too_many_parameters":
        error_msg = f"% Invalid input detected at '^' marker." if vendor == "cisco" else (
            f"Error: Too many parameters found at '^' position." if vendor == "huawei" else f"% Too many parameters found at '^' position.")
    elif error_type == "incomplete":
        if vendor == "cisco":
            pointer_line = ""
            error_msg = f"% Incomplete command."
        else:
            error_msg = f"Error: Incomplete command found at '^' position." if vendor == "huawei" else f"% Incomplete command found at '^' position."

    if pointer_line:
        return f"{full_command_line}\n{pointer_line}\n{error_msg}"
    return f"{full_command_line}\n{error_msg}"


# === 5. API Routing Endpoints ===

# --- Added: API to get question content ---

@app.route('/api/agent/execute', methods=['POST'])
def execute_command():
    data = request.json
    if not data or "device_name" not in data or "command" not in data or "question_number" not in data:
        return jsonify({"error": "Missing required parameter 'device_name', 'command', or 'question_number'"}), 400

    device_name = data.get("device_name")
    command = data.get("command").strip()
    question_number = data.get("question_number")

    vendor = DEVICE_VENDOR_MAP.get(device_name)
    if not vendor:
        return jsonify({"error": f"Device '{device_name}' not found"}), 404

    # --- A. Validate against regex whitelist ---
    vendor_rules = SUPPORTED_COMMANDS.get(vendor, [])
    is_supported = any(re.match(rule, command, re.IGNORECASE) for rule in vendor_rules)

    # === GENERATED: LIMITS_CHECK_LOGIC BEGIN ===
    # Check no_permission limit based on question_number + device_name + command
    _q_key = f"question_{question_number}"
    _q_conf = _QUESTION_LIMITS_CONFIG.get(_q_key, {})
    _no_perm = _q_conf.get("no_permission", {})
    if command in _no_perm and device_name in _no_perm[command]:
        return jsonify({
            "status": "execution_failed",
            "device_name": device_name,
            "vendor": vendor,
            "command_executed": command,
            "result": "Error: No permission to perform the operation"
        }), 403
    # === GENERATED: LIMITS_CHECK_LOGIC END ===

    # --- B. Branch: Invalid command (Triggers dynamic syntax error simulation) ---
    if not is_supported:
        cli_error_output = generate_cli_error(vendor, device_name, command)
        logging.warning(f"Device: {device_name} ({vendor}) | Syntax Error: '{command}'")

        return jsonify({
            "status": "execution_failed",
            "device_name": device_name,
            "vendor": vendor,
            "command_executed": command,
            "result": cli_error_output
        }), 422

    # --- C. Branch: Valid command, query from memory cache ---
    safe_filename = command.replace("/", "_").replace("\\", "_").replace("..", "").replace(" ", "_")
    # Prioritize searching the question number directory, fallback to 'others' directory if it doesn't exist
    q_dir = str(question_number) if str(question_number) in QUESTION_DIRS else "others"
    cache_key = f"{q_dir}/{device_name}/{safe_filename}.txt"
    content = COMMAND_CACHE.get(cache_key)

    # === Special handling: Simulate missing physical resources for specific parameterized commands ===
    if content is None:
        cmd_lower = command.lower()
        words = command.split()

        # Define prefix rules that trigger "resource missing" errors, and the word index (0-based) where parameter x is located
        special_missing_rules = [
            ("display eth-trunk", 2),
            ("display stp interface", 3),
            ("display ipv6 interface", 3),
            ("display ip routing-table vpn-instance", 4)
        ]

        is_resource_missing = False
        error_word = ""

        # Iterate through special rules, extract parameter x if prefix matches and word count is sufficient
        for prefix, param_idx in special_missing_rules:
            if cmd_lower.startswith(prefix) and len(words) > param_idx:
                error_word = words[param_idx]
                is_resource_missing = True
                break

        # Trigger parameter pointing error
        if is_resource_missing:
            prompt_str = f"<{device_name}>" if vendor in ["huawei", "h3c"] else f"{device_name}#"
            full_command_line = f"{prompt_str} {command}"

            # Pinpoint the first character position of parameter x
            try:
                match = re.search(r'\b' + re.escape(error_word) + r'\b', command)
                cmd_index = match.start() if match else command.find(error_word)
            except:
                cmd_index = command.find(error_word)

            padding_length = len(prompt_str) + 1 + cmd_index
            pointer_line = " " * padding_length + "^"

            # Vendor-specific error echo
            if vendor == "cisco":
                error_msg = f"% Invalid input detected at '^' marker."
            elif vendor == "huawei":
                error_msg = f"Error: Wrong parameter found at '^' position."
            else:
                error_msg = f"% Wrong parameter found at '^' position."

            cli_error_output = f"{full_command_line}\n{pointer_line}\n{error_msg}"

            logging.warning(f"Device: {device_name} ({vendor}) | Resource Not Found (Missing TXT) for: '{command}'")

            # Return 422 status code to Agent, indicating parameter anomaly
            return jsonify({
                "status": "execution_failed",
                "device_name": device_name,
                "vendor": vendor,
                "command_executed": command,
                "result": cli_error_output,
                "reason": f"Simulated resource '{error_word}' not found"
            }), 422

        # If not one of the 4 special parameterized commands above, throw normal HTTP 404
        return jsonify(
            {"error": "Error: No permission to perform the operation", "filename": f"{safe_filename}.txt"}), 404

    # --- D. Cache hit, return directly ---
    prompt = f"<{device_name}>" if vendor in ["huawei", "h3c"] else f"{device_name}#"
    return jsonify({
        "status": "success",
        "device_name": device_name,
        "vendor": vendor,
        "command_executed": command,
        "result": f"{prompt} {command}\n{content}"
    }), 200


@app.route('/health')
def health():
    return jsonify({"status": "ok"})