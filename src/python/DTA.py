# -*- coding:utf-8 -*-
##############################################################
# Created Date: Friday, December 2nd 2022
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

import math
import numpy as np
import random
from enum import Enum

from VDF import PeriodVDF


MAX_AGENT_TYPES = 10
# because of the od demand store format, the MAX_demandtype must >= g_DEMANDTYPES.size()+1

MAX_TIME_PERIODS = 6
# time period set to 4: mid night, morning peak, mid-day and afternoon peak

MAX_ORIGIN_DISTRICTS = 30
# origin based aggregation grids

MAX_TIME_SLOT_PER_PERIOD = 300
# max 96 5-min slots per day

MAX_TIME_INTERVAL_PER_DAY = 300
# max 96*3 5-min slots per day

MIN_PER_TIME_SLOT = 5


class e_traffic_flow_model(Enum):
    POINT_QUEUE = 0
    SPATIAL_QUEUE = 1
    KINEMATIVE_WAVE = 2


class e_VDF_type(Enum):
    Q_VDF = 0
    BPR_VDF = 1


class e_assignment_mode(Enum):
    LUE = 0
    DTA = 3
    CBI = 11
    CBSA = 12


class DemandPeriod:

    def _initialize_instance_fields(self):
        # instance fields found by C++ to Python Converter:
        self.demand_period = ""
        self.starting_time_slot_no = 0
        self.ending_time_slot_no = 0
        self.time_period_in_hour = 0
        self.t2_peak_in_hour = 0
        self.time_period = ""
        self.number_of_demand_files = 0
        self.demand_period_id = 0

    def __init__(self, **kwargs):
        self._initialize_instance_fields()

        self.demand_period_id = 0
        self.demand_period = 0
        self.starting_time_slot_no = 0
        self.ending_time_slot_no = 0
        self.t2_peak_in_hour = 0
        self.time_period_in_hour = 1
        self.number_of_demand_files = 0

        if kwargs:
            for key in kwargs:
                setattr(self, key, kwargs[key])

    def get_time_horizon_in_min(self):
        return (self.ending_time_slot_no - self.starting_time_slot_no) * MIN_PER_TIMESLOT


class DepartureTimeProfile:

    def __init__(self, **kwargs):

        self.departure_time_profile_no = 0
        self.m_RandomSeed = 101
        self.starting_time_slot_no = 0
        self.ending_time_slot_no = 0
        self.departure_time_ratio = [0 for _ in range(MAX_TIME_SLOT_PER_PERIOD)]
        self.cumulative_departure_time_ratio = [0 for _ in range(MAX_TIME_SLOT_PER_PERIOD)]

        if kwargs:
            for key in kwargs:
                setattr(self, key, kwargs[key])

    def compute_cumulative_profile(self, starting_slot_no: int, ending_slot_no: int):

        total_ratio = 0.0
        for s in range(starting_slot_no + 1, ending_slot_no + 1):
            total_ratio += self.departure_time_ratio[s]

        total_ratio = max(total_ratio, 0.000001)

        self.cumulative_departure_time_ratio[starting_slot_no] = 0

        cumulative_ratio = 0
        for s in range(starting_slot_no + 1, ending_slot_no + 1):
            cumulative_ratio += self.departure_time_ratio[s] / total_ratio
            self.cumulative_departure_time_ratio[s] = cumulative_ratio

            hour = s / 12
            minute = s * 5 - hour * 60

            print(f"cumulative profile no. {self.departure_time_profile_no}, ratio at slot {s} ({hour} : {minute}) = {self.departure_time_ratio[s]}, CR {self.cumulative_departure_time_ratio[s]}")

        print(f"final cumulative profile ratio = {self.cumulative_departure_time_ratio[ending_slot_no - 1]}")

    def get_time_slot_no(self, agent_seq_no: int, agent_size: int) -> int:

        # large number of agents, then use pure uniform sequence
        # r is between 0 and 1
        r = agent_seq_no * 1.0 / agent_size if agent_size >= 10 else random.random()

        s = self.starting_time_slot_no
        while s < self.ending_time_slot_no:
            if r < self.cumulative_departure_time_ratio[s]:
                hour = s / 12
                minute = s * 5 - hour * 60
                print(f"s = {s}, ({hour} : {minute}) = {self.ending_time_slot_no}")
                return s
            s += 1

        hour = self.starting_time_slot_no / 12
        minute = self.starting_time_slot_no * 5 - hour * 60
        print(f"s = {self.starting_time_slot_no}, ({hour} : {minute}) = {self.ending_time_slot_no}")

        return self.starting_time_slot_no  # first time slot as the default value

    def get_departure_time_in_min(self, agent_seq_no: int, agent_size: int) -> float:

        isDebug = False
        # large number of agents, then use pure uniform sequence
        # r is between 0 and 1
        r = agent_seq_no * 1.0 / agent_size if agent_size >= 10 else random.random()

        s = self.starting_time_slot_no + 1
        while s <= self.ending_time_slot_no:
            hour = s / 12
            minute = int(((s * 1.0 / 12 - hour) * 60 + 0.5))

            if isDebug:
                print(f"s = {s}, ({hour} : {minute}) = {self.cumulative_departure_time_ratio[s]}")

            if r < self.cumulative_departure_time_ratio[s]:

                slot_fraction = self.cumulative_departure_time_ratio[s] - self.cumulative_departure_time_ratio[s-1]
                floating_point = max(0.0, (r - self.cumulative_departure_time_ratio[s - 1]) / max(0.00001, slot_fraction))

                time_in_min = (s - self.starting_time_slot_no + floating_point) * MIN_PER_TIME_SLOT

                if isDebug:
                    print(f"select: s={s}, ({hour} : {minute}) = {self.ending_time_slot_no}, dep_time = {time_in_min}")

                return time_in_min
            s += 1

        if isDebug:
            hour = self.starting_time_slot_no / 12
            minute = self.starting_time_slot_no * 5 - hour * 60

            print(f"s = {self.starting_time_slot_no}, ({hour} : {minute}) = {self.ending_time_slot_no}")

        # first time slot as the default value
        return (r) * MIN_PER_TIME_SLOT


