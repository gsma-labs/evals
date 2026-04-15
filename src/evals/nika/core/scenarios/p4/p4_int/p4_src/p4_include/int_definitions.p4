/*
 * Copyright 2017-present Open Networking Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/* -*- P4_16 -*- */
#ifndef __INT_DEFINE__
#define __INT_DEFINE__

#include "defines.p4"

#define TARGET_BMV2

/* indicate INT by TOS value */
const bit<8> TOS_INT = 0x66; // 0x66: 01100110
const bit<8> TOS_MASK = 0xFF; // 0xFF: 11111111

typedef bit<48> timestamp_t;
typedef bit<32> switch_id_t;

const bit<8> INT_HEADER_LEN_WORD = 3;
const bit<16> INT_HEADER_SIZE = 8;
const bit<16> INT_SHIM_HEADER_SIZE = 4;

const bit<8> CPU_MIRROR_SESSION_ID = 250;
const bit<32> REPORT_MIRROR_SESSION_ID = 500;
const bit<6> HW_ID = 1;
const bit<8> REPORT_HDR_TTL = 64;

#ifdef TARGET_BMV2
// These definitions are from:
// https://github.com/jafingerhut/p4-guide/blob/master/v1model-special-ops/v1model-special-ops.p4

// These definitions are derived from the numerical values of the enum
// named "PktInstanceType" in the p4lang/behavioral-model source file
// targets/simple_switch/simple_switch.h
// https://github.com/p4lang/behavioral-model/blob/master/targets/simple_switch/simple_switch.h#L126-L134

//  Cloned packets can be distinguished from others by the value of the
//  standard_metadata instance_type field.

const bit<32> BMV2_V1MODEL_INSTANCE_TYPE_NORMAL        = 0;
const bit<32> BMV2_V1MODEL_INSTANCE_TYPE_INGRESS_CLONE = 1;
const bit<32> BMV2_V1MODEL_INSTANCE_TYPE_EGRESS_CLONE  = 2;
const bit<32> BMV2_V1MODEL_INSTANCE_TYPE_COALESCED     = 3;
const bit<32> BMV2_V1MODEL_INSTANCE_TYPE_RECIRC        = 4;
const bit<32> BMV2_V1MODEL_INSTANCE_TYPE_REPLICATION   = 5;
const bit<32> BMV2_V1MODEL_INSTANCE_TYPE_RESUBMIT      = 6;

#define IS_NORMAL(smeta) (smeta.instance_type == BMV2_V1MODEL_INSTANCE_TYPE_NORMAL)
#define IS_RESUBMITTED(smeta) (smeta.instance_type == BMV2_V1MODEL_INSTANCE_TYPE_RESUBMIT)
#define IS_RECIRCULATED(smeta) (smeta.instance_type == BMV2_V1MODEL_INSTANCE_TYPE_RECIRC)
#define IS_I2E_CLONE(smeta) (smeta.instance_type == BMV2_V1MODEL_INSTANCE_TYPE_INGRESS_CLONE)
#define IS_E2E_CLONE(smeta) (smeta.instance_type == BMV2_V1MODEL_INSTANCE_TYPE_EGRESS_CLONE)
#define IS_REPLICATED(smeta) (smeta.instance_type == BMV2_V1MODEL_INSTANCE_TYPE_REPLICATION)
#endif // TARGET__BMV2

#endif
