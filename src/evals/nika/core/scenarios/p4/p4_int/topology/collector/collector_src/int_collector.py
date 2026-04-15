import time
from datetime import datetime

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from int_defines import (
    ETHERNET_HEADER_LENGTH,
    INNER_ETHERNET_OFFSET,
    INNER_IP_HEADER_OFFSET,
    INNER_L4_HEADER_OFFSET,
    INT_META_LENGTH,
    INT_META_WORD_LENGTH,
    INT_REPORT_HEADER_LENGTH,
    INT_SHIM_LENGTH,
    INT_SHIM_OFFSET,
    INT_SHIM_WORD_LENGTH,
    IP_HEADER_LENGTH,
    OUTER_IP_HEADER,
    OUTER_L4_HEADER_OFFSET,
    UDP_HEADER_LENGTH,
    UDP_PROTO,
    INT_IPv4_DSCP,
)
from int_headers import (
    INTEgressInterfaceTxUtil,
    INTEgressTstamp,
    INTHopLatency,
    INTIngressTstamp,
    INTLevel1InterfaceIDs,
    INTLevel2InterfaceIDs,
    INTMeta,
    INTNodeID,
    INTQueueOccupancy,
    INTShim,
    TelemetryReport,
)
from scapy.all import raw, sniff
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether
from scapy.packet import Raw

token = "int_token"
org = "int_org"
bucket = "int_bucket"


class FlowKey:
    def __init__(self, src_ip="", dst_ip="", ip_proto="", src_port="", dst_port=""):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.ip_proto = ip_proto
        self.src_port = src_port
        self.dst_port = dst_port


class FlowInfo:
    def __init__(self):
        self.src_ip = ""
        self.dst_ip = ""
        self.ip_proto = ""
        self.src_port = ""
        self.dst_port = ""
        self.int_hop_num = 0
        self.flow_sink_time = ""
        self.sw_ids = []
        self.l1_in_port_ids = []
        self.l1_e_port_ids = []
        self.hop_latencies = []
        self.flow_latency = 0
        self.queue_ids = []
        self.queue_occups = []
        self.ingr_times = []
        self.egr_times = []
        self.l2_in_port_ids = []
        self.l2_e_port_ids = []
        self.tx_utilizes = []


class FlowTable:
    def __init__(self):
        # [{FlowKey: FlowInfo}]
        self.flow_table = {}

    def lookup_flow_info(self, flow_key: FlowKey):
        if self.flow_table[flow_key]:
            return self.flow_table[flow_key]
        else:
            return None