class AgentTypeDistrict:

    def __init__(self, **kwargs):

        self.count_of_links = 0
        self.total_od_volume = 0
        self.total_person_distance_km = 0
        self.total_person_distance_mile = 0
        self.total_person_travel_time = 0
        self.avg_travel_time = 0
        self.avg_travel_distance_km = 0
        self.avg_travel_distance_mile = 0

        if kwargs:
            for key in kwargs:
                setattr(self, key, kwargs[key])


class AnalysisDistrict:

    def __init__(self, **kwargs):

        self.district_id = 0
        self.district_name = 0
        self.shape_points = []
        self.data_by_agent_type = [AgentTypeDistrict() for _ in range(MAX_AGENT_TYPES)]

        if kwargs:
            for key in kwargs:
                setattr(self, key, kwargs[key])

    def record_origin_2_district_volume(self, at: int, od_volume: float):
        if at >= MAX_AGENT_TYPES:
            return

        self.data_by_agent_type[at].total_od_volume += od_volume

    def record_link_2_district_data(self, element: AgentTypeDistrict, at: int):
        if at >= MAX_AGENT_TYPES:
            return

        self.data_by_agent_type[at].count_of_links += 1
        self.data_by_agent_type[at].total_person_travel_time += element.total_person_travel_time
        self.data_by_agent_type[at].total_person_distance_km += element.total_person_distance_km
        self.data_by_agent_type[at].total_person_distance_mile += element.total_person_distance_mile

    def computer_avg_value(self, at: int):
        count = self.data_by_agent_type[at].count_of_links

        if count >= 1:
            self.data_by_agent_type[at].avg_travel_distance_km = self.data_by_agent_type[at].total_person_distance_km / max(1.0, self.data_by_agent_type[at].total_od_volume)

            self.data_by_agent_type[at].avg_travel_distance_mile = self.data_by_agent_type[at].total_person_distance_mile / max(1.0, self.data_by_agent_type[at].total_od_volume)

            self.data_by_agent_type[at].avg_travel_time = self.data_by_agent_type[at].total_person_travel_time / max(1, self.data_by_agent_type[at].total_od_volume)


class AgentType:

    def _initialize_instance_fields(self):

        self.agent_type = ""
        self.display_code = ""
        self.access_node_type = ""
        self.zone_id_cover_map = {}

    def __init__(self, **kwargs):
        self._initialize_instance_fields()

        self.agent_type_no = 1
        self.value_of_time = 100
        self.time_headway_in_sec = 1
        self.real_time_information = 0
        self.access_speed = 2
        self.access_distance_lb = 0.0001
        self.access_distance_ub = 4
        self.access_link_k = 4
        self.PCE = 1
        self.OCC = 1
        self.DSR = 1
        self.number_of_allowed_links = 0

        if kwargs:
            for key in kwargs:
                setattr(self, key, kwargs[key])


