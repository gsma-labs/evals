from int_headers import (
    INTEgressInterfaceTxUtil,
    INTEgressTstamp,
    INTHopLatency,
    INTIngressTstamp,
    INTLevel1InterfaceIDs,
    INTLevel2InterfaceIDs,
    INTNodeID,
    INTQueueOccupancy,
)


def extract_0003_i0(b):
    return


def extract_0003_i1(b):
    data = {}
    q_occpu = INTQueueOccupancy(b[0:4])
    q_occpu.show()
    data["q_id"] = q_occpu.q_id
    data["q_occupancy"] = q_occpu.q_occupancy
    return data


def extract_0003_i2(b):
    data = {}
    hop_l = INTHopLatency(b[0:4])
    data["hop_latency"] = hop_l.hop_latency
    hop_l.show()
    return data


def extract_0003_i3(b):
    data = {}
    hop_l = INTHopLatency(b[0:4])
    data["hop_latency"] = hop_l.hop_latency
    hop_l.show()

    q_occpu = INTQueueOccupancy(b[4:8])
    q_occpu.show()
    data["q_id"] = q_occpu.q_id
    data["q_occupancy"] = q_occpu.q_occupancy
    return data


def extract_0003_i4(b):
    data = {}
    l1_intf_ids = INTLevel1InterfaceIDs(b[0:4])
    data["l1_ingress_interface_id"] = l1_intf_ids.l1_ingress_interface_id
    data["l1_egress_interface_id"] = l1_intf_ids.l1_egress_interface_id
    l1_intf_ids.show()
    return data


def extract_0003_i5(b):
    data = {}
    l1_intf_ids = INTLevel1InterfaceIDs(b[0:4])
    data["l1_ingress_interface_id"] = l1_intf_ids.l1_ingress_interface_id
    data["l1_egress_interface_id"] = l1_intf_ids.l1_egress_interface_id
    l1_intf_ids.show()

    q_occpu = INTQueueOccupancy(b[4:8])
    q_occpu.show()
    data["q_id"] = q_occpu.q_id
    data["q_occupancy"] = q_occpu.q_occupancy
    return data


def extract_0003_i6(b):
    data = {}
    l1_intf_ids = INTLevel1InterfaceIDs(b[0:4])
    data["l1_ingress_interface_id"] = l1_intf_ids.l1_ingress_interface_id
    data["l1_egress_interface_id"] = l1_intf_ids.l1_egress_interface_id
    l1_intf_ids.show()

    hop_l = INTHopLatency(b[4:8])
    data["hop_latency"] = hop_l.hop_latency
    hop_l.show()
    return data


def extract_0003_i7(b):
    data = {}
    l1_intf_ids = INTLevel1InterfaceIDs(b[0:4])
    data["l1_ingress_interface_id"] = l1_intf_ids.l1_ingress_interface_id
    data["l1_egress_interface_id"] = l1_intf_ids.l1_egress_interface_id
    l1_intf_ids.show()

    hop_l = INTHopLatency(b[4:8])
    data["hop_latency"] = hop_l.hop_latency
    hop_l.show()

    q_occpu = INTQueueOccupancy(b[8:12])
    q_occpu.show()
    data["q_id"] = q_occpu.q_id
    data["q_occupancy"] = q_occpu.q_occupancy
    return data


def extract_0003_i8(b):
    data = {}
    s_id = INTNodeID(b[0:4])
    data["node_id"] = s_id.node_id
    s_id.show()
    return data


def extract_0003_i9(b):
    data = {}
    s_id = INTNodeID(b[0:4])
    data["node_id"] = s_id.node_id
    s_id.show()

    q_occpu = INTQueueOccupancy(b[4:8])
    q_occpu.show()
    data["q_id"] = q_occpu.q_id
    data["q_occupancy"] = q_occpu.q_occupancy
    return data


def extract_0003_i10(b):
    data = {}
    s_id = INTNodeID(b[0:4])
    data["node_id"] = s_id.node_id
    s_id.show()

    hop_l = INTHopLatency(b[4:8])
    data["hop_latency"] = hop_l.hop_latency
    hop_l.show()
    return data


def extract_0003_i11(b):
    data = {}
    s_id = INTNodeID(b[0:4])
    data["node_id"] = s_id.node_id
    s_id.show()

    hop_l = INTHopLatency(b[4:8])
    data["hop_latency"] = hop_l.hop_latency
    hop_l.show()

    q_occpu = INTQueueOccupancy(b[8:12])
    q_occpu.show()
    data["q_id"] = q_occpu.q_id
    data["q_occupancy"] = q_occpu.q_occupancy
    return data


