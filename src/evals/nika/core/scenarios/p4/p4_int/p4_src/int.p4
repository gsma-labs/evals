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
#include <core.p4>
#include <v1model.p4>

#include "p4_include/defines.p4"
#include "p4_include/headers.p4"
#include "p4_include/int_definitions.p4"
#include "p4_include/int_headers.p4"
#include "p4_include/checksums.p4"
#include "p4_include/int_parser.p4"
#include "p4_include/int_source.p4"
#include "p4_include/int_transit.p4"
#include "p4_include/int_sink.p4"
#include "p4_include/int_report.p4"
#include "p4_include/dmac_forward.p4"

#define TARGET_BMV2

control ingress (
    inout headers_t hdr,
    inout local_metadata_t local_metadata,
    inout standard_metadata_t standard_metadata) {

    apply {
        dmac_forward_control.apply(hdr, local_metadata, standard_metadata);
        process_int_source_sink.apply(hdr, local_metadata, standard_metadata);
    

        if (local_metadata.int_meta.source == _TRUE) {
            process_int_source.apply(hdr, local_metadata, standard_metadata);
        }

        if (local_metadata.int_meta.sink == _TRUE && hdr.int_header.isValid()) {
            // clone packet for Telemetry Report
            // FIXME: this works only on BMv2
            #ifdef TARGET_BMV2
            clone_preserving_field_list(CloneType.I2E, REPORT_MIRROR_SESSION_ID, PreservedFieldList.Field);
            #endif // TARGET_BMV2
        }
    }
}

control egress (
    inout headers_t hdr,
    inout local_metadata_t local_metadata,
    inout standard_metadata_t standard_metadata) {

    apply {
        if(hdr.int_header.isValid()) {
            process_int_transit.apply(hdr, local_metadata, standard_metadata);

            if (IS_I2E_CLONE(standard_metadata)) {
                /* send int report */
                process_int_report.apply(hdr, local_metadata, standard_metadata);
            }

            if (local_metadata.int_meta.sink == _TRUE && !IS_I2E_CLONE(standard_metadata)) {
                process_int_sink.apply(hdr, local_metadata, standard_metadata);
             }
        }
    }
}

V1Switch(
    int_parser(),
    verify_checksum_control(),
    ingress(),
    egress(),
    compute_checksum_control(),
    int_deparser()
) main;