class LinkType:

    def _initialize_instance_fields(self):

        self.link_type_name = ""
        self.type_code = ""

    def __init__(self, **kwargs):
        self._initialize_instance_fields()

        self.link_type = 1
        self.number_of_links = 0
        self.traffic_flow_code = e_traffic_flow_model.SPATIAL_QUEUE
        self.k_jam = 300
        self.vdf_type = e_VDF_type.Q_VDF

        if kwargs:
            for key in kwargs:
                setattr(self, key, kwargs[key])


class DTAVehListPerTimeInterval:

    def __init__(self, **kwargs):

        self.m_AgentIDVector = []

        if kwargs:
            for key in kwargs:
                setattr(self, key, kwargs[key])


class Assignment:

    def _initialize_instance_fields(self):

        self.zone_id_to_centriod_node_no_mapping = {}
        self.zone_id_2_node_no_mapping = {}
        self.zone_id_2_cell_id_mapping = {}
        self.cell_id_mapping = {}
        self.cell_id_2_cell_code_mapping = {}

        self.g_origin_demand_array = {}

        self.node_seq_no_2_info_zone_id_mapping = {}
        self.zone_seq_no_2_info_mapping = {}
        self.zone_seq_no_2_activity_mapping = {}
        self.zone_id_to_centriod_node_id_mapping = {}
        self.zone_id_to_seed_zone_id_mapping = {}

        self.g_node_id_to_seq_no_map = {}
        self.access_node_id_to_zone_id_map = {}
        self.g_zone_seq_no_to_analysis_distrct_id_mapping = {}
        self.g_zoneid_to_zone_seq_no_mapping = {}
        self.g_zoneid_to_zone_sindex_no_mapping = {}
        self.g_link_id_map = {}
        self.zone_id_X_mapping = {}
        self.zone_id_Y_mapping = {}

        self.g_DemandPeriodVector = []
        self.g_DepartureTimeProfileVector = []

        self.g_LoadingStartTimeInMin = 0
        self.g_LoadingEndTimeInMin = 0
        self.g_AgentTypeVector = [AgentType() for _ in range(MAX_AGENT_TYPES)]
        self.g_LinkTypeMap = {}
        self.demand_period_to_seqno_mapping = {}
        self.agent_type_2_seqno_mapping = {}
        self.o_district_id_factor_map = {}
        self.d_district_id_factor_map = {}
        self.od_district_id_factor_map = {}
        self.SA_o_district_id_factor_map = {}
        self.SA_d_district_id_factor_map = {}
        self.SA_od_district_id_factor_map = {}

        self.total_demand = [[] for _ in range(MAX_AGENT_TYPES)]
        self.g_DemandGlobalMultiplier = 0

        self.m_link_TD_waiting_time = []
        self.m_link_total_waiting_time_vector = []

        self.g_start_simu_interval_no = 0
        self.g_number_of_simulation_intervals = 0
        self.g_number_of_loading_intervals_in_sec = 0
        self.g_number_of_intervals_in_min = 0
        self.g_number_of_intervals_in_sec = 0
        self.m_TMClink_map = {}
        self.m_TMC_corridor_map = {}

        """
        # self.simu_log_file = std: : ofstream()
        # self.sp_log_file = std: : ofstream()
        # self.assign_log_file = std: : ofstream()
        # self.summary_file = std: : ofstream()
        # self.summary_file2 = std: : ofstream()
        # self.summary_corridor_file = std: : ofstream()
        # self.summary_district_file = std: : ofstream()
        # self.MRM_log_file = std: : ofstream()
        """

    def __init__(self, **kwargs):
        self._initialize_instance_fields()

        self.assignment_mode = e_assignment_mode.LUE
        self.g_number_of_memory_blocks = 4
        self.g_number_of_threads = 1
        self.g_info_updating_freq_in_min = 5
        self.g_visual_distance_in_cells = 5
        self.g_link_type_file_loaded = True
        self.g_agent_type_file_loaded = False
        self.total_demand_volume = 0.0
        self.g_number_of_in_memory_simulation_intervals = 500
        self.g_number_of_column_generation_iterations = 20
        self.g_number_of_column_updating_iterations = 0
        self.g_number_of_ODME_iterations = 0
        self.g_number_of_sensitivity_analysis_iterations = 0
        self.g_number_of_demand_periods = 3
        self.g_number_of_links = 0
        self.g_number_of_timing_arcs = 0
        self.g_number_of_nodes = 0
        self.g_number_of_zones = 0
        self.g_number_of_agent_types = 0
        self.debug_detail_flag = 1
        self.path_output = 1
        self.trajectory_output_count = -1
        self.trace_output = 0
        self.major_path_volume_threshold = 0.000001
        self.trajectory_sampling_rate = 1.0
        self.td_link_performance_sampling_interval_in_min = -1
        self.dynamic_link_performance_sampling_interval_hd_in_min = 15
        self.trajectory_diversion_only = 0
        self.m_GridResolution = 0.01
        self.shortest_path_log_zone_id = -1
        self.g_number_of_analysis_districts = 1
        self.m_LinkCumulativeArrivalVector = None
        self.m_LinkCumulativeDepartureVector = None

        # CA, assign this value to m_LinkCumulativeArrivalVector at a given time in min
        self.m_link_CA_count = None
        self.m_link_CD_count = None
        self.m_LinkOutFlowCapacity = None
        self.m_LinkOutFlowState = None

        if kwargs:
            for key in kwargs:
                setattr(self, key, kwargs[key])

        """self.summary_file.open("final_summary.csv", std: : fstream.out)
        if not self.summary_file.is_open():
            Globals.dtalog.output() << "File final_summary.csv cannot be open."
            g_program_stop()
        self.summary_corridor_file.open("corridor_performance.csv", std: : fstream.out)
        """


