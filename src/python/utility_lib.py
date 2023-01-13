# -*- coding:utf-8 -*-
##############################################################
# Created Date: Thursday, December 1st 2022
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

# values in dictionary are features required by the function
required_input_file_dict = {
    "settings.yml": {"link_type", "link_type_name", "agent_type_blocklist", "type_code", "traffic_flow_code"},
    "Reading.csv": {"tmc_code", "measurement_tstamp", "speed", "average_speed", "reference_speed", "travel_time_seconds", "confidence_score", "cvalue"},
    "TMC_Identification.csv": {"tmc", "road", "direction", "intersection",
                               "state", "county", "zip", "start_latitude",
                               "start_longitude", "end_latitude", "end_longitude",
                               "miles", "road_order", "timezone_name", "type",
                               "country", "active_start_date", "active_end_date"}}