class INTCollector:
    def __init__(self, sw_name):
        self.sw_name = sw_name
        self.flow_table = FlowTable()

    def recv_msg_cpu(self, packet):
        # Skip packets without Raw layer to avoid Scapy "Layer [Raw] not found" and socket close
        if not packet.haslayer(Raw):
            return
        # packet.show()
        pkt = raw(packet)
        info = {}
        info["rec_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        # parse outer headers
        _ = Ether(pkt[0:ETHERNET_HEADER_LENGTH])
        # eth_report.show()
        _ = IP(pkt[OUTER_IP_HEADER : OUTER_IP_HEADER + IP_HEADER_LENGTH])
        # ip_report.show()
        _ = UDP(pkt[OUTER_L4_HEADER_OFFSET : OUTER_L4_HEADER_OFFSET + UDP_HEADER_LENGTH])
        # udp_report.show()

        # parse report header
        raw_payload = bytes(packet[Raw])  # to get 'raw' payload
        telemetry_report = TelemetryReport(raw_payload[0:INT_REPORT_HEADER_LENGTH])
        # telemetry_report.show()

        # parse inner headers
        _ = Ether(raw_payload[INNER_ETHERNET_OFFSET : INNER_ETHERNET_OFFSET + ETHERNET_HEADER_LENGTH])
        # inner_eth.show()
        inner_ip = IP(raw_payload[INNER_IP_HEADER_OFFSET : INNER_IP_HEADER_OFFSET + IP_HEADER_LENGTH])
        # inner_ip.show()
        # check if it's the int packets
        if inner_ip.tos != INT_IPv4_DSCP or inner_ip.proto != UDP_PROTO:
            return
        inner_udp = UDP(raw_payload[INNER_L4_HEADER_OFFSET : INNER_L4_HEADER_OFFSET + UDP_HEADER_LENGTH])
        # inner_udp.show()

        # parse int headers
        int_shim_offset = INT_SHIM_OFFSET
        int_shim_offset += UDP_HEADER_LENGTH
        int_meta_offset = int_shim_offset + INT_SHIM_LENGTH
        # print("SHIM OFFSET: "+str(int_shim_offset))
        int_shim = INTShim(raw_payload[int_shim_offset : int_shim_offset + INT_SHIM_LENGTH])
        # int_shim.show()
        int_meta = INTMeta(raw_payload[int_meta_offset : int_meta_offset + INT_META_LENGTH])
        # int_meta.show()

        # parse int metadata stack
        int_metadata_stack_offset = int_meta_offset + INT_META_LENGTH
        int_metadata_stack_length = (int_shim.len - INT_SHIM_WORD_LENGTH - INT_META_WORD_LENGTH) * 4
        stack_payload = raw_payload[int_metadata_stack_offset : int_metadata_stack_offset + int_metadata_stack_length]

        # hop_m_len：per-hop metadata length, set by the source for transit and sink
        hop_m_len = int_meta.hop_metadata_len * 4
        int_hop_num = int(int_metadata_stack_length / hop_m_len)

        flow_info = FlowInfo()
        # record basic info into flow_info
        flow_info.src_ip = inner_ip.src
        flow_info.dst_ip = inner_ip.dst
        flow_info.ip_proto = inner_ip.proto
        flow_info.src_port = inner_udp.sport
        flow_info.dst_port = inner_udp.dport
        flow_info.int_hop_num = int_hop_num
        flow_info.flow_sink_time = telemetry_report.ingress_tstamp

        # parse the instruction bitmaps
        is_l1_in_e_port_ids = bool(int_meta.instruction_mask_0003 & 0b0100)
        is_hop_latencies = bool(int_meta.instruction_mask_0003 & 0b0010)
        is_queue_occups = bool(int_meta.instruction_mask_0003 & 0b0001)
        is_ingr_times = bool(int_meta.instruction_mask_0407 & 0b1000)
        is_egr_times = bool(int_meta.instruction_mask_0407 & 0b0100)
        is_l2_in_e_port_ids = bool(int_meta.instruction_mask_0407 & 0b0010)
        is_tx_utilizes = bool(int_meta.instruction_mask_0407 & 0b0001)

        # start to parse each hop metadata stack
        for hop_index in range(0, int_hop_num):
            # cut the current hop metadata stack
            cur_offset = hop_index * hop_m_len

            # parse per-hop metadata field
            flow_info.sw_ids.append(INTNodeID(stack_payload[cur_offset : cur_offset + len(INTNodeID())]).node_id)
            cur_offset += len(INTNodeID())
            if is_l1_in_e_port_ids:
                flow_info.l1_in_port_ids.append(
                    INTLevel1InterfaceIDs(
                        stack_payload[cur_offset : cur_offset + len(INTLevel1InterfaceIDs())]
                    ).l1_ingress_interface_id
                )
                flow_info.l1_e_port_ids.append(
                    INTLevel1InterfaceIDs(
                        stack_payload[cur_offset : cur_offset + len(INTLevel1InterfaceIDs())]
                    ).l1_egress_interface_id
                )
                cur_offset += len(INTLevel1InterfaceIDs())
            if is_hop_latencies:
                flow_info.hop_latencies.append(
                    INTHopLatency(stack_payload[cur_offset : cur_offset + len(INTHopLatency())]).hop_latency
                )

                flow_info.flow_latency += INTHopLatency(
                    stack_payload[cur_offset : cur_offset + len(INTHopLatency())]
                ).hop_latency
                cur_offset += len(INTHopLatency())
            if is_queue_occups:
                flow_info.queue_ids.append(
                    INTQueueOccupancy(stack_payload[cur_offset : cur_offset + len(INTQueueOccupancy())]).q_id
                )
                flow_info.queue_occups.append(
                    INTQueueOccupancy(stack_payload[cur_offset : cur_offset + len(INTQueueOccupancy())]).q_occupancy
                )
                cur_offset += len(INTQueueOccupancy())
            if is_ingr_times:
                flow_info.ingr_times.append(
                    INTIngressTstamp(
                        stack_payload[cur_offset : cur_offset + len(INTIngressTstamp())]
                    ).ingress_global_timestamp
                )
                cur_offset += len(INTIngressTstamp())
            if is_egr_times:
                flow_info.egr_times.append(
                    INTEgressTstamp(
                        stack_payload[cur_offset : cur_offset + len(INTEgressTstamp())]
                    ).egress_global_timestamp
                )
                cur_offset += len(INTEgressTstamp())
            if is_l2_in_e_port_ids:
                flow_info.l2_in_port_ids.append(
                    INTLevel2InterfaceIDs(
                        stack_payload[cur_offset : cur_offset + len(INTLevel2InterfaceIDs())]
                    ).l2_ingress_interface_id
                )
                flow_info.l2_e_port_ids.append(
                    INTLevel2InterfaceIDs(
                        stack_payload[cur_offset : cur_offset + len(INTLevel2InterfaceIDs())]
                    ).l2_egress_interface_id
                )
                cur_offset += len(INTLevel2InterfaceIDs())
            if is_tx_utilizes:
                flow_info.tx_utilizes.append(
                    INTEgressInterfaceTxUtil(
                        stack_payload[cur_offset : cur_offset + len(INTEgressInterfaceTxUtil())]
                    ).egress_interface_tx_util
                )
                cur_offset += len(INTEgressInterfaceTxUtil())
        print("INT data: ", flow_info.__dict__)

        # record into influxdb
        with InfluxDBClient(url="http://localhost:8086", token=token, org=org) as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            # write flow latency and flow path
            if is_hop_latencies:
                path_str = ":".join(str(flow_info.sw_ids[i]) for i in reversed(range(0, int_hop_num)))
                p = (
                    Point("flow_stat")
                    .tag("src_ip", flow_info.src_ip)
                    .tag("dst_ip", flow_info.dst_ip)
                    .tag("ip_proto", flow_info.ip_proto)
                    .tag("src_port", flow_info.src_port)
                    .tag("dst_port", flow_info.dst_port)
                    .field("flow_latency", flow_info.flow_latency)
                    .field("flow_path", path_str)
                )
                # .time(flow_info.flow_sink_time)
                write_api.write(bucket=bucket, org=org, record=p)

                # write hop latency
                for i in range(0, int_hop_num):
                    p = (
                        Point("flow_hop_latency")
                        .tag("src_ip", flow_info.src_ip)
                        .tag("dst_ip", flow_info.dst_ip)
                        .tag("ip_proto", flow_info.ip_proto)
                        .tag("src_port", flow_info.src_port)
                        .tag("dst_port", flow_info.dst_port)
                        .tag("sw_id", flow_info.sw_ids[i])
                        .field("hop_latency", flow_info.hop_latencies[i])
                    )
                    # .time('%s' % flow_info.egr_times[i] if is_egr_times else '')
                    write_api.write(bucket=bucket, org=org, record=p)

            # write tx utilize
            for i in range(0, int_hop_num):
                p = (
                    Point("port_tx_utilization")
                    .tag("sw_id", flow_info.sw_ids[i])
                    .tag("egress_id", flow_info.l1_e_port_ids[i])
                    .field("tx_utilization", flow_info.tx_utilizes[i])
                )
                # .time('%s' % flow_info.egr_times[i] if is_egr_times else '')
                write_api.write(bucket=bucket, org=org, record=p)

            # write queue occupancy
            for i in range(0, int_hop_num):
                p = (
                    Point("sw_queue_occupancy")
                    .tag("sw_id", flow_info.sw_ids[i])
                    .tag("queue_id", flow_info.queue_ids[i])
                    .field("queue_occupancy", flow_info.queue_occups[i])
                )
                # .time('%s' % flow_info.egr_times[i] if is_egr_times else '')
                write_api.write(bucket=bucket, org=org, record=p)

    def run_cpu_port_loop(self):
        cpu_port_intf = "eth0"
        while True:
            try:
                sniff(iface=cpu_port_intf, prn=self.recv_msg_cpu)
            except Exception as e:
                # Socket may close on "Layer [Raw] not found" etc.; retry instead of exiting
                print(f"WARNING: sniff failed ({e}), restarting in 2s...")
                time.sleep(2)


if __name__ == "__main__":
    INTCollector("s2").run_cpu_port_loop()