def extract_0003_i12(b):
    data = {}
    s_id = INTNodeID(b[0:4])
    data["node_id"] = s_id.node_id
    s_id.show()

    l1_intf_ids = INTLevel1InterfaceIDs(b[4:8])
    data["l1_ingress_interface_id"] = l1_intf_ids.l1_ingress_interface_id
    data["l1_egress_interface_id"] = l1_intf_ids.l1_egress_interface_id
    l1_intf_ids.show()
    return data


def extract_0003_i13(b):
    data = {}
    s_id = INTNodeID(b[0:4])
    data["node_id"] = s_id.node_id
    s_id.show()

    l1_intf_ids = INTLevel1InterfaceIDs(b[4:8])
    data["l1_ingress_interface_id"] = l1_intf_ids.l1_ingress_interface_id
    data["l1_egress_interface_id"] = l1_intf_ids.l1_egress_interface_id
    l1_intf_ids.show()

    q_occpu = INTQueueOccupancy(b[8:12])
    q_occpu.show()
    data["q_id"] = q_occpu.q_id
    data["q_occupancy"] = q_occpu.q_occupancy
    return data


def extract_0003_i14(b):
    data = {}
    s_id = INTNodeID(b[0:4])
    data["node_id"] = s_id.node_id
    s_id.show()

    l1_intf_ids = INTLevel1InterfaceIDs(b[4:8])
    data["l1_ingress_interface_id"] = l1_intf_ids.l1_ingress_interface_id
    data["l1_egress_interface_id"] = l1_intf_ids.l1_egress_interface_id
    l1_intf_ids.show()

    hop_l = INTHopLatency(b[8:12])
    data["hop_latency"] = hop_l.hop_latency
    hop_l.show()
    return data


def extract_0003_i15(b):
    data = {}
    s_id = INTNodeID(b[0:4])
    data["node_id"] = s_id.node_id
    s_id.show()

    l1_intf_ids = INTLevel1InterfaceIDs(b[4:8])
    data["l1_ingress_interface_id"] = l1_intf_ids.l1_ingress_interface_id
    data["l1_egress_interface_id"] = l1_intf_ids.l1_egress_interface_id
    l1_intf_ids.show()

    hop_l = INTHopLatency(b[8:12])
    data["hop_latency"] = hop_l.hop_latency
    hop_l.show()

    q_occpu = INTQueueOccupancy(b[12:16])
    q_occpu.show()
    data["q_id"] = q_occpu.q_id
    data["q_occupancy"] = q_occpu.q_occupancy
    return data


# handle instruction bit 4-7
def extract_0407_i0():
    return


def extract_0407_i1(b):
    data = {}
    egress_intf_tx_util = INTEgressInterfaceTxUtil(b[0:4])
    egress_intf_tx_util.show()
    data["egress_interface_tx_util"] = egress_intf_tx_util.egress_interface_tx_util
    return data


def extract_0407_i2(b):
    data = {}
    l2_intf_ids = INTLevel2InterfaceIDs(b[0:8])
    l2_intf_ids.show()
    data["l2_ingress_interface_id"] = l2_intf_ids.l2_ingress_interface_id
    data["l2_egress_interface_id"] = l2_intf_ids.l2_egress_interface_id
    return data


def extract_0407_i3(b):
    data = {}
    l2_intf_ids = INTLevel2InterfaceIDs(b[0:8])
    l2_intf_ids.show()
    data["l2_ingress_interface_id"] = l2_intf_ids.l2_ingress_interface_id
    data["l2_egress_interface_id"] = l2_intf_ids.l2_egress_interface_id

    egress_intf_tx_util = INTEgressInterfaceTxUtil(b[8:12])
    egress_intf_tx_util.show()
    data["egress_interface_tx_util"] = egress_intf_tx_util.egress_interface_tx_util
    return data


def extract_0407_i4(b):
    data = {}
    egress_t_stamp = INTEgressTstamp(b[0:4])
    egress_t_stamp.show()
    data["egress_global_timestamp"] = egress_t_stamp.egress_global_timestamp
    return data


def extract_0407_i5(b):
    data = {}
    egress_t_stamp = INTEgressTstamp(b[0:4])
    egress_t_stamp.show()
    data["egress_global_timestamp"] = egress_t_stamp.egress_global_timestamp

    egress_intf_tx_util = INTEgressInterfaceTxUtil(b[4:8])
    egress_intf_tx_util.show()
    data["egress_interface_tx_util"] = egress_intf_tx_util.egress_interface_tx_util
    return data