class GDPoint:

    def __init__(self, **kwargs):
        self.x = 0
        self.y = 0
        self.node_no = 0
        self.distance_from_origin = 0

        if kwargs:
            for key in kwargs:
                setattr(self, key, kwargs[key])

    def less_than(self, other):
        return self.distance_from_origin < other.distance_from_origin


class Link:

    def _initialize_instance_fields(self):

        self.m_link_pedefined_capacity_map_in_sec = {}
        self.m_link_pedefined_information_response_map = {}
        self.model_speed = [0 for _ in range(MAX_TIME_INTERVAL_PER_DAY)]
        self.est_volume_per_hour_per_lane = [0 for _ in range(MAX_TIME_INTERVAL_PER_DAY)]
        self.est_avg_waiting_time_in_min = [0 for _ in range(MAX_TIME_INTERVAL_PER_DAY)]
        self.est_queue_length_per_lane = [0 for _ in range(MAX_TIME_INTERVAL_PER_DAY)]
        self.dynamic_link_closure_map = {}
        self.dynamic_link_closure_type_map = {}
        self.cost = 0
        self.link_seq_no = 0
        self.capacity_reduction_map = {}
        self.vms_map = {}
        self.link_id = ""
        self.geometry = ""
        self.vdf_code = ""
        self.PCE = 0
        self.from_node_seq_no = 0
        self.to_node_seq_no = 0
        self.mvmt_txt_id = ""
        self.link_code_str = ""
        self.tmc_corridor_name = ""
        self.link_type_name = ""
        self.link_type_code = ""
        self.VDF_period = [PeriodVDF() for _ in range(MAX_TIME_PERIODS)]
        self.type = 0
        self.background_PCE_volume_per_period = [0 for _ in range(MAX_TIME_PERIODS)]
        self.RT_speed_vector = {}
        self.number_of_periods = 0
        self.tmc_code = ""
        self.tmc_road = ""
        self.tmc_direction = ""
        self.tmc_intersection = ""
        self.tmc_reference_speed = 0
        self.tmc_mean_speed = 0
        self.tmc_volume = 0
        self.TMC_from = GDPoint()
        self.TMC_to = GDPoint()
        self.TMC_highest_speed = 0
        self.EntranceQueue = []
        self.ExitQueue = []
        self.win_count = 0
        self.lose_count = 0

    def __init__(self):
        self._initialize_instance_fields()

        self.main_node_id = -1
        self.free_speed = 70
        self.v_congestion_cutoff = 49
        self.v_critical = 49
        self.length_in_meter = 1
        self.link_distance_VDF = 0.001
        self.BWTT_in_simulation_interval = 100
        self.zone_seq_no_for_outgoing_connector = -1
        self.number_of_lanes = 1
        self.lane_capacity = 1999
        self.free_flow_travel_time_in_min = 0.01
        self.link_spatial_capacity = 100
        self.timing_arc_flag = False
        self.traffic_flow_code = 0
        self.spatial_capacity_in_vehicles = 999999
        self.link_type = 2
        self.subarea_id = -1
        self.RT_flow_volume = 0
        self.cell_type = -1
        self.saturation_flow_rate = 1800
        self.dynamic_link_event_start_time_in_min = 99999
        self.b_automated_generated_flag = False
        self.time_to_be_released = -1
        self.RT_waiting_time = 0
        self.FT = 1
        self.AT = 1
        self.s3_m = 4
        self.tmc_road_order = 0
        self.tmc_road_sequence = -1
        self.k_critical = 45
        self.vdf_type = e_VDF_type.Q_VDF
        self.tmc_corridor_id = -1
        self.from_node_id = -1
        self.to_node_id = -1
        self.kjam = 300
        self.link_distance_km = 0
        self.link_distance_mile = 0
        self.meso_link_id = -1
        self.total_simulated_delay_in_min = 0
        self.total_simulated_meso_link_incoming_volume = 0
        self.global_minute_capacity_reduction_start = -1
        self.global_minute_capacity_reduction_end = -1
        self.layer_no = 0

        self.PCE_volume_per_period = [0 for _ in range(MAX_TIME_PERIODS)]
        self.person_volume_per_period = [0 for _ in range(MAX_TIME_PERIODS)]
        self.queue_link_distance_VDF_perslot = [0 for _ in range(MAX_TIME_PERIODS)]
        self.travel_time_per_period = [0 for _ in range(MAX_TIME_PERIODS)]

        self.person_volume_per_period_per_at = np.zeros((MAX_TIME_PERIODS, MAX_AGENT_TYPES))
        self.person_volume_per_district_per_at = np.zeros((MAX_AGENT_TYPES, MAX_ORIGIN_DISTRICTS))

    def calculate_dynamic_VDFunction(self, assignment: Assignment, inner_iteration_number: int, congestion_bottleneck_sensitivity_analysis_mode: bool, VDF_type_no: int):
        RT_waiting_time = 0

        if VDF_type_no in [0, 1]:
            # for each time period

            # here that 3 is from assignment.g_number_of_demand_periods
            for tau in range(assignment.g_number_of_demand_periods):
                link_volume_to_be_assigned = self.PCE_volume_per_period[tau] + self.VDF_period[tau].preload + self.VDF_period[tau].sa_volume

                if self.link_id == "7422":
                    idebug = 1

                if self.VDF_period[tau].num_lanes == 0:
                    idebug = 1

                self.travel_time_per_period[tau] = self.VDF_period[tau].calculate_travel_time_based_on_QVDF(
                    link_volume_to_be_assigned,
                    self.model_speed,
                    self.est_volume_per_hour_per_lane)

                self.VDF_period[tau].link_volume = link_volume_to_be_assigned
        else:
            # VDF_type_no == 2
            for tau in range(assignment.g_number_of_demand_periods):
                self.VDF_period[tau].queue_length = 0
                self.VDF_period[tau].arrival_flow_volume = self.PCE_volume_per_period[tau]
                self.VDF_period[tau].discharge_rate = self.VDF_period[tau].lane_based_ultimate_hourly_capacity * self.VDF_period[tau].num_lanes

                self.VDF_period[tau].avg_waiting_time = 0

            for tau in range(1, assignment.g_number_of_demand_periods):
                self.VDF_period[tau].queue_length = max(0, self.VDF_period[tau - 1].queue_length + self.VDF_period[tau].arrival_flow_volume - self.VDF_period[tau].discharge_rate)

                # if (inner_iteration_number == 1 && g_node_vector[this->from_node_seq_no].node_id == 1 &&
				# g_node_vector[this->to_node_seq_no].node_id == 3):
                #     idebug = 1

            for tau in range(3):
                prevailing_queue_length = 0

                if tau > 1:
                    prevailing_queue_length = self.VDF_period[tau - 1].queue_length

                total_waiting_time = (prevailing_queue_length + self.VDF_period[tau].queue_length) / 2 * self.VDF_period[tau].L

                self.VDF_period[tau].avg_waiting_time = total_waiting_time / max(1, self.VDF_period[tau].arrival_flow_volume)
                self.VDF_period[tau].avg_travel_time = self.VDF_period[tau].FFTT + self.VDF_period[tau].avg_waiting_time
                self.VDF_period[tau].DOC = (prevailing_queue_length + self.VDF_period[tau].arrival_flow_volume) / max(0.01, self.VDF_period[tau].lane_based_ultimate_hourly_capacity * self.VDF_period[tau].num_lanes)

                self.travel_time_per_period[tau] = self.VDF_period[tau].avg_waiting_time + self.VDF_period[tau].FFTT

                for slot_no in range(int(assignment.g_DemandPeriodVector[tau].starting_time_slot_no), int(assignment.g_DemandPeriodVector[tau].ending_time_slot_no)):
                    self.est_queue_length_per_lane[slot_no] = self.VDF_period[tau].queue_length / max(1, self.number_of_lanes)
                    self.est_avg_waiting_time_in_min[slot_no] = self.VDF_period[tau].avg_waiting_time
                    number_of_hours = assignment.g_DemandPeriodVector[tau].time_period_in_hour
                    self.est_volume_per_hour_per_lane[slot_no] = self.VDF_period[tau].arrival_flow_volume / max(0.01, number_of_hours) / max(1, self.number_of_lanes)

    def calculate_marginal_cost_for_agent_type(self, tau: int, agent_type_no: int, PCE_agent_type: float):
        # volume * dervative
        # BPR_term: volume * FFTT * alpha * (beta) * power(v/c, beta-1),

        #        travel_marginal_cost_per_period[tau][agent_type_no] = VDF_period[tau].marginal_base * PCE_agent_type
        pass

    def get_generalized_first_order_gradient_cost_of_second_order_loss_for_agent_type(self, tau: int, agent_type_no: int) -> float:
        # *60 as 60 min per hour
        generalized_cost = self.travel_time_per_period[tau] + self.VDF_period[tau].penalty + self.VDF_period[tau].toll[agent_type_no] / Assignment().g_AgentTypeVector[agent_type_no].value_of_time * 60

        return generalized_cost

    def get_model_5_min_speed(self, time_in_min: int) -> float:
        t = math.trunc(time_in_min / float(5))
        # total_speed_value = 0
        # total_speed_count = 0
        return self.model_speed[t]

    def get_model_15_min_speed(self, time_in_min: int) -> float:
        t = math.trunc(time_in_min / float(5))
        total_speed_value = 0
        total_speed_count = 0

        for tt in range(3):
            if (t + tt >= 0) and (t + tt < MAX_TIME_INTERVAL_PER_DAY) and self.model_speed[t + tt] >= 1:
                total_speed_value += self.model_speed[t + tt]
                total_speed_count += 1

        return total_speed_value / max(1, total_speed_count)

    def get_model_hourly_speed(self, time_in_min: int) -> float:
        t = math.trunc(time_in_min / float(5))
        total_speed_value = 0
        total_speed_count = 0

        for tt in range(12):
            if (t + tt >= 0) and (t + tt < MAX_TIME_INTERVAL_PER_DAY) and self.model_speed[t + tt] >= 1:
                total_speed_value += self.model_speed[t + tt]
                total_speed_count += 1
        return total_speed_value / max(1, total_speed_count)

    def get_est_hourly_volume(self, time_in_min: int) -> float:
        t = math.trunc(time_in_min / float(5))
        total_volume_value = 0
        total_volume_count = 0

        for tt in range(12):

            if (t + tt >= 0) and (t + tt < MAX_TIME_INTERVAL_PER_DAY) and (self.est_volume_per_hour_per_lane[t + tt] >= 1):
                total_volume_value += self.est_volume_per_hour_per_lane[t + tt]
                total_volume_count += 1
        return total_volume_value / max(1, total_volume_count)

    def update_kc(self, free_speed_value: float):

        self.k_critical = 45
        self.v_critical = self.lane_capacity / self.k_critical
        if free_speed_value != 0 and self.v_critical != 0:
            self.s3_m = 2 * math.log(2) / math.log(free_speed_value / self.v_critical)

            self.TMC_highest_speed = free_speed_value

    def get_volume_from_speed(self, speed: float, free_speed_value: float, lane_capacity: float) -> float:
        #test data free_speed = 55.0f;
        #speed = 52
        #k_critical = 23.14167648

        speed = min(speed, free_speed_value * 0.99)
        if speed < 0:
            return -1

        self.v_critical = lane_capacity / self.k_critical
        self.s3_m = 2 * math.log(2) / math.log(free_speed_value / self.v_critical)

        speed_ratio = free_speed_value / max(1.0, speed)
        speed_ratio = max(speed_ratio, 1.00001)

        #   float volume = 0
        ratio_difference = math.pow(speed_ratio, self.s3_m / 2) - 1

        ratio_difference_final = max(ratio_difference, 0.00000001)

        volume = speed * self.k_critical * math.pow(ratio_difference_final, 1 / self.s3_m)

        volume = min(volume, lane_capacity)
        return volume

    def AllowAgentType(self, agent_type: str, tau: int) -> bool:
        # if the allowed_uses is empty then all types are allowed.
        if self.VDF_period[tau].allowed_uses.size() == 0 or self.VDF_period[tau].allowed_uses == "all":
            return True
        else:
            # otherwise, only an agent type is listed in this "allowed_uses", then this agent type is allowed to travel on this link
            return self.VDF_period[tau].allowed_uses.find(agent_type) != -1


