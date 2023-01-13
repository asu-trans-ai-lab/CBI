# -*- coding:utf-8 -*-
##############################################################
# Created Date: Friday, December 16th 2022
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

import os
import yaml
import pandas as pd
import math

from utility_lib import required_input_file_dict
from func_lib import (get_file_from_folder_by_type,
                      check_required_files_exist,
                      check_required_column_names_exist,
                      func_running_time,
                      path2linux,
                      validate_filename,
                      generate_absolute_path)

from DTA import (Assignment,
                 DemandPeriod,
                 Node,
                 Link,
                 LinkType,
                 GDPoint,
                 e_traffic_flow_model,
                 e_VDF_type)

from DTA import (MIN_PER_TIME_SLOT,
                 MAX_TIME_INTERVAL_PER_DAY,
                 DTA_Direction,
                 TMC_Corridor_Info)
from cbi_reading import g_measurement_tstamp_parser, TMCLink


class CBI_TOOL:
    def __init__(self, path_input_folder: str) -> None:
        # initialize variables for the CBI TOOL
        self.__initial_values()

        self.path_input_folder = path_input_folder

        # Check if all required input files are provided in the input folder
        self.isRequired = self.__check_required_files_exist_in_folder()

        if self.isRequired:
            # prepare demand period for assignment
            self.__prepare_demand_period_for_assignment()
        else:
            raise Exception("Required input files are not provided in the input folder!")

    def __initial_values(self):

        self.g_node_vector = []  # Node
        self.g_link_vector = []  # Link
        self.g_vdf_type_map = {}  # VDF_Type
        self.g_corridor_info_base0_map = {}
        self.g_corridor_info_SA_map = {}  # Corridor_Info

        self.g_tmc_corridor_vector = {}  # TMC_Corridor_Info
        self.g_TMC_vector = []  # TMC_Link

        self.g_related_zone_vector_size = 0

        # initialize assignment object
        self.assignment = Assignment()

        self.node_col_name = ["node_id", "node_no", "layer_no", "agent_id", "sequence_no",
                              "distance_from_origin", "MRM_gate_flag", "node_type", "is_boundary",
                              "#_of_outgoing_nodes", "activity_node_flag", "agent_type",
                              "zone_id", "cell_code", "info_zone_flag", "x_coord", "y_coord"]
        self.link_col_name = ["link_id", "link_no", "layer_no", "from_node_id", "to_node_id",
                              "from_gate_flag", "to_gate_flag", "link_type", "link_type_name",
                              "lanes", "link_distance_VDF", "free_speed", "cutoff_speed", "fftt",
                              "capacity", "allow_uses", "BPR_plf", "BPR_alpha", "BPR_beta",
                              "QVDF_qdf", "QVDF_alpha", "QVDF_beta", "QVDF_cd", "QVDF_n", "geometry"]

        _cbi_col_1 = ["link_id", "tmc", "tmc_corridor_name", "tmc_corridor_id", "tmc_road_order",
                      "tmc_road_sequence", "tmc_road", "tmc_direction", "tmc_intersection",
                      "tmc_highest_speed", "link_no", "from_node_id", "to_node_id",
                      "link_type", "link_type_code", "FT", "AT", "vdf_code",
                      "nlanes", "link_distance_VDF", "free_speed", "capacity",
                      "k_critical", "v_congestion_cutoff"]
        _cbi_col_2 = ["highest_speed", "vcutoff_updated", "vcutoff_ratio", "v_critical_s3"]

        _cbi_col_3 = [f"{period}_{name}"  for period in ["AM","MD","PM"] for name in ["t0","t3","V","peak_hour_volume","D","VC_ratio","DC_ratio","P","vc/vt2-1","vf_delay_index","vc_delay_index","speed_ph","queue_speed","vt2","plf","Q_n","Q_cp","Q_alpha","Q_beta","mV","mD","mDC_ratio","mP","mv_QVDF","mvt2_QVDF","m_mu_QVDF","m_gamma_QVDF","m_peak_hour_volume","mVC_ratio","mv_BPR"]]

        _cbi_col_3 += ["geometry", "tmc_geometry"]

        _cbi_col_4 = [f"vh{divmod(hour, 60)[0]}" for hour in range(6 * 60, 20 * 60, 60)]
        _cbi_col_5 = [f"m_vh{divmod(hour, 60)[0]}" for hour in range(
            6 * 60, 20 * 60, 60)]

        _cbi_col_6 = ["evhMAE", "evhMAPE", "evhRMSE"]
        _cbi_col_7 = [f"qh{divmod(hour, 60)[0]}" for hour in range(6 * 60, 20 * 60, 60)]
        _cbi_col_8 = [f"vhr{divmod(hour, 60)[0]}" for hour in range(6 * 60, 20 * 60, 60)]

        _cbi_col_9 = [f"v{divmod(hour, 60)[0]}: {divmod(hour, 60)[1]}" for hour in range(6 * 60, 20 * 60, 5)]
        _cbi_col_10 = [f"mv{divmod(hour, 60)[0]}: {divmod(hour, 60)[1]}" for hour in range(6 * 60, 20 * 60, 5)]
        _cbi_col_11 = [f"v{divmod(hour, 60)[0]}: {divmod(hour, 60)[0]}" for hour in range(6 * 60, 20 * 60, 15)]
        _cbi_col_12 = [f"mv{divmod(hour, 60)[0]}: {divmod(hour, 60)[0]}" for hour in range(6 * 60, 20 * 60, 15)]

        _cbi_col_13 = [f"q{divmod(hour, 60)[0]}: {divmod(hour, 60)[0]}" for hour in range(6 * 60, 20 * 60, 5)]

        self.cbi_summary_col_name = _cbi_col_1 + _cbi_col_2 + _cbi_col_3 + _cbi_col_4 + _cbi_col_5 + _cbi_col_6 + _cbi_col_7 + _cbi_col_8 + _cbi_col_9 + _cbi_col_10 + _cbi_col_11 + _cbi_col_12 + _cbi_col_13

        self.link_qvdf_col_name = ["data_type","link_id","tmc_corridor_name","from_node_id","to_node_id","vdf_code"]

        for i in range(3):
            self.link_qvdf_col_name += [f"QVDF_plf{i+1}",f"QVDF_n{i+1}",f"QVDF_s{i+1}",f"QVDF_cp{i+1}",f"QVDF_cd{i+1}",f"QVDF_alpha{i+1}",f"QVDF_beta{i+1}"]

    def __check_required_files_exist_in_folder(self) -> bool:
        # get all csv files in the input folder
        csv_files = get_file_from_folder_by_type(self.path_input_folder, file_type="csv")
        yaml_files = get_file_from_folder_by_type(self.path_input_folder, file_type="yml")
        return check_required_files_exist(list(required_input_file_dict.keys()), csv_files + yaml_files)

    def __prepare_demand_period_for_assignment(self) -> Assignment:
        self.assignment.g_LoadingStartTimeInMin = 99999
        self.assignment.g_LoadingEndTimeInMin = 0

        # AM, MD, Afternoon
        demand_period = DemandPeriod()
        am_md_afternoon = [(7 * 60, 9 * 60), (10 * 60, 14 * 60), (15 * 60, 19 * 60)]
        am_md_afternoon_demand_period = ["AM", "MD", "PM"]
        am_md_afternoon_demand_period_id = [1, 2, 2]

        for i in range(len(am_md_afternoon)):
            # create demand period with id and name
            global_minute_vector = am_md_afternoon[i]
            demand_period.demand_period_id = am_md_afternoon_demand_period_id[i]
            demand_period.demand_period = am_md_afternoon_demand_period[i]

            # update values accordingly
            demand_period.starting_time_slot_no = global_minute_vector[0] / MIN_PER_TIME_SLOT
            demand_period.ending_time_slot_no = global_minute_vector[1] / MIN_PER_TIME_SLOT
            demand_period.time_period_in_hour = (global_minute_vector[1] - global_minute_vector[0]) / 60
            demand_period.t2_peak_in_hour = (global_minute_vector[0] + global_minute_vector[1]) / 2 / 60

            # add demand period to assignment
            self.assignment.g_DemandPeriodVector.append(demand_period)

        # initialize counter to 0
        self.assignment.g_number_of_nodes = 0
        self.assignment.g_number_of_links = 0

        return self.assignment

    @func_running_time
    def read_settings_yaml_file(self) -> None:
        print("Start reading settings.yml...\n")
        path_yaml = path2linux(os.path.join(self.path_input_folder, "settings.yml"))

        # load yaml data
        with open(path_yaml, "r", encoding="utf-8") as f:
            data_yaml = yaml.safe_load(f)
        df_yaml = pd.DataFrame(data_yaml)

        # check required column name
        isColumnNameRequired = check_required_column_names_exist(
            list(required_input_file_dict["settings.yml"]),
            list(df_yaml.columns)
        )

        if not isColumnNameRequired:
            raise Exception("Column name not required: please check settings.yml file")

        # create a special link typ for virtual connector
        element_vc = LinkType()
        element_vc.link_type = -1
        element_vc.type_code = "c"
        element_vc.traffic_flow_code = e_traffic_flow_model.SPATIAL_QUEUE
        self.assignment.g_LinkTypeMap[element_vc.link_type] = element_vc
        # end of create special link type for virtual connectors

        for i in range(len(df_yaml)):
            element = LinkType()

            element.link_type = df_yaml.loc[i, "link_type"]
            element.type_code = df_yaml.loc[i, "type_code"]
            element.vdf_type = e_traffic_flow_model

            # a new column called: vdf_type
            if "vdf_type" in df_yaml.columns:
                vdf_type_str = df_yaml.loc[i, "vdf_type"]
            else:
                vdf_type_str = ""

            if vdf_type_str == "bpr":
                element.vdf_type = e_VDF_type.BPR_VDF

            if vdf_type_str == "qvdf":
                element.vdf_type = e_VDF_type.Q_VDF

            element.traffic_flow_code = e_traffic_flow_model.SPATIAL_QUEUE

            if "k_jam" in df_yaml.columns:
                element.k_jam = df_yaml.loc[i, "k_jam"]

            traffic_flow_code_str = df_yaml.loc[i, "traffic_flow_code"]
            if traffic_flow_code_str == "point_queue":
                element.traffic_flow_code = e_traffic_flow_model.POINT_QUEUE

            if traffic_flow_code_str == "spatial_queue":
                element.traffic_flow_code = e_traffic_flow_model.SPATIAL_QUEUE

            if traffic_flow_code_str == "kw":
                element.traffic_flow_code = e_traffic_flow_model.KINEMATIVE_WAVE

            self.assignment.g_LinkTypeMap[element.link_type] = element

        print("Settings.yml loaded...\n")

    @func_running_time
    def read_tmc_identification_csv_file(self) -> None:
        print("Start reading tmc_identification.csv file...\n")
        path_tmc_identification = path2linux(os.path.join(self.path_input_folder, "tmc_identification.csv"))
        df_tmc_identification = pd.read_csv(path_tmc_identification)
        tmc_identification_col = list(df_tmc_identification.columns)

        # dictionary store key: value pair; string: int
        long_lat_string_to_node_id_mapping = {}

        # dictionary store key: value pair; int: int
        zone_id_to_analysis_district_id_mapping = {}

        internal_node_seq_no = 0

        # read Node data
        # Prepare and Save Node data to g_NodeVector and assignment
        for i in range(len(df_tmc_identification)):
            node = Node()

            x_coord_from = start_longitude = df_tmc_identification.loc[i, "start_longitude"]
            y_coord_from = start_latitude = df_tmc_identification.loc[i, "start_latitude"]
            x_coord_to = end_longitude = df_tmc_identification.loc[i, "end_longitude"]
            y_coord_to = end_latitude = df_tmc_identification.loc[i, "end_latitude"]
            direction = df_tmc_identification.loc[i, "direction"]

            if direction == "EASTBOUND":
                DTA_DIR = DTA_Direction(DTA_Direction.DTA_EAST)
            elif direction == "NORTHBOUND":
                DTA_DIR = DTA_Direction(DTA_Direction.DTA_NORTH)
            elif direction == "SOUTHBOUND":
                DTA_DIR = DTA_Direction(DTA_Direction.DTA_SOUTH)
            elif direction == "WESTBOUND":
                DTA_DIR = DTA_Direction(DTA_Direction.DTA_WEST)
            else:
                DTA_DIR = DTA_Direction(DTA_Direction.DTA_NULL)

            if "tmc_corridor_name" in tmc_identification_col:
                tmc_corridor_name = df_tmc_identification.loc[i, "tmc_corridor_name"]
            elif {"road", "direction"}.issubset(set(tmc_identification_col)):
                tmc_corridor_name = df_tmc_identification.loc[i, "road"] + "_" + df_tmc_identification.loc[i, "direction"]
            else:
                tmc_corridor_name = ""

            long_lat_string_from = f"{str(start_longitude)}_{str(start_latitude)}"
            long_lat_string_to = f"{str(end_longitude)}_{str(end_latitude)}"

            corridor = TMC_Corridor_Info()

            # if tmc_corridor_name not in dictionary of g_tmc_corridor_vector
            if tmc_corridor_name not in self.g_tmc_corridor_vector:

                corridor.tmc_corridor_id = len(self.g_tmc_corridor_vector) + 1
                corridor.m_dir = DTA_DIR
                self.g_tmc_corridor_vector[tmc_corridor_name] = corridor

            # if long_lat_string_from not in dictionary of long_lat_string_to_node_id_mapping
            if long_lat_string_from not in long_lat_string_to_node_id_mapping:
                # micro network filter
                pt = GDPoint()
                pt.x = x_coord_from
                pt.y  = y_coord_from

                node_id = len(self.assignment.g_node_id_to_seq_no_map) + 1
                long_lat_string_to_node_id_mapping[long_lat_string_from] = node_id

                self.assignment.g_node_id_to_seq_no_map[node_id] = internal_node_seq_no
                node.node_id = node_id
                node.node_seq_no = internal_node_seq_no
                node.x = x_coord_from
                node.y = y_coord_from
                node.agent_id = tmc_corridor_name

                self.g_node_vector.append(node)

                self.g_tmc_corridor_vector[tmc_corridor_name].node_no_vector.append(internal_node_seq_no)
                pt.node_no = node.node_seq_no
                self.g_tmc_corridor_vector[tmc_corridor_name].point_vector.append(pt)

                internal_node_seq_no += 1

                self.assignment.g_number_of_nodes += 1

            # if long_lat_string_to not in dictionary of long_lat_string_to_node_id_mapping
            if long_lat_string_to not in long_lat_string_to_node_id_mapping:
                pt = GDPoint()
                pt.x = x_coord_to
                pt.y = y_coord_to

                node_id = len(self.assignment.g_node_id_to_seq_no_map) + 1
                long_lat_string_to_node_id_mapping[long_lat_string_to] = node_id
                self.assignment.g_node_id_to_seq_no_map[node_id] = internal_node_seq_no
                node.node_id = node_id
                node.node_seq_no = internal_node_seq_no
                node.x = x_coord_to
                node.y = y_coord_to
                node.agent_id = tmc_corridor_name

                self.g_node_vector.append(node)

                self.g_tmc_corridor_vector[tmc_corridor_name].node_no_vector.append(internal_node_seq_no)
                pt.node_no = node.node_seq_no
                self.g_tmc_corridor_vector[tmc_corridor_name].point_vector.append(pt)
                self.assignment.g_number_of_nodes += 1
                internal_node_seq_no += 1

            if self.assignment.g_number_of_nodes % 1000 == 0:
                print(f"reading {self.assignment.g_number_of_nodes} node...")

        # read link data
        link_type_warning_count = 0
        length_in_km_warning = False

        for i in range(len(df_tmc_identification)):
            link = Link()

            # Prepare and Save Link data to g_LinkVector and assignment
            if "link_type_name" in tmc_identification_col:
                link_type_name = df_tmc_identification.loc[i, "link_type_name"]
            else:
                link_type_name = ""

            start_longitude = df_tmc_identification.loc[i, "start_longitude"]
            start_latitude = df_tmc_identification.loc[i, "start_latitude"]
            end_longitude = df_tmc_identification.loc[i, "end_longitude"]
            end_latitude = df_tmc_identification.loc[i, "end_latitude"]

            long_lat_string_from = f"{str(start_longitude)}_{str(start_latitude)}"
            long_lat_string_to = f"{str(end_longitude)}_{str(end_latitude)}"

            from_node_id = long_lat_string_to_node_id_mapping.get(long_lat_string_from, -1)
            to_node_id = long_lat_string_to_node_id_mapping.get(long_lat_string_to, -1)

            if from_node_id == -1 or to_node_id == -1:
                continue

            link_id = df_tmc_identification.loc[i, "tmc"]

            # add the to node id into the outbound (adjacent) node list
            if from_node_id not in self.assignment.g_node_id_to_seq_no_map:
                print(f"Error: from_node_id {from_node_id} in file TMC_Identification.csv is not defined in node.csv")

            if to_node_id not in self.assignment.g_node_id_to_seq_no_map:
                print(f"Error: to_node_id {to_node_id} in file TMC_Identification.csv is not defined in node.csv")

            internal_from_node_seq_no = self.assignment.g_node_id_to_seq_no_map[from_node_id]
            internal_to_node_seq_no = self.assignment.g_node_id_to_seq_no_map[to_node_id]

            link.from_node_seq_no = internal_from_node_seq_no
            link.to_node_seq_no = internal_to_node_seq_no
            link.link_seq_no = self.assignment.g_number_of_links
            link.link_id = link_id

            self.assignment.g_link_id_map[link.link_id] = 1

            link.tmc_code = link_id
            link.tmc_road_sequence = 1

            if tmc_corridor_name:
                link.tmc_corridor_name = tmc_corridor_name

            if "road_order" in tmc_identification_col:
                # "corridor_link_sequence"
                corridor_link_sequence = df_tmc_identification.loc[i, "road_order"]
            else:
                corridor_link_sequence = ""

            if corridor_link_sequence:
                link.tmc_road_sequence = corridor_link_sequence

            if link.tmc_corridor_name in self.g_tmc_corridor_vector:
                link.tmc_corridor_id = self.g_tmc_corridor_vector[link.tmc_corridor_name].tmc_corridor_id

            link_type = 2
            length = 1  # km or mile
            free_speed = 60
            cutoff_speed = 1.0

            # print("link_type", link.link_type)
            if link.link_type in self.assignment.g_LinkTypeMap:
                k_jam = self.assignment.g_LinkTypeMap[link.link_type].k_jam
            else:
                k_jam = 300

            bwtt_speed = 12

            lane_capacity = 1800
            length = df_tmc_identification.loc[i, "miles"]

            link.free_flow_travel_time_in_min = length / free_speed * 60
            fftt_in_sec = link.free_flow_travel_time_in_min * 60

            link.length_in_meter = length * 1609.34
            link.link_distance_VDF = length
            link.link_distance_mile = length

            link.numbeer_of_lanes = 1
            link.lane_capacity = lane_capacity

            if link.link_type in self.assignment.g_LinkTypeMap:
                link.vdf_type = self.assignment.g_LinkTypeMap[link.link_type].vdf_type
            link.k_jam = k_jam

            VDF_field_name = []

            for i in range(MAX_TIME_INTERVAL_PER_DAY):
                link.model_speed[i] = free_speed
                link.est_volume_per_hour_per_lane[i] = 0
                link.est_avg_waiting_time_in_min[i] = 0
                link.est_queue_length_per_lane[i] = 0

            for tau in range(self.assignment.g_number_of_demand_periods):
                if link.link_type in self.assignment.g_LinkTypeMap:
                    link.VDF_period[tau].vdf_type = self.assignment.g_LinkTypeMap[link.link_type].vdf_type
                link.VDF_period[tau].lane_based_ultimate_hourly_capacity = lane_capacity
                link.VDF_period[tau].num_lanes = 1

                link.VDF_period[tau].FFTT = link.link_distance_VDF / max(0.0001, link.free_speed) * 60
                link.v_congestion_cutoff = 0.7 * link.free_speed
                link.VDF_period[tau].vf = link.free_speed
                link.VDF_period[tau].v_congestion_cutoff = link.v_congestion_cutoff
                link.VDF_period[tau].aplha = 0.15
                link.VDF_period[tau].beta = 4
                link.VDF_period[tau].preload = 0

                link.VDF_period[tau].starting_time_in_hour = self.assignment.g_DemandPeriodVector[tau].starting_time_slot_no * MIN_PER_TIME_SLOT / 60.0
                link.VDF_period[tau].ending_time_in_hour = self.assignment.g_DemandPeriodVector[tau].ending_time_slot_no * MIN_PER_TIME_SLOT / 60.0
                link.VDF_period[tau].L = self.assignment.g_DemandPeriodVector[tau].time_period_in_hour
                link.VDF_period[tau].t2 = self.assignment.g_DemandPeriodVector[tau].t2_peak_in_hour
                link.VDF_period[tau].peak_load_factor = 1

            link.update_kc(free_speed)
            link.link_spatial_capacity = k_jam * 1 * link.link_distance_VDF
            link.link_distance_VDF = max(0.000001, link.link_distance_VDF)

            for tau in range(self.assignment.g_number_of_demand_periods):
                link.travel_time_per_period[tau] = link.link_distance_VDF / free_speed * 60

            self.g_node_vector[internal_from_node_seq_no].m_outgoing_link_seq_no_vector.append(
                link.link_seq_no)
            self.g_node_vector[internal_to_node_seq_no].m_incoming_link_seq_no_vector.append(
                link.link_seq_no)
            self.g_node_vector[internal_from_node_seq_no].m_to_node_seq_no_vector.append(link.to_node_seq_no)
            self.g_node_vector[internal_from_node_seq_no].m_to_node_2_link_seq_no_map[link.to_node_seq_no] = link.link_seq_no

            self.g_link_vector.append(link)
            self.assignment.g_number_of_links += 1

            if self.assignment.g_number_of_links % 10000 == 0:
                print("reading link %d" % self.assignment.g_number_of_links)

        print("tmc_identification file loaded...")

    @func_running_time
    def read_Readings_csv_file(self) -> None:
        print("Start reading Reading.csv file...\n")
        path_reading = path2linux(os.path.join(self.path_input_folder, "Reading.csv"))
        df_reading = pd.read_csv(path_reading)

        isColumnNameRequired = check_required_column_names_exist(
            list(required_input_file_dict["Reading.csv"]),
            list(df_reading.columns)
        )

        if not isColumnNameRequired:
            raise Exception("Column name not required: please check Reading.csv")

        # convert measurement_tstamp to datetime
        df_reading["measurement_tstamp"] = pd.to_datetime(df_reading["measurement_tstamp"])

        for i in range(len(df_reading)):
            tmc = df_reading.loc[i, "tmc_code"]

            # convert time stamp to string
            measurement_tstamp = str(df_reading.loc[i, "measurement_tstamp"])

            length_of_measurement_tstamp = len(measurement_tstamp)
            if length_of_measurement_tstamp == 0:
                continue

            if length_of_measurement_tstamp < 18:
                print(f"reading data for measurement_tstamp = {measurement_tstamp}, len of the timestamp is {length_of_measurement_tstamp}. \nPlease use stand ISO 8601 data and time to format. eg: 2022-05-23T22:00:23")

            tmc_reference_speed = 0
            speed = -1
            bMatched_flag = False

            day_of_week_flag = 0
            day_of_year = 0
            global_time = g_measurement_tstamp_parser(measurement_tstamp, day_of_week_flag, day_of_year)

            speed = df_reading.loc[i, "speed"]
            reference_speed = df_reading.loc[i, "reference_speed"]

            volume_pl = df_reading.loc[i, "volume_pl"] if "volume_pl" in df_reading.columns else -1
            road_name = df_reading.loc[i, "ROADNAME"] if "ROADNAME" in df_reading.columns else ""

            if tmc not in self.assignment.m_TMClink_map:
                tmc_link = TMCLink()
                tmc_link.tmc_code = tmc
                self.assignment.m_TMClink_map[tmc] = len(self.g_TMC_vector)
                self.g_TMC_vector.append(tmc_link)

            index = self.assignment.m_TMClink_map[tmc]
            self.g_TMC_vector[index].add_speed_sensor_data(day_of_year, global_time, speed, volume_pl)
        print("Reading.csv loaded...\n")

    @func_running_time
    def generate_node_csv(self, isSave2csv=True) -> pd.DataFrame:

        # generate Node.csv
        node_result_list = []

        for corridor_name in self.g_tmc_corridor_vector:
            tmc_corridor_info = self.g_tmc_corridor_vector[corridor_name]
            tmc_corridor_info.find_center_and_origin()

            if len(tmc_corridor_info.point_vector) <= 5:
                continue

            for k in range(len(tmc_corridor_info.point_vector)):
                i = tmc_corridor_info.point_vector[k].node_no
                if self.g_node_vector[i].node_id > 0:
                    node_result_list.append([
                        self.g_node_vector[i].node_id,
                        self.g_node_vector[i].node_seq_no,
                        self.g_node_vector[i].layer_no,
                        self.g_node_vector[i].agent_id,
                        k,
                        tmc_corridor_info.point_vector[k].distance_from_origin,
                        self.g_node_vector[i].MRM_gate_flag,
                        self.g_node_vector[i].node_type,
                        self.g_node_vector[i].is_boundary,
                        len(self.g_node_vector[i].m_outgoing_link_seq_no_vector),
                        self.g_node_vector[i].is_activity_node,
                        self.g_node_vector[i].agent_type_str,

                        self.g_node_vector[i].zone_org_id,
                        self.g_node_vector[i].cell_str,
                        0,
                        self.g_node_vector[i].x,
                        self.g_node_vector[i].y
                    ])

        df_node = pd.DataFrame(node_result_list, columns=self.node_col_name)
        if isSave2csv:
            df_node.to_csv(validate_filename(generate_absolute_path(file_name="Node.csv")), index=False)
            print("Successfully saved Node.csv to cbi_results/Node.csv \n")

        return df_node

    @func_running_time
    def generate_link_csv(self, isSave2csv=True) -> pd.DataFrame:

        # Generate Link.csv
        link_result_list = []

        for i in range(len(self.g_link_vector)):
            if self.g_link_vector[i].link_type <= -100:
                continue

            if len(self.g_link_vector[i].geometry) > 0:
                geometry_str = self.g_link_vector[i].geometry
            else:
                geometry_str = f"LINESTRING({self.g_node_vector[self.g_link_vector[i].from_node_seq_no].x} {self.g_node_vector[self.g_link_vector[i].from_node_seq_no].y}, {self.g_node_vector[self.g_link_vector[i].to_node_seq_no].x} {self.g_node_vector[self.g_link_vector[i].to_node_seq_no].y})"

            link_result_list.append([
                self.g_link_vector[i].link_id,
                self.g_link_vector[i].link_seq_no,
                self.g_link_vector[i].layer_no,
                self.g_node_vector[self.g_link_vector[i].from_node_seq_no].node_id,
                self.g_node_vector[self.g_link_vector[i].to_node_seq_no].node_id,
                self.g_node_vector[self.g_link_vector[i].from_node_seq_no].MRM_gate_flag,
                self.g_node_vector[self.g_link_vector[i].to_node_seq_no].MRM_gate_flag,
                self.g_link_vector[i].link_type,
                self.g_link_vector[i].link_type_name,
                self.g_link_vector[i].number_of_lanes,
                self.g_link_vector[i].link_distance_VDF,
                self.g_link_vector[i].free_speed,
                self.g_link_vector[i].v_congestion_cutoff,
                self.g_link_vector[i].free_flow_travel_time_in_min,
                self.g_link_vector[i].lane_capacity,
                # g_link_vector[i].VDF_period[0].allowed_uses,
                "all",
                self.g_link_vector[i].VDF_period[0].peak_load_factor,
                self.g_link_vector[i].VDF_period[0].alpha,
                self.g_link_vector[i].VDF_period[0].beta,

                self.g_link_vector[i].VDF_period[0].peak_load_factor,
                self.g_link_vector[i].VDF_period[0].Q_alpha,
                self.g_link_vector[i].VDF_period[0].Q_beta,
                self.g_link_vector[i].VDF_period[0].Q_cd,
                self.g_link_vector[i].VDF_period[0].Q_n,
                geometry_str
            ])

        df_link = pd.DataFrame(link_result_list, columns=self.link_col_name)

        if isSave2csv:
            df_link.to_csv(validate_filename(generate_absolute_path(file_name="Link.csv")), index=False)
            print("Successfully saved Link.csv to cbi_results/Link.csv \n")

        return df_link

    @func_running_time
    def generate_cbi_summary_csv(self, isSave2csv=True) -> pd.DataFrame:
        # initialize the empty list to store cbi summary result
        link_cbi_summary_result_list = []

        # initialize the empty dictionary
        TMC_long_id_mapping = {}

        # ignored the column name from source code, generate data directly

        # sort data records
        for i in range(len(self.g_link_vector)):
            if len(self.g_link_vector[i].tmc_code) > 0:
                TMC_long_key = (self.g_link_vector[i].tmc_corridor_id * 10000 +
                                self.g_link_vector[i].tmc_road_sequence) * 10 + self.g_link_vector[i].link_seq_no

                TMC_long_id_mapping[TMC_long_key] = self.g_link_vector[i].link_seq_no

        for tmc_long_key in TMC_long_id_mapping:
            i = TMC_long_id_mapping[tmc_long_key]

            highest_speed = self.g_link_vector[i].free_speed

            if self.g_link_vector[i].tmc_code in self.assignment.m_TMClink_map:
                tmc_index = self.assignment.m_TMClink_map[self.g_link_vector[i].tmc_code]

                if not self.g_TMC_vector[tmc_index].b_with_sensor_speed_data:
                    continue

                highest_speed = self.g_TMC_vector[tmc_index].get_highest_speed()
            else:
                continue

            free_speed = self.g_link_vector[i].free_speed

            if self.g_link_vector[i].lane_capacity > 5000:
                continue

            self.g_link_vector[i].update_kc(self.g_link_vector[i].free_speed)

            cbi_result_1 = [
                self.g_link_vector[i].link_id,
                self.g_link_vector[i].tmc_code,
                self.g_link_vector[i].tmc_corridor_name,
                self.g_link_vector[i].tmc_corridor_id,
                self.g_link_vector[i].tmc_road_order,
                self.g_link_vector[i].tmc_road_sequence,
                self.g_link_vector[i].tmc_road,
                self.g_link_vector[i].tmc_direction,
                self.g_link_vector[i].tmc_intersection,
                highest_speed,
                self.g_link_vector[i].link_seq_no,
                self.g_node_vector[self.g_link_vector[i].from_node_seq_no].node_id,
                self.g_node_vector[self.g_link_vector[i].to_node_seq_no].node_id,
                self.g_link_vector[i].link_type,
                self.g_link_vector[i].link_type_code,
                self.g_link_vector[i].FT,
                self.g_link_vector[i].AT,
                self.g_link_vector[i].vdf_code,
                self.g_link_vector[i].number_of_lanes,
                self.g_link_vector[i].link_distance_VDF,
                self.g_link_vector[i].free_speed,
                self.g_link_vector[i].lane_capacity,
                self.g_link_vector[i].k_critical,
                self.g_link_vector[i].v_congestion_cutoff
            ]

            if self.g_link_vector[i].tmc_code in self.assignment.m_TMClink_map:
                tmc_index = self.assignment.m_TMClink_map[self.g_link_vector[i].tmc_code]
                highest_speed = 0

                p_link = self.g_link_vector[i]

                updated_vc = self.g_TMC_vector[tmc_index].scan_highest_speed_and_vc(
                    p_link.free_speed, highest_speed)

                for time_index in range(MAX_TIME_INTERVAL_PER_DAY):
                    p_link.model_speed[time_index] = p_link.free_speed

                p_link.v_congestion_cutoff = updated_vc
                p_link.update_kc(free_speed)

                cbi_result_2 = [
                    highest_speed,
                    p_link.v_congestion_cutoff,
                    p_link.v_congestion_cutoff / max(1, highest_speed),
                    p_link.v_critical
                ]

                # generate 0-24 hours list
                analysis_hour_flag = [0] * 25

                cbi_result_3 = []
                for tau in range(min(3, len(self.assignment.g_DemandPeriodVector))):
                    assign_period_start_time_in_hour = self.assignment.g_DemandPeriodVector[
                        tau].starting_time_slot_no * MIN_PER_TIME_SLOT / 60.0
                    assign_period_end_time_in_hour = self.assignment.g_DemandPeriodVector[
                        tau].ending_time_slot_no * MIN_PER_TIME_SLOT / 60.0
                    assign_period_t2_peak_in_hour = self.assignment.g_DemandPeriodVector[
                        tau].t2_peak_in_hour

                    for hour in range(int(assign_period_start_time_in_hour), int(assign_period_end_time_in_hour)):
                        analysis_hour_flag[hour] = 1

                    obs_t0_in_hour = 0
                    obs_t3_in_hour = 0
                    obs_P = 0

                    V = D = VOC_ratio = DOC_ratio = 0

                    peak_hour_volume = 0
                    mean_speed_BPR = 0
                    mean_speed_QVDF = 0
                    t2_speed = 0

                    plf = 1
                    Q_n = Q_s = Q_cd = Q_cp = 1
                    outside_time_margin_in_hour = 1

                    obs_P = self.g_TMC_vector[tmc_index].scan_congestion_duration(
                        tau,
                        assign_period_start_time_in_hour,
                        assign_period_end_time_in_hour,
                        outside_time_margin_in_hour,
                        assign_period_t2_peak_in_hour,
                        p_link.v_congestion_cutoff,
                        p_link,
                        obs_t0_in_hour,
                        obs_t3_in_hour,
                        obs_P,
                        V,
                        peak_hour_volume,
                        D,
                        VOC_ratio,
                        DOC_ratio,
                        mean_speed_BPR,
                        mean_speed_QVDF,
                        highest_speed,
                        t2_speed,
                        plf,
                        #Q_n, Q_s, Q_cd, Q_cp
                    )

                    Q_alpha = 8 / 15 * Q_cp * math.pow(Q_cd, Q_s)
                    Q_beta = Q_n * Q_s

                    Q_alpha = self.g_TMC_vector[tmc_index].check_feasible_range(
                        Q_alpha, 0.27, 0.01, 1)
                    Q_beta = self.g_TMC_vector[tmc_index].check_feasible_range(
                        Q_beta, 1.14, 0.5, 5)

                    if p_link.link_id == "201065AB":
                        idebug = 1

                    p_link.VDF_period[tau].sa_volume = V * p_link.number_of_lanes
                    p_link.VDF_period[tau].peak_load_factor = plf
                    p_link.VDF_period[tau].v_congestion_cutoff = p_link.v_congestion_cutoff
                    p_link.VDF_period[tau].Q_alpha = Q_alpha
                    p_link.VDF_period[tau].Q_beta = Q_beta
                    p_link.VDF_period[tau].Q_cd = Q_cd
                    p_link.VDF_period[tau].Q_n = Q_n
                    p_link.VDF_period[tau].Q_cp = Q_cp
                    p_link.VDF_period[tau].Q_s = Q_s

                    p_link.free_speed = highest_speed
                    p_link.VDF_period[tau].vf = highest_speed

                    p_link.calculate_dynamic_VDFunction(self.assignment, 0, False, p_link.vdf_type)

                    speed_reduction_factor = 0
                    if (obs_P > 0.25) and (t2_speed < p_link.v_congestion_cutoff):
                        speed_reduction_factor = p_link.v_congestion_cutoff / \
                            max(1, t2_speed) - 1

                    queue_vc_delay_index = p_link.v_congestion_cutoff / \
                        max(1, mean_speed_QVDF) - 1
                    if queue_vc_delay_index < 0:
                        queue_vc_delay_index = 0

                    BPR_vf_delay_index = max(highest_speed, float(
                        p_link.free_speed)) / max(1, mean_speed_BPR) - 1
                    if BPR_vf_delay_index < 0:
                        BPR_vf_delay_index = 0

                    log_VOC = log_DOC = log_P = log_sf = log_vfdi = log_vcdi = 0
                    if DOC_ratio > 0.00001:
                        log_DOC = math.log(DOC_ratio)
                        log_VOC = math.log(VOC_ratio)

                    if obs_P > 0.00001:
                        log_P = math.log(obs_P)

                    if speed_reduction_factor > 0.00001:
                        log_sf = math.log(speed_reduction_factor)

                    if BPR_vf_delay_index > 0.00001:
                        log_vfdi = math.log(BPR_vf_delay_index)

                    if queue_vc_delay_index > 0.00001:
                        log_vcdi = math.log(queue_vc_delay_index)

                    cbi_result_3.extend([
                        obs_t0_in_hour,
                        obs_t3_in_hour,
                        V,
                        peak_hour_volume,
                        D,
                        VOC_ratio,
                        DOC_ratio,
                        obs_P,
                        speed_reduction_factor,
                        BPR_vf_delay_index,
                        queue_vc_delay_index,
                        mean_speed_BPR,
                        mean_speed_QVDF,
                        t2_speed,
                        plf,
                        Q_n,
                        Q_cp,
                        Q_alpha,
                        Q_beta,
                        self.g_link_vector[i].VDF_period[tau].link_volume,
                        self.g_link_vector[i].VDF_period[tau].lane_based_D,
                        self.g_link_vector[i].VDF_period[tau].DOC,
                        self.g_link_vector[i].VDF_period[tau].P,
                        self.g_link_vector[i].VDF_period[tau].avg_queue_speed,
                        self.g_link_vector[i].VDF_period[tau].vt2,
                        self.g_link_vector[i].VDF_period[tau].Q_mu,
                        self.g_link_vector[i].VDF_period[tau].Q_gamma,
                        self.g_link_vector[i].VDF_period[tau].lane_based_Vph,
                        self.g_link_vector[i].VDF_period[tau].VOC,
                        self.g_link_vector[i].VDF_period[tau].avg_speed_BPR,
                    ])
                cbi_result_3.extend(
                    [str(self.g_link_vector[i].geometry),
                    f"LINESTRING({self.g_link_vector[i].TMC_from.x} {self.g_link_vector[i].TMC_from.y},{self.g_link_vector[i].TMC_to.x} {self.g_link_vector[i].TMC_to.x})"]
                )

                if self.g_link_vector[i].tmc_code in self.assignment.m_TMClink_map:
                    tmc_index = self.assignment.m_TMClink_map[self.g_link_vector[i].tmc_code]

                    count_total = 0
                    MAE_total = 0
                    MAPE_total = 0
                    RMSE_total = 0

                    ObsSpeed = [0] * 25
                    EstSpeed = [0] * 25
                    EstSpeedDiff = [0] * 25

                    for t in range(6 * 60, 20 * 60, 60):
                        hour = int(t / 60)

                        # return data from index 6 to 20
                        ObsSpeed[hour] = self.g_TMC_vector[tmc_index].get_avg_hourly_speed(t)

                        # return data from index 6 to 20
                        model_speed = self.g_link_vector[i].get_model_hourly_speed(t)
                        EstSpeed[hour] = model_speed

                        if EstSpeed[hour] > 1 and ObsSpeed[hour] > 1 and analysis_hour_flag[hour] == 1:
                            EstSpeedDiff.append(
                                math.fabs(EstSpeed[hour] - ObsSpeed[hour]))
                            MAE_total += math.fabs(EstSpeedDiff[hour])
                            MAPE_total += math.fabs(
                                EstSpeedDiff[hour] / max(1, ObsSpeed[hour]))
                            RMSE_total += EstSpeedDiff[hour] * \
                                EstSpeedDiff[hour]
                            count_total += 1
                        else:
                            EstSpeedDiff.append(0)

                    MSE_total = RMSE_total / max(1, count_total)

                    cbi_result_4 = ObsSpeed[6:20] + EstSpeed[6:20] + [
                        MAE_total / max(1, count_total),
                        MAPE_total / max(1, count_total) * 100,
                        math.pow(MSE_total, 0.5)
                    ]

                    cbi_result_5_volume = [self.g_TMC_vector[tmc_index].get_avg_hourly_volume(
                        t) for t in range(6 * 60, 20 * 60, 60)]

                    cbi_result_6_speed_ratio = []
                    for t in range(6 * 60, 20 * 60, 60):
                        hour = int(t / 60)
                        speed_ratio = ObsSpeed[hour] / max(1, self.g_link_vector[i].TMC_highest_speed)
                        if speed_ratio > 1:
                            speed_ratio = 1
                        cbi_result_6_speed_ratio.append(speed_ratio)

                    cbi_result_7 = [self.g_TMC_vector[tmc_index].get_avg_speed(
                        t) for t in range(6 * 60, 20 * 60, 5)]

                    cbi_result_8 = [self.g_link_vector[i].get_model_5_min_speed(
                        t) for t in range(6 * 60, 20 * 60, 5)]
                    cbi_result_9 = [self.g_TMC_vector[tmc_index].get_avg_speed(
                        t) for t in range(6 * 60, 20 * 60, 15)]
                    cbi_result_10 = [self.g_link_vector[i].get_model_15_min_speed(
                        t) for t in range(6 * 60, 20 * 60, 15)]

                    cbi_result_11 = []
                    for t in range(6 * 60, 20 * 60, 5):
                        speed = self.g_TMC_vector[tmc_index].get_avg_speed(t)
                        volume = self.g_TMC_vector[tmc_index].get_avg_volume(
                            t, self.g_link_vector[i], speed, self.g_link_vector[i].TMC_highest_speed)
                        cbi_result_11.append(volume * 12)

                    link_cbi_summary_result_list.append(
                        cbi_result_1 + cbi_result_2 + cbi_result_3 + cbi_result_4 + cbi_result_5_volume + cbi_result_6_speed_ratio + cbi_result_7 + cbi_result_8 + cbi_result_9 + cbi_result_10 + cbi_result_11)
                else:
                    link_cbi_summary_result_list.append(cbi_result_1 + cbi_result_2 + cbi_result_3)
            else:
                link_cbi_summary_result_list.append(cbi_result_1)

        df_cbi_summary = pd.DataFrame(link_cbi_summary_result_list, columns=self.cbi_summary_col_name)

        if isSave2csv:
            df_cbi_summary.to_csv(validate_filename(generate_absolute_path(file_name="cbi_summary.csv")), index=False)
            print("Successfully saved Link.csv to cbi_results/cbi_summary.csv \n")


        return df_cbi_summary

    @func_running_time
    def generate_link_qvdf_csv(self, isSave2csv=True) -> pd.DataFrame:
        # initialize the empty list to store cbi summary result
        qvdf_result_list = []

        # initialize the empty dictionary
        TMC_long_id_mapping = {}

        # ignored the column name from source code, generate data directly
        # sort data records
        for i in range(len(self.g_link_vector)):
            if len(self.g_link_vector[i].tmc_code) > 0:
                TMC_long_key = (self.g_link_vector[i].tmc_corridor_id * 10000 +
                                self.g_link_vector[i].tmc_road_sequence) * 10 + self.g_link_vector[i].link_seq_no

                TMC_long_id_mapping[TMC_long_key] = self.g_link_vector[i].link_seq_no

        for tmc_long_key in TMC_long_id_mapping:
            i = TMC_long_id_mapping[tmc_long_key]

            highest_speed = self.g_link_vector[i].free_speed

            if self.g_link_vector[i].tmc_code in self.assignment.m_TMClink_map:
                tmc_index = self.assignment.m_TMClink_map[self.g_link_vector[i].tmc_code]

                if not self.g_TMC_vector[tmc_index].b_with_sensor_speed_data:
                    continue

                highest_speed = self.g_TMC_vector[tmc_index].get_highest_speed(
                )
            else:
                continue

            free_speed = self.g_link_vector[i].free_speed

            if self.g_link_vector[i].lane_capacity > 5000:
                continue

            self.g_link_vector[i].update_kc(self.g_link_vector[i].free_speed)

            qvdf_result_1 = [
                "link",
                self.g_link_vector[i].link_id,
                self.g_link_vector[i].tmc_corridor_name,
                self.g_node_vector[self.g_link_vector[i].from_node_seq_no].node_id,
                self.g_node_vector[self.g_link_vector[i].to_node_seq_no].node_id,
                self.g_link_vector[i].vdf_code
            ]

            if self.g_link_vector[i].tmc_code in self.assignment.m_TMClink_map:
                tmc_index = self.assignment.m_TMClink_map[self.g_link_vector[i].tmc_code]
                highest_speed = 0

                p_link = self.g_link_vector[i]

                updated_vc = self.g_TMC_vector[tmc_index].scan_highest_speed_and_vc(
                    p_link.free_speed, highest_speed)

                for time_index in range(MAX_TIME_INTERVAL_PER_DAY):
                    p_link.model_speed[time_index] = p_link.free_speed

                p_link.v_congestion_cutoff = updated_vc
                p_link.update_kc(free_speed)


                qvdf_result_2 = []
                for tau in range(min(3, len(self.assignment.g_DemandPeriodVector))):
                    assign_period_start_time_in_hour = self.assignment.g_DemandPeriodVector[
                        tau].starting_time_slot_no * MIN_PER_TIME_SLOT / 60.0
                    assign_period_end_time_in_hour = self.assignment.g_DemandPeriodVector[
                        tau].ending_time_slot_no * MIN_PER_TIME_SLOT / 60.0
                    assign_period_t2_peak_in_hour = self.assignment.g_DemandPeriodVector[
                        tau].t2_peak_in_hour

                    obs_t0_in_hour = 0
                    obs_t3_in_hour = 0
                    obs_P = 0

                    V = D = VOC_ratio = DOC_ratio = 0

                    peak_hour_volume = 0
                    mean_speed_BPR = 0
                    mean_speed_QVDF = 0
                    t2_speed = 0

                    plf = 1
                    Q_n = Q_s = Q_cd = Q_cp = 1
                    outside_time_margin_in_hour = 1

                    obs_P = self.g_TMC_vector[tmc_index].scan_congestion_duration(
                        tau,
                        assign_period_start_time_in_hour,
                        assign_period_end_time_in_hour,
                        outside_time_margin_in_hour,
                        assign_period_t2_peak_in_hour,
                        p_link.v_congestion_cutoff,
                        p_link,
                        obs_t0_in_hour,
                        obs_t3_in_hour,
                        obs_P,
                        V,
                        peak_hour_volume,
                        D,
                        VOC_ratio,
                        DOC_ratio,
                        mean_speed_BPR,
                        mean_speed_QVDF,
                        highest_speed,
                        t2_speed,
                        plf,
                        #Q_n, Q_s, Q_cd, Q_cp
                    )

                    Q_alpha = 8 / 15 * Q_cp * math.pow(Q_cd, Q_s)
                    Q_beta = Q_n * Q_s

                    Q_alpha = self.g_TMC_vector[tmc_index].check_feasible_range(
                        Q_alpha, 0.27, 0.01, 1)
                    Q_beta = self.g_TMC_vector[tmc_index].check_feasible_range(
                        Q_beta, 1.14, 0.5, 5)

                    p_link.VDF_period[tau].Q_alpha = Q_alpha
                    p_link.VDF_period[tau].Q_beta = Q_beta
                    p_link.VDF_period[tau].Q_cd = Q_cd
                    p_link.VDF_period[tau].Q_n = Q_n
                    p_link.VDF_period[tau].Q_cp = Q_cp
                    p_link.VDF_period[tau].Q_s = Q_s

                    if len(p_link.vdf_code) > 1:
                        self.g_vdf_type_map[p_link.vdf_code].record_qvdf_data(p_link.VDF_period[tau], tau)

                    # self.g_vdf_type_map["all"].record_qvdf_data(p_link.VDF_period[tau], tau)

                    qvdf_result_2.extend([
                        plf, Q_n, Q_s, Q_cp, Q_cd, Q_alpha, Q_beta
                    ])

                qvdf_result_list.append(qvdf_result_1 + qvdf_result_2)

            else:
                qvdf_result_list.append(qvdf_result_1)

        for key in self.g_vdf_type_map:
            qvdf_result_3 = []
            for tau in range(min(3, len(self.assignment.g_DemandPeriodVector))):
                self.g_vdf_type_map[key].computer_avg_parameter(tau)
                qvdf_result_3.extend([
                    self.g_vdf_type_map[key].VDF_period_sum[tau].peak_load_factor,
                    self.g_vdf_type_map[key].VDF_period_sum[tau].Q_n,
                    self.g_vdf_type_map[key].VDF_period_sum[tau].Q_s,
                    self.g_vdf_type_map[key].VDF_period_sum[tau].Q_cp,
                    self.g_vdf_type_map[key].VDF_period_sum[tau].Q_cd,
                    self.g_vdf_type_map[key].VDF_period_sum[tau].Q_alpha,
                    self.g_vdf_type_map[key].VDF_period_sum[tau].Q_beta
                ])

            qvdf_result_list.append(
                ["vdf_code","","","","", key] + qvdf_result_3
            )

        df_qvdf = pd.DataFrame(qvdf_result_list, columns = self.link_qvdf_col_name)

        if isSave2csv:
            df_qvdf.to_csv(validate_filename(generate_absolute_path(file_name="link_qvdf.csv")), index=False)
            print("Successfully saved Link.csv to cbi_results/link_qvdf.csv \n")

        return df_qvdf

    def cbi_execution(self):

        print("Step 1: read settings.yaml data\n")
        self.read_settings_yaml_file()

        print("Step 2: read tmc_identification.csv data\n")
        self.read_tmc_identification_csv_file()

        print("Step 3: read Reading.csv data\n")
        self.read_Readings_csv_file()

        print("Step 4: generate node.csv data\n")
        self.generate_node_csv(isSave2csv=True)

        print("Step 5: generate link.csv data\n")
        self.generate_link_csv(isSave2csv=True)

        print("Step 6: generate cbi_summary.csv data\n")
        self.generate_cbi_summary_csv(isSave2csv=True)

        print("Step 7: generate link_qvdf.csv data\n")
        self.generate_link_qvdf_csv(isSave2csv=True)


if __name__ == "__main__":
    # define the path of input folder
    path_input_folder = "./data_input"

    # create an instance of CBI_TOOL
    cbi = CBI_TOOL(path_input_folder)

    # execute the CBI_TOOL
    cbi.cbi_execution()
