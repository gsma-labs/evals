from scapy.all import Packet
from scapy.fields import BitField, ByteField, IntField, ShortField


# INT Report
class INTReportFixedHeader(Packet):
    name = "INTReportFixedPacket"

    fields_desc = [
        BitField("ver", 0, 4),
        BitField("len", 0, 4),
        BitField("nproto", 0, 3),
        BitField("rep_md_bits", 0, 6),
        BitField("d", 0, 1),
        BitField("q", 0, 1),
        BitField("f", 0, 1),
        BitField("rsvd", 0, 6),
        BitField("hw_id", 0, 6),
        IntField("sw_id", None),
        IntField("seq_no", None),
        IntField("ingress_tstamp", None),
    ]


class INTShim(Packet):
    Name = "Telemetry Report Header"

    fields_desc = [
        ByteField("int_type", 0),
        ByteField("rsvd1", 0),
        ByteField("len", 0),
        BitField("dscp", 0, 6),
        BitField("rsvd2", 0, 2),
    ]


class INTMeta(Packet):
    name = "INT Metadata Header"

    fields_desc = [
        BitField("ver", 0, 4),
        BitField("rep", 0, 2),
        BitField("c", 0, 1),
        BitField("e", 0, 1),
        BitField("m", 0, 1),
        BitField("rsvd1", 0, 7),
        BitField("rsvd2", 0, 3),
        BitField("hop_metadata_len", 0, 5),
        ByteField("remaining_hop_cnt", 0),
        BitField("instruction_mask_0003", 0, 4),
        BitField("instruction_mask_0407", 0, 4),
        BitField("instruction_mask_0811", 0, 4),
        BitField("instruction_mask_1215", 0, 4),
        ShortField("rsvd3", 0),
    ]


class TelemetryReport(Packet):
    name = "INT telemetry report"

    fields_desc = [
        BitField("ver", 1, 4),
        BitField("len", 4, 4),
        BitField("nProto", 0, 3),
        BitField("repMdBits", 0, 6),
        BitField("rsvd", 0, 6),
        BitField("d", 0, 1),
        BitField("q", 0, 1),
        BitField("f", 0, 1),
        BitField("hw_id", 0, 6),
        IntField("switch_id", None),
        IntField("seq_no", None),
        IntField("ingress_tstamp", None),
    ]


# INT Metadata
class INTNodeID(Packet):
    name = "Node ID"

    fields_desc = [
        IntField("node_id", 0),
    ]


class INTLevel1InterfaceIDs(Packet):
    name = "Level 1 interface IDs"

    fields_desc = [
        ShortField("l1_ingress_interface_id", 0),
        ShortField("l1_egress_interface_id", 0),
    ]


class INTHopLatency(Packet):
    name = "Hop Latency"

    fields_desc = [
        IntField("hop_latency", 0),
    ]


class INTQueueOccupancy(Packet):
    name = "Queue Occupancy"

    fields_desc = [
        ByteField("q_id", 0),
        BitField("q_occupancy", 0, 24),
    ]


class INTIngressTstamp(Packet):
    name = "Ingress Timestamp"

    fields_desc = [
        IntField("ingress_global_timestamp", 0),
    ]


class INTEgressTstamp(Packet):
    name = "Egress Timestamp"

    fields_desc = [
        IntField("egress_global_timestamp", 0),
    ]


class INTLevel2InterfaceIDs(Packet):
    name = "Level 2 Interface Ids"

    fields_desc = [IntField("l2_ingress_interface_id", 0), IntField("l2_egress_interface_id", 0)]


class INTEgressInterfaceTxUtil(Packet):
    name = "Egress Interface TX util"

    fields_desc = [
        IntField("egress_interface_tx_util", 0),
    ]