class VDFType:

    def __init__(self):
        self.vdf_code = ""
        self.VDF_period_sum = [PeriodVDF() for _ in range(MAX_TIME_PERIODS)]

    def record_qvdf_data(self, element: PeriodVDF, tau: int):
        # sourcery skip: extract-method
        if tau >= MAX_TIME_PERIODS:
            return

        if self.VDF_period_sum[tau].vdf_data_count == 0:

            self.VDF_period_sum[tau].peak_load_factor = element.peak_load_factor
            self.VDF_period_sum[tau].Q_alpha = element.Q_alpha
            self.VDF_period_sum[tau].Q_beta = element.Q_beta
            self.VDF_period_sum[tau].Q_cp = element.Q_cp
            self.VDF_period_sum[tau].Q_n = element.Q_n
            self.VDF_period_sum[tau].Q_s = element.Q_s
            self.VDF_period_sum[tau].Q_cd = element.Q_cd
        else:
            self.VDF_period_sum[tau].peak_load_factor += element.peak_load_factor
            self.VDF_period_sum[tau].Q_alpha += element.Q_alpha
            self.VDF_period_sum[tau].Q_beta += element.Q_beta
            self.VDF_period_sum[tau].Q_cp += element.Q_cp
            self.VDF_period_sum[tau].Q_n += element.Q_n
            self.VDF_period_sum[tau].Q_s += element.Q_s
            self.VDF_period_sum[tau].Q_cd += element.Q_cd

        self.VDF_period_sum[tau].vdf_data_count += 1

    def computer_avg_parameter(self, tau: int):
        count = self.VDF_period_sum[tau].vdf_data_count
        if count >= 1:
            self.VDF_period_sum[tau].peak_load_factor /= count
            self.VDF_period_sum[tau].Q_alpha /= count
            self.VDF_period_sum[tau].Q_beta /= count
            self.VDF_period_sum[tau].Q_cp /= count
            self.VDF_period_sum[tau].Q_n /= count
            self.VDF_period_sum[tau].Q_s /= count
            self.VDF_period_sum[tau].Q_cd /= count