def extract_0407_i6(b):
    data = {}
    egress_t_stamp = INTEgressTstamp(b[0:4])
    egress_t_stamp.show()
    data["egress_global_timestamp"] = egress_t_stamp.egress_global_timestamp

    l2_intf_ids = INTLevel2InterfaceIDs(b[4:12])
    l2_intf_ids.show()
    data["l2_ingress_interface_id"] = l2_intf_ids.l2_ingress_interface_id
    data["l2_egress_interface_id"] = l2_intf_ids.l2_egress_interface_id
    return data


def extract_0407_i7(b):
    data = {}
    egress_t_stamp = INTEgressTstamp(b[0:4])
    egress_t_stamp.show()
    data["egress_global_timestamp"] = egress_t_stamp.egress_global_timestamp

    l2_intf_ids = INTLevel2InterfaceIDs(b[4:12])
    l2_intf_ids.show()
    data["l2_ingress_interface_id"] = l2_intf_ids.l2_ingress_interface_id
    data["l2_egress_interface_id"] = l2_intf_ids.l2_egress_interface_id

    egress_intf_tx_util = INTEgressInterfaceTxUtil(b[12:16])
    egress_intf_tx_util.show()
    data["egress_interface_tx_util"] = egress_intf_tx_util.egress_interface_tx_util
    return data


def extract_0407_i8(b):
    data = {}
    ingress_t_stamp = INTIngressTstamp(b[0:4])
    ingress_t_stamp.show()
    data["ingress_global_timestamp"] = ingress_t_stamp.ingress_global_timestamp
    return data


def extract_0407_i9(b):
    data = {}
    ingress_t_stamp = INTIngressTstamp(b[0:4])
    ingress_t_stamp.show()
    data["ingress_global_timestamp"] = ingress_t_stamp.ingress_global_timestamp

    egress_intf_tx_util = INTEgressInterfaceTxUtil(b[4:8])
    egress_intf_tx_util.show()
    data["egress_interface_tx_util"] = egress_intf_tx_util.egress_interface_tx_util
    return data


def extract_0407_i10(b):
    data = {}
    ingress_t_stamp = INTIngressTstamp(b[0:4])
    ingress_t_stamp.show()
    data["ingress_global_timestamp"] = ingress_t_stamp.ingress_global_timestamp

    l2_intf_ids = INTLevel2InterfaceIDs(b[4:12])
    l2_intf_ids.show()
    data["l2_ingress_interface_id"] = l2_intf_ids.l2_ingress_interface_id
    data["l2_egress_interface_id"] = l2_intf_ids.l2_egress_interface_id
    return data


def extract_0407_i11(b):
    data = {}
    ingress_t_stamp = INTIngressTstamp(b[0:4])
    ingress_t_stamp.show()
    data["ingress_global_timestamp"] = ingress_t_stamp.ingress_global_timestamp

    l2_intf_ids = INTLevel2InterfaceIDs(b[4:12])
    l2_intf_ids.show()
    data["l2_ingress_interface_id"] = l2_intf_ids.l2_ingress_interface_id
    data["l2_egress_interface_id"] = l2_intf_ids.l2_egress_interface_id

    egress_intf_tx_util = INTEgressInterfaceTxUtil(b[12:16])
    egress_intf_tx_util.show()
    data["egress_interface_tx_util"] = egress_intf_tx_util.egress_interface_tx_util
    return data


def extract_0407_i12(b):
    data = {}
    ingress_t_stamp = INTIngressTstamp(b[0:4])
    ingress_t_stamp.show()
    data["ingress_global_timestamp"] = ingress_t_stamp.ingress_global_timestamp

    egress_t_stamp = INTEgressTstamp(b[4:8])
    egress_t_stamp.show()
    data["egress_global_timestamp"] = egress_t_stamp.egress_global_timestamp
    return data


def extract_0407_i13(b):
    data = {}
    ingress_t_stamp = INTIngressTstamp(b[0:4])
    ingress_t_stamp.show()
    data["ingress_global_timestamp"] = ingress_t_stamp.ingress_global_timestamp

    egress_t_stamp = INTEgressTstamp(b[4:8])
    egress_t_stamp.show()
    data["egress_global_timestamp"] = egress_t_stamp.egress_global_timestamp

    egress_intf_tx_util = INTEgressInterfaceTxUtil(b[8:12])
    egress_intf_tx_util.show()
    data["egress_interface_tx_util"] = egress_intf_tx_util.egress_interface_tx_util
    return data


def extract_0407_i14(b):
    data = {}
    ingress_t_stamp = INTIngressTstamp(b[0:4])
    ingress_t_stamp.show()
    data["ingress_global_timestamp"] = ingress_t_stamp.ingress_global_timestamp

    egress_t_stamp = INTEgressTstamp(b[4:8])
    egress_t_stamp.show()
    data["egress_global_timestamp"] = egress_t_stamp.egress_global_timestamp

    l2_intf_ids = INTLevel2InterfaceIDs(b[8:16])
    l2_intf_ids.show()
    data["l2_ingress_interface_id"] = l2_intf_ids.l2_ingress_interface_id
    data["l2_egress_interface_id"] = l2_intf_ids.l2_egress_interface_id
    return data


