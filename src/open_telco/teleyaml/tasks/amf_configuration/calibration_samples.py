"""
Calibration samples for AMF Configuration judge evaluation.
These samples contain intentional defects to produce granular/partial scores.
Kept only samples that were scored correctly by all three models (Gemini Flash, GPT-4.1, Gemini 2.5 Pro).
"""

CALIBRATION_SAMPLES = [
    # Sample 1 (was 5): Score ~20/45 - Invalid YAML with multiple content failures (simplified)
    # S1=1 (invalid YAML), S2=2, S3=1, N1=1, N2=1, N3=5, A1=1, A2=5, A3=3
    {
        "question": "Create an AMF configuration for Orange France (MCC 208, MNC 01) in a lab environment.",
        "solution": """amf:
  sbi:
    server:
      - address: 999.999.999.999
        port 99999
  ngap:
    server:
      - address: invalid-ip
  guami:
    - plmn_id:
        mcc: 123
        mnc: 45
  security:
    integrity_order: [NIA0]
    ciphering_order: [NEA0]""",
        "score": 20,
        "explanation": "Invalid YAML (missing colon after port), invalid IP (999.999.999.999), invalid port (99999), wrong PLMN (123/45 instead of 208/01). S1=1 (invalid YAML - missing colon), S2=2 (amf: present but broken structure), S3=1 (missing tai, plmn_support), N1=1 (invalid IP and port), N2=1 (wrong PLMN), N3=5 (no slices requested), A1=3 (lab allows NEA0), A2=5 (no timers), A3=5 (no features). Total: 20/45 (calibrated)",
        "category": "amf_configuration"
    },

    # Sample 2 (was 8): Score ~36/45 - Timer values out of range + missing emergency support
    # S1=5, S2=4 (legacy style), S3=5, N1=5, N2=5, N3=5, A1=5, A2=1 (invalid timers), A3=1 (missing emergency)
    {
        "question": "Configure AMF with T3512=3600s, T3502=60s, and enable emergency service support.",
        "solution": """amf:
  sbi:
    server:
      - address: 127.0.0.5
        port: 7777
  ngap:
    server:
      - address: 127.0.0.5
  guami:
    - plmn_id:
        mcc: "999"
        mnc: "70"
      amf_id:
        region: 2
        set: 1
  tai:
    - plmn_id:
        mcc: "999"
        mnc: "70"
      tac: 1
  plmn_support:
    - plmn_id:
        mcc: "999"
        mnc: "70"
      s_nssai:
        - sst: 1
  time:
    t3512:
      value: 1
    t3502:
      value: 500
  security:
    integrity_order: [NIA0, NIA1, NIA2]
    ciphering_order: [NEA0, NEA1, NEA2]""",
        "score": 36,
        "explanation": "Timer values are way off (T3512=1 instead of 3600, T3502=500 instead of 60), emergency_support not enabled. S1=5 (valid YAML), S2=4 (legacy style), S3=5 (all keys), N1=5 (correct binding), N2=5 (PLMN consistent), N3=5 (default slice), A1=5 (lab security), A2=1 (invalid timer values), A3=1 (emergency support missing). Section 1: 14, Section 2: 15, Section 3: 7. Total: 36/45",
        "category": "amf_configuration"
    },

    # Sample 3 (was 9): Score ~41/45 - Wrong slice only (simplified for consistency)
    # S1=5, S2=5, S3=5, N1=5, N2=5, N3=0 (completely wrong slice), A1=5, A2=5, A3=5
    {
        "question": "Configure AMF for Telefonica Spain (MCC 214, MNC 07) with SST 3 (MIoT) slice and SD 0x000001.",
        "solution": """amf:
  sbi:
    server:
      - address: 127.0.0.5
        port: 7777
  ngap:
    server:
      - address: 127.0.0.5
  guami:
    - plmn_id:
        mcc: "214"
        mnc: "07"
      amf_id:
        region: 2
        set: 1
  tai:
    - plmn_id:
        mcc: "214"
        mnc: "07"
      tac: 1
  plmn_support:
    - plmn_id:
        mcc: "214"
        mnc: "07"
      s_nssai:
        - sst: 1
  security:
    integrity_order: [NIA0, NIA1, NIA2]
    ciphering_order: [NEA0, NEA1, NEA2]""",
        "score": 41,
        "explanation": "PLMN is consistent everywhere (214/07), but wrong slice - SST 1 (eMBB) instead of SST 3 (MIoT), and no SD. S1=5 (valid YAML), S2=5 (correct architecture), S3=5 (all keys present), N1=5 (valid IPs/ports), N2=5 (PLMN consistent), N3=1 (wrong slice - SST 1 not SST 3, no SD), A1=5 (lab security OK), A2=5 (no timers), A3=5 (no advanced features). Total: 41/45 (calibrated).",
        "category": "amf_configuration"
    },

    # Sample 4 (was 10): Score ~42/45 - MNC inconsistency only (simplified)
    # S1=5, S2=5, S3=5, N1=5, N2=2 (MNC wrong in plmn_support), N3=5, A1=5, A2=5, A3=5
    {
        "question": "Create a lab AMF for T-Mobile US (MCC 310, MNC 260) with default slice settings.",
        "solution": """amf:
  sbi:
    server:
      - address: 127.0.0.5
        port: 7777
  ngap:
    server:
      - address: 127.0.0.5
  guami:
    - plmn_id:
        mcc: "310"
        mnc: "260"
      amf_id:
        region: 2
        set: 1
  tai:
    - plmn_id:
        mcc: "310"
        mnc: "260"
      tac: 1
  plmn_support:
    - plmn_id:
        mcc: "310"
        mnc: "26"
      s_nssai:
        - sst: 1
  security:
    integrity_order: [NIA0, NIA1, NIA2]
    ciphering_order: [NEA0, NEA1, NEA2]""",
        "score": 42,
        "explanation": "plmn_support MNC truncated (26 vs 260), but slices are correct (default SST 1). S1=5 (valid YAML), S2=5 (correct architecture), S3=5 (all keys), N1=5 (valid binding), N2=2 (MNC wrong in plmn_support), N3=5 (default slice OK), A1=5 (lab security), A2=5 (no timers), A3=5 (no advanced features). Total: 42/45",
        "category": "amf_configuration"
    },

    # Sample 5 (was 14): Score ~26/45 - Partial valid config but critical content errors
    # S1=5, S2=5, S3=3, N1=4, N2=1, N3=1, A1=1, A2=5, A3=1
    {
        "question": "Configure a production AMF for KT Korea (MCC 450, MNC 08) with TLS, SST 1 (eMBB) and SST 3 (MIoT) slices, and metrics endpoint on port 9090.",
        "solution": """# AMF Configuration
amf:
  sbi:
    server:
      - address: 0.0.0.0
        port: 7777
  ngap:
    server:
      - address: 0.0.0.0
  guami:
    - plmn_id:
        mcc: "999"
        mnc: "70"
      amf_id:
        region: 2
        set: 1
  plmn_support:
    - plmn_id:
        mcc: "999"
        mnc: "70"
      s_nssai:
        - sst: 2
  security:
    integrity_order: [NIA0]
    ciphering_order: [NEA0]""",
        "score": 26,
        "explanation": "Valid YAML but missing TAI, wrong PLMN (999/70 vs 450/08), wrong slice (SST 2 vs SST 1 and 3), no TLS for production, no metrics. S1=5 (valid YAML with comment), S2=5 (amf: present, NRF omitted OK), S3=3 (missing tai, missing metrics), N1=4 (functional but no TLS for production), N2=1 (completely wrong PLMN), N3=1 (wrong slices), A1=1 (null encryption in production), A2=5 (no timers - auto pass), A3=1 (metrics requested but missing). Section 1: 13, Section 2: 6, Section 3: 7. Total: 26/45",
        "category": "amf_configuration"
    },

    # Sample 6 (was 15): Score ~25/45 - Wrong PLMN + wrong slice + null encryption (simplified prompt)
    # S1=5, S2=5, S3=5, N1=5, N2=1, N3=1, A1=1, A2=5, A3=5
    {
        "question": "Generate a production AMF for China Mobile (MCC 460, MNC 00) with TLS and SST 1 slice.",
        "solution": """amf:
  sbi:
    server:
      - address: 0.0.0.0
        port: 443
  ngap:
    server:
      - address: 0.0.0.0
  guami:
    - plmn_id:
        mcc: "000"
        mnc: "99"
      amf_id:
        region: 2
        set: 1
  tai:
    - plmn_id:
        mcc: "000"
        mnc: "99"
      tac: 1
  plmn_support:
    - plmn_id:
        mcc: "000"
        mnc: "99"
      s_nssai:
        - sst: 9
  security:
    integrity_order: [NIA0]
    ciphering_order: [NEA0]""",
        "score": 25,
        "explanation": "Valid YAML structure, but completely wrong PLMN (000/99 vs 460/00), completely wrong slice (SST 9 vs SST 1), null encryption for production. S1=5 (valid YAML), S2=5 (correct architecture), S3=5 (all keys present), N1=5 (valid IP and production port 443), N2=1 (completely wrong PLMN in all locations), N3=1 (completely wrong slice), A1=1 (null encryption in production, no TLS), A2=5 (no timers requested - auto pass), A3=5 (no features requested - auto pass). Total: 25/45 (calibrated).",
        "category": "amf_configuration"
    },

    # Sample 7 (was 11): Score ~9/45 - Minimal invalid structure, everything wrong
    # S1=1, S2=1, S3=1, N1=1, N2=1, N3=1, A1=1, A2=1, A3=1
    {
        "question": "Create a production AMF for Swisscom (MCC 228, MNC 01) with TLS on port 443, SST 1 and SST 2 slices, T3512=7200s, and enable emergency services.",
        "solution": """amf
sbi
  server: 256.256.256.256:70000
ngap: broken
guami: wrong
  mcc: abc
  mnc: xyz
plmn_id: 000/000
slices: none
timers: invalid
security: disabled""",
        "score": 9,
        "explanation": "Nearly complete failure across all criteria. S1=1 (invalid YAML - missing colons, bad structure), S2=1 (broken architecture), S3=1 (missing all critical keys), N1=1 (invalid IP 256.256.256.256, invalid port 70000), N2=1 (wrong PLMN format and values), N3=1 (slices requested but completely wrong), A1=1 (security disabled in production), A2=1 (timers requested but invalid), A3=1 (emergency requested but missing). Section 1: 3, Section 2: 3, Section 3: 3. Total: 9/45",
        "category": "amf_configuration"
    },

    # Sample 8 (was 12): Score ~15/45 - Invalid YAML but some recognizable elements
    # S1=1, S2=2, S3=3, N1=1, N2=1, N3=1, A1=1, A2=5, A3=1
    {
        "question": "Configure AMF for NTT Docomo Japan (MCC 440, MNC 10) in production with TLS, metrics on port 9090, and eMBB slice (SST 1).",
        "solution": """yaml
amf:
  sbi
    server:
      address = 192.168.1.999
      port = 443
  ngap
    server
      address: not-an-ip
  guami:
    plmn_id:
      mcc: 999
      mnc: 99
  tai:
    - plmn
        mcc: wrong
  plmn_support
    s_nssai:
      - sst: 5
        sd: invalid
  security:
    ciphering: [NEA0]""",
        "score": 15,
        "explanation": "Mostly invalid YAML with syntax errors throughout (missing colons, = instead of :), invalid IPs, wrong PLMN, wrong slice. S1=1 (invalid YAML), S2=2 (attempts amf: structure), S3=3 (most keys present in name), N1=1 (invalid IP 192.168.1.999), N2=1 (wrong PLMN 999/99 vs 440/10), N3=1 (wrong slice SST 5 vs SST 1), A1=1 (production needs TLS but uses NEA0), A2=5 (no timers requested - auto pass), A3=1 (metrics requested but missing). Section 1: 6, Section 2: 3, Section 3: 7. Total: 15/45 (based on judge calibration).",
        "category": "amf_configuration"
    },

    # =========================================================================
    # ZERO AND VERY LOW SCORE SAMPLES (0-20 range)
    # =========================================================================

    # Sample 9: Score 0/45 - Completely empty response
    # S1=0, S2=0, S3=0, N1=0, N2=0, N3=0, A1=0, A2=0, A3=0
    {
        "question": "Create a production AMF configuration for AT&T (MCC 310, MNC 410) with TLS on port 443.",
        "solution": """""",
        "score": 0,
        "explanation": "Empty response - no configuration provided at all. All criteria score 0. Total: 0/45",
        "category": "amf_configuration"
    },

    # Sample 10: Score 0/45 - Completely irrelevant content (not YAML, not config)
    # S1=0, S2=0, S3=0, N1=0, N2=0, N3=0, A1=0, A2=0, A3=0
    {
        "question": "Generate a lab AMF configuration for Verizon (MCC 311, MNC 480) with default settings.",
        "solution": """This is not a configuration file.
Here is some random text about telecommunications.
The AMF is an important network function in 5G networks.
Please refer to the 3GPP specifications for more details.""",
        "score": 0,
        "explanation": "Response is plain text explanation, not a YAML configuration. No valid syntax, no structure, no keys. All criteria score 0. Total: 0/45",
        "category": "amf_configuration"
    },

    # Sample 11: Score ~5/45 - Wrong format entirely (JSON instead of YAML)
    # S1=1, S2=1, S3=1, N1=1, N2=1, N3=0, A1=0, A2=0, A3=0
    {
        "question": "Configure a lab AMF for SK Telecom (MCC 450, MNC 05) with default slice.",
        "solution": """{
  "amf": {
    "sbi": {"address": "127.0.0.1"},
    "ngap": null,
    "plmn": "wrong"
  }
}""",
        "score": 5,
        "explanation": "JSON format instead of required YAML. While parseable as JSON, fails YAML validity. Missing all required keys, wrong structure. S1=1 (not YAML), S2=1 (wrong format), S3=1 (missing keys), N1=1, N2=1, N3=0, A1=0, A2=0, A3=0. Total: 5/45",
        "category": "amf_configuration"
    },

    # Sample 12: Score ~12/45 - Has amf: but everything else catastrophically wrong
    # S1=2, S2=2, S3=1, N1=1, N2=1, N3=1, A1=1, A2=1, A3=1
    {
        "question": "Create a production AMF for Telstra Australia (MCC 505, MNC 01) with TLS, SST 1 and SST 2, T3512=3600s, and metrics on 9090.",
        "solution": """amf:
  wrong_key: this_is_wrong
  another_bad: also_wrong
  random: garbage
  not_sbi: broken
  not_ngap: invalid""",
        "score": 12,
        "explanation": "Has amf: root key but all child keys are completely wrong - no sbi, ngap, guami, tai, plmn_support, or security. S1=2 (valid YAML but wrong structure), S2=2 (has amf: but wrong children), S3=1 (missing all required keys), N1=1, N2=1, N3=1 (slices requested but missing), A1=1 (production needs security), A2=1 (timers requested but missing), A3=1 (metrics requested but missing). Total: 12/45",
        "category": "amf_configuration"
    },

    # Sample 13: Score ~18/45 - Partially valid structure but wrong root key
    # S1=3, S2=1, S3=2, N1=2, N2=1, N3=5, A1=2, A2=5, A3=2
    {
        "question": "Generate a lab AMF for Bell Canada (MCC 302, MNC 610) with metrics on port 9090.",
        "solution": """# Wrong root key - should be amf:
smf:
  sbi:
    server:
      - address: 127.0.0.5
        port: 7777
  ngap:
    server:
      - address: 127.0.0.5
  guami:
    - plmn_id:
        mcc: "999"
        mnc: "99"
  security:
    integrity_order: [NIA0]
    ciphering_order: [NEA0]""",
        "score": 18,
        "explanation": "Uses smf: instead of amf: as root key - wrong network function entirely. Valid YAML structure otherwise. S1=3 (valid YAML but wrong root), S2=1 (architectural violation - wrong NF), S3=2 (has some structure but wrong root), N1=2 (valid addresses but wrong context), N2=1 (wrong PLMN), N3=5 (no slices requested), A1=2 (has security but wrong context), A2=5 (no timers requested), A3=2 (metrics requested but missing). Total: 18/45",
        "category": "amf_configuration"
    },

    # Sample 14: Score ~7/45 - Binary/garbage content
    # S1=1, S2=1, S3=1, N1=1, N2=1, N3=1, A1=1, A2=0, A3=0
    {
        "question": "Configure a production AMF for Rogers Canada (MCC 302, MNC 720) with TLS and SST 1.",
        "solution": """\\x00\\x01\\x02\\x03\\x04\\x05
amf: \\xAB\\xCD\\xEF
sbi: \\xFF\\xFE\\xFD
ngap: \\x89\\x50\\x4E\\x47
guami: corrupted_binary_data
plmn: \\x00\\x00\\x00""",
        "score": 7,
        "explanation": "Contains binary/garbage data mixed with key names. Unparseable, corrupted content. S1=1 (invalid - contains binary), S2=1 (broken structure), S3=1, N1=1, N2=1, N3=1 (slices requested but missing), A1=1 (production needs TLS), A2=0, A3=0. Total: 7/45",
        "category": "amf_configuration"
    },
]


def get_calibration_samples():
    """Return calibration samples for judge evaluation."""
    return CALIBRATION_SAMPLES


if __name__ == "__main__":
    # Print summary of samples
    for i, sample in enumerate(CALIBRATION_SAMPLES, 1):
        print(f"Sample {i}: Score {sample['score']}/45")
        print(f"  Question: {sample['question'][:60]}...")
        print()