class PeriodCorridor:

    def __init__(self):

        self.volume = 0
        self.count = 0
        self.speed = 0
        self.DoC = 0
        self.P = 0
        self.AvgP = 0
        self.MaxP = 0


class Corridor_Info:

    def __init__(self):
        self.tmc_corridor_name = ""
        self.corridor_period = [PeriodCorridor() for _ in range(MAX_TIME_PERIODS)]
        self.corridor_period_before = [
            PeriodCorridor() for _ in range(MAX_TIME_PERIODS)]

    def record_link_2_corridor_data(self, element: PeriodCorridor, tau: int):
        if tau >= MAX_TIME_PERIODS:
            return

        self.corridor_period[tau].volume += element.volume
        self.corridor_period[tau].DoC += element.DoC
        self.corridor_period[tau].speed += element.speed
        self.corridor_period[tau].P = max(self.corridor_period[tau].P, element.P)
        self.corridor_period[tau].count += 1

    def computer_avg_value(self, tau: int):
        count = self.corridor_period[tau].count
        if count >= 1:
            self.corridor_period[tau].volume /= count
            self.corridor_period[tau].speed /= count
            self.corridor_period[tau].DoC /= count


class Node:

    def _initialize_instance_fields(self):

        self.cell_id = 0
        self.cell_str = ""
        self.zone_coordinate_vector = []
        self.node_type = ""
        self.agent_type_str = ""
        self.agent_id = ""
        self.node_id = 0
        self.x = 0
        self.y = 0
        self.m_outgoing_link_seq_no_vector = []
        self.m_incoming_link_seq_no_vector = []
        self.m_to_node_seq_no_vector = []
        self.m_to_node_2_link_seq_no_map = {}
        self.m_prohibited_movement_string_map = {}
        self.next_link_for_resource_request = {}
        self.label_cost = {}
        self.pred_per_iteration_map = {}
        self.label_cost_per_iteration_map = {}
        self.pred_RT_map = {}
        self.label_cost_RT_map = {}

        self.label_cost_RT_map = {}

    def __init__(self):
        self._initialize_instance_fields()

        self.zone_id = -1
        self.zone_org_id = -1
        self.layer_no = 0
        self.MRM_gate_flag = -1
        self.prohibited_movement_size = 0
        self.node_seq_no = -1
        self.subarea_id = -1
        self.is_activity_node = 0
        self.agent_type_no = -1
        self.is_boundary = 0
        self.access_distance = 0.04