def extract_0407_i15(b):
    data = {}
    ingress_t_stamp = INTIngressTstamp(b[0:4])
    ingress_t_stamp.show()
    data["ingress_global_timestamp"] = ingress_t_stamp.ingress_global_timestamp

    egress_t_stamp = INTEgressTstamp(b[4:8])
    egress_t_stamp.show()
    data["egress_global_timestamp"] = egress_t_stamp.egress_global_timestamp

    l2_intf_ids = INTLevel2InterfaceIDs(b[8:16])
    l2_intf_ids.show()
    data["l2_ingress_interface_id"] = l2_intf_ids.l2_ingress_interface_id
    data["l2_egress_interface_id"] = l2_intf_ids.l2_egress_interface_id

    egress_intf_tx_util = INTEgressInterfaceTxUtil(b[16:20])
    egress_intf_tx_util.show()
    data["egress_interface_tx_util"] = egress_intf_tx_util.egress_interface_tx_util
    return data


def extract_ins_00_03(instruction, b):
    if instruction == 0:
        return extract_0003_i0(b)
    elif instruction == 1:
        return extract_0003_i1(b)
    elif instruction == 2:
        return extract_0003_i2(b)
    elif instruction == 3:
        return extract_0003_i3(b)
    elif instruction == 4:
        return extract_0003_i4(b)
    elif instruction == 5:
        return extract_0003_i5(b)
    elif instruction == 6:
        return extract_0003_i6(b)
    elif instruction == 7:
        return extract_0003_i7(b)
    elif instruction == 8:
        return extract_0003_i8(b)
    elif instruction == 9:
        return extract_0003_i9(b)
    elif instruction == 10:
        return extract_0003_i10(b)
    elif instruction == 11:
        return extract_0003_i11(b)
    elif instruction == 12:
        return extract_0003_i12(b)
    elif instruction == 13:
        return extract_0003_i13(b)
    elif instruction == 14:
        return extract_0003_i14(b)
    elif instruction == 15:
        return extract_0003_i15(b)


def extract_ins_04_07(instruction, b):
    if instruction == 0:
        return extract_0407_i0(b)
    elif instruction == 1:
        return extract_0407_i1(b)
    elif instruction == 2:
        return extract_0407_i2(b)
    elif instruction == 3:
        return extract_0407_i3(b)
    elif instruction == 4:
        return extract_0407_i4(b)
    elif instruction == 5:
        return extract_0407_i5(b)
    elif instruction == 6:
        return extract_0407_i6(b)
    elif instruction == 7:
        return extract_0407_i7(b)
    elif instruction == 8:
        return extract_0407_i8(b)
    elif instruction == 9:
        return extract_0407_i9(b)
    elif instruction == 10:
        return extract_0407_i10(b)
    elif instruction == 11:
        return extract_0407_i11(b)
    elif instruction == 12:
        return extract_0407_i12(b)
    elif instruction == 13:
        return extract_0407_i13(b)
    elif instruction == 14:
        return extract_0407_i14(b)
    elif instruction == 15:
        return extract_0407_i15(b)
    return


# def extract_metadata_stack(b, total_data_len, hop_m_len, instruction_mask_0003, instruction_mask_0407, info):
#     num_hops = int(total_data_len / hop_m_len)
#     info["instruction_mask_0003"] = instruction_mask_0003
#     info["instruction_mask_0407"] = instruction_mask_0407
#     info["data"] = {}
#     print("##[ INT Metadata Stack ]##")
#     count_table_0003 = [i * 4 for i in [0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4]]
#     i = 0
#     for hop in range(num_hops, 0, -1):
#         print("##[ Data from hop " + str(hop) + " ]##")
#         info["data"]["hop_" + str(hop)] = {}
#
#         # calculate the bytes offset
#         offset_start_0003 = i * hop_m_len
#         offset_end_0003 = offset_start_0003 + count_table_0003[instruction_mask_0003]
#         offset_end_0407 = offset_start_0003 + hop_m_len
#
#         if instruction_mask_0003 != 0:
#             data_0003 = extract_ins_00_03(instruction_mask_0003, b[offset_start_0003:offset_end_0003])
#             info["data"]["hop_" + str(hop)] = data_0003
#         if instruction_mask_0407 != 0:
#             data_0407 = extract_ins_04_07(instruction_mask_0407, b[offset_end_0003:offset_end_0407])
#             info["data"]["hop_" + str(hop)].update(data_0407)
#         i += 1
#     return info
