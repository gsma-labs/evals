#include <v1model.p4>

#include "headers.p4"
#include "defines.p4"


control dmac_forward_control(inout headers_t hdr,
                       inout local_metadata_t local_metadata,
                       inout standard_metadata_t standard_metadata) {

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action send_to_cpu() {
        standard_metadata.egress_spec = CPU_PORT;
    }

    action forward_to_port(bit<9> egress_port) {
        standard_metadata.egress_spec = egress_port;
    }

    table dmac_forward {
        key = {
            hdr.ethernet.src_addr: ternary;
            hdr.ethernet.dst_addr: exact;
        }
        actions = {
            forward_to_port;
            drop;
        }
        size = 4;
        default_action = drop;
    }

    apply {
        if (hdr.ipv4.isValid()) {
            dmac_forward.apply();
        }
     }

}