class DTA_Direction(Enum):
    DTA_NULL = 0
    DTA_NORTH = 1
    DTA_SOUTH = 2
    DTA_EAST = 3
    DTA_WEST = 4


class TMC_Corridor_Info:

    def _initialize_instance_fields(self):

        self.m_dir = 0
        self.avg_speed = 0
        self.total_congestion_duration = 0
        self.road_sequence_map = {}
        self.node_no_vector = []
        self.point_vector = []
        self.center = GDPoint()

    def __init__(self, **kwargs):
        self._initialize_instance_fields()

        self.total_PMT = 0
        self.total_PHT = 0
        self.total_PSDT = 0
        self.lowest_speed = 9999
        self.highest_speed = -1
        self.link_count = 0
        self.origin_node_no = 0
        self.tmc_corridor_id = 0

        if kwargs:
            for key in kwargs:
                setattr(self, key, kwargs[key])

    def Find_P2P_Angle(self, p1: GDPoint, p2: GDPoint) -> float:
        delta_x = p2.x - p1.x
        delta_y = p2.y - p1.y

        if abs(delta_x) < 0.00001:
            delta_x = 0

        if abs(delta_y) < 0.00001:
            delta_y = 0

        angle = math.atan2(delta_y, delta_x) * 180 / 3.14159 + 0.5
        # angle = 90 - angle

        while angle < 0:
            angle += 360

        while angle > 360:
            angle -= 360

        return angle

    def test_direction_matching(self, dir1: DTA_Direction, dir2: DTA_Direction) -> bool:
        if dir1 == DTA_Direction.DTA_NORTH and dir2 == DTA_Direction.DTA_SOUTH:
            return False

        if dir2 == DTA_Direction.DTA_NORTH and dir1 == DTA_Direction.DTA_SOUTH:
            return False

        if dir1 == DTA_Direction.DTA_EAST and dir2 == DTA_Direction.DTA_WEST:
            return False

        if dir2 == DTA_Direction.DTA_EAST and dir1 == DTA_Direction.DTA_WEST:
            return False

        return True

    def Find_Closest_Angle_to_Approach(self, angle: float) -> DTA_Direction:
        if angle < 45:
            return DTA_Direction.DTA_NORTH
        elif angle < 45 + 90:
            return DTA_Direction.DTA_EAST
        elif angle < 225:
            return DTA_Direction.DTA_SOUTH
        elif angle < 315:
            return DTA_Direction.DTA_SOUTH
        else:
            return DTA_Direction.DTA_NORTH

    def reset(self):
        self.total_PMT = 0
        self.total_PHT = 0
        self.total_PSDT = 0
        self.lowest_speed = 9999
        self.highest_speed = -1
        self.link_count = 0

    def get_avg_speed(self):
        return self.total_PMT / max(0.001, self.total_PHT)  # miles per hour

    def find_center_and_origin(self):
        # first stage: find center
        x = 0
        y = 0

        for k in range(len(self.point_vector)):
            x += self.point_vector[k].x
            y += self.point_vector[k].y


        self.center.x = x / max(1, len(self.point_vector))
        self.center.y = y / max(1, len(self.point_vector))


        # second stage: find origin
        longest_distance_from_center = 0

        origin = GDPoint()
        origin.x = 0
        origin.y = 0

        origin_node_k = -1
        for k in range(len(self.point_vector)):
            local_distance_from_center = 999999

            if self.m_dir != DTA_Direction.DTA_NULL:

                dir1 = self.Find_Closest_Angle_to_Approach(self.Find_P2P_Angle(self.point_vector[k], self.center))

                if self.test_direction_matching(dir1, self.m_dir):
                    local_distance_from_center = math.pow(math.pow(self.point_vector[k].x - self.center.x, 2) + math.pow(self.point_vector[k].y - self.center.y, 2), 0.5)


                    if local_distance_from_center > longest_distance_from_center:
                        longest_distance_from_center = local_distance_from_center # reset
                        self.origin_node_no = self.node_no_vector[k]
                        origin_node_k = k
                        origin.x = self.point_vector[k].x
                        origin.y = self.point_vector[k].y


        # third stage: compute the distance from origin for each node

        for k in range(len(self.point_vector)):
            local_distance_from_origin = math.pow(math.pow(self.point_vector[k].x - origin.x, 2) + math.pow(self.point_vector[k].y - origin.y, 2), 0.5)

            self.point_vector[k].distance_from_origin = local_distance_from_origin

        # forth stage: sort the point vector according the distance
        self.point_vector.sort(key=lambda x: x.distance_from_origin, reverse=False)
