# -*- coding:utf-8 -*-
##############################################################
# Created Date: Friday, December 2nd 2022
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################


import math
from enum import Enum
import datetime
import pandas as pd

from DTA import Link


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


class TMCLink:

    def __init__(self):

        self.b_with_sensor_speed_data = False

        self.speed_sum = [0 for _ in range(MAX_TIME_INTERVAL_PER_DAY)]
        self.avg_speed = [0 for _ in range(MAX_TIME_INTERVAL_PER_DAY)]
        self.speed_lowest = [0 for _ in range(MAX_TIME_INTERVAL_PER_DAY)]

        self.volume_sum = [0 for _ in range(MAX_TIME_INTERVAL_PER_DAY)]
        self.avg_volume = [0 for _ in range(MAX_TIME_INTERVAL_PER_DAY)]

        self.b_volume_data_available_flag = [False for _ in range(MAX_TIME_INTERVAL_PER_DAY)]
        self.speed_count = [0 for _ in range(MAX_TIME_INTERVAL_PER_DAY)]
        self.volume_count = [0 for _ in range(MAX_TIME_INTERVAL_PER_DAY)]

        self.volume_per_hour_per_lane = [0 for _ in range(MAX_TIME_INTERVAL_PER_DAY)]

        self.tmc_code = ""
        self.matching_link_no = 0
        self.reference_speed = 0

    def record_avg_speed(self, time_in_min: int) -> float:
        t = int(time_in_min / 5)

        if self.speed_count[t] == 0:
            return -1

        if t >= 0 and t < MAX_TIME_INTERVAL_PER_DAY:
            self.avg_speed[t] = self.speed_sum[t] / max(1.0, self.speed_count[t])  # avoid zero division
            return self.avg_speed[t]
        return -1

    def get_avg_speed(self, time_in_min: int) -> float:
        t = int(time_in_min / 5)
        if t >= 0 and t < MAX_TIME_INTERVAL_PER_DAY:
            return self.avg_speed[t] / max(1.0, self.speed_count[t])  # avoid zero division
        return -1

    def get_highest_speed(self) -> float:

        highest_speed = 0

        for t_in_min in range(6 * 60, 20 * 60, 5):
            avg_speed = self.record_avg_speed(t_in_min)

            if avg_speed > highest_speed:
                highest_speed = avg_speed

        return highest_speed

    def scan_highest_speed_and_vc(self, free_speed: float, highest_speed: float = 0) -> float:
        for t_in_min in range(6 * 60, 20 * 60, 5):
            avg_speed = self.record_avg_speed(t_in_min)

            if avg_speed > highest_speed:
                highest_speed = avg_speed

        vf = highest_speed
        return vf * 0.7 / max(1.0, vf) * vf

    def check_feasible_range(self, input_value: float, default_value: float, lower_bound: float, upper_bound: float) -> float:

        if (input_value < lower_bound) or (input_value > upper_bound):
            return default_value

        return input_value

    def add_speed_sensor_data(self, day_no: int, time_in_min: int, speed_value: float, volume_pl_value: float):
        self.b_with_sensor_speed_data = True
        t = math.trunc(time_in_min / float(5))

        if (t >= 0) and (t < MAX_TIME_INTERVAL_PER_DAY):
            self.speed_sum[t] += speed_value
            self.speed_count[t] += 1

            if speed_value < self.speed_lowest[t]:
                self.speed_lowest[t] = speed_value

            if volume_pl_value >= 0:
                self.b_volume_data_available_flag[t] = True
                self.volume_sum[t] += volume_pl_value
                self.volume_count[t] += 1

    def get_avg_volume(self, time_in_min: int, p_link: Link, avg_speed: float, highest_speed: float) -> float:
        t = math.trunc(time_in_min / float(5))

        if self.volume_count[t] > 0 and t >= 0 and t < MAX_TIME_INTERVAL_PER_DAY:
            # 5 min to hourly volume
            return self.volume_sum[t] / max(1.0, self.volume_count[t]) * 12
        else:  # default
            return p_link.get_volume_from_speed(avg_speed, highest_speed, p_link.lane_capacity)

    def get_avg_speed_15min(self, time_in_min: int) -> float:
        t = math.trunc(time_in_min / float(5))

        total_speed_value = 0
        total_speed_count = 0

        for tt in range(3):

            if t + tt >= 0 and t + tt < MAX_TIME_INTERVAL_PER_DAY:
                total_speed_value += self.speed_sum[t + tt] / max(1.0, self.speed_count[t + tt])
                total_speed_count += 1
        return total_speed_value / max(1, total_speed_count)

    def get_avg_hourly_speed(self, time_in_min: int) -> float:
        t = math.trunc(time_in_min / float(5))

        total_speed_value = 0
        total_speed_count = 0

        for tt in range(12):

            if t + tt >= 0 and t + tt < MAX_TIME_INTERVAL_PER_DAY:
                total_speed_value += self.speed_sum[t + tt] / max(1.0, self.speed_count[t + tt])
                total_speed_count += 1

        return total_speed_value / max(1, total_speed_count)

    def get_avg_hourly_volume(self, time_in_min: int) -> float:
        t = math.trunc(time_in_min / float(5))

        total_volume_value = 0
        total_volume_count = 0

        for tt in range(12):

            if t + tt >= 0 and t + tt < MAX_TIME_INTERVAL_PER_DAY:
                total_volume_value += self.volume_sum[t + tt] / max(1.0, self.volume_count[t + tt])
                total_volume_count += 1

        return total_volume_value

    def get_lowest_speed(self, time_in_min: int) -> float:
        t = math.trunc(time_in_min / float(5))
        if t >= 0 and t < MAX_TIME_INTERVAL_PER_DAY:

            return self.speed_lowest[t]

    def scan_congestion_duration(self, peak_no, starting_time_in_hour, ending_time_in_hour, outside_time_margin_in_hour, assign_period_t2_peak_in_hour, FD_vcutoff, p_link, obs_t0_in_hour, obs_t3_in_hour, obs_P_in_hour, V, peak_hour_volume, D, VOC_ratio, DOC_ratio, mean_speed_BPR, mean_speed_QVDF, highest_speed, t2_speed, plf):

        Q_n = 1.24
        Q_s = 4
        Q_cd = 1
        Q_cp = 0.24

        obs_t0_in_hour = -1
        obs_t3_in_hour = -1
        obs_P_in_hour = 0
        V = 0

        D = 0
        DOC_ratio = 0
        VOC_ratio = 0
        mean_speed_BPR = 0
        mean_speed_QVDF = 0
        highest_speed = 0

        obs_t0_in_interval = -1
        obs_t3_in_interval = -1
        obs_ts_in_interval = int(starting_time_in_hour * 12)
        obs_te_in_interval = int(ending_time_in_hour * 12)

        L = ending_time_in_hour - starting_time_in_hour
        plf = 1.0

        total_speed_value = 0
        total_speed_count = 0

        # step 1: record highest speed
        for t_in_min in range(6 * 60, 20 * 60, 5):

            avg_speed = self.record_avg_speed(t_in_min)

            if avg_speed > highest_speed:
                highest_speed = avg_speed

        t_mid = int(assign_period_t2_peak_in_hour * 12)

        V = 0

        t_lowest_speed = -1
        lowest_speed = 99999
        t2_speed = self.avg_speed[t_mid]

        if self.avg_speed[t_mid] < 0:
            return 0

        if self.avg_speed[t_mid] > 0:
            t_in_min = max(6, starting_time_in_hour) * 60
            while t_in_min < min(20, ending_time_in_hour) * 60:

                avg_speed = self.record_avg_speed(t_in_min)
                volume = self.get_avg_volume(
                    t_in_min, p_link, avg_speed, highest_speed)
                V += volume / 12  # 12 5-min interval per hour

                if avg_speed < lowest_speed:
                    t_lowest_speed = math.trunc(t_in_min / float(5))
                    lowest_speed = avg_speed
                t_in_min += 5

        b_t0_found_flag = False
        b_t3_found_flag = False

        # step 5:
        # exit if the speed is higher than v_congestion_cutoff
        if self.avg_speed[t_mid] < FD_vcutoff:
            obs_t3_in_interval = t_mid
            obs_t3_in_hour = t_mid * 1.0 / 12.0
            b_t3_found_flag = True

            obs_t0_in_interval = t_mid
            b_t0_found_flag = True
            obs_t0_in_hour = t_mid * 1.0 / 12.0

        for t in range(t_mid + 1, obs_te_in_interval + 1):
            # move forward from mid t
            if self.avg_speed[t] < 1:
                i_no_data = 1
                break

            # exit if the speed is higher than v_congestion_cutoff
            if self.avg_speed[t] > FD_vcutoff:
                break

            obs_t3_in_interval = t
            obs_t3_in_hour = t * 1.0 / 12.0
            b_t3_found_flag = True

        for t in range(t_mid - 1, obs_ts_in_interval - 1, -1):
            # move backward from t_mid
            if self.avg_speed[t] < 1:
                i_no_data = 1
                break
            if self.avg_speed[t] > FD_vcutoff:
                break

            obs_t0_in_interval = t
            b_t0_found_flag = True
            obs_t0_in_hour = t * 1.0 / 12.0

        # consider peak hour
        # - 30 min
        peak_hour_t0_in_interval = int(t_mid - 60 / 2 / 5)
        peak_hour_t3_in_interval = int(t_mid + 60 / 2 / 5)  # + 30 min

        total_speed_count = 0  # initial values
        total_speed_value = 0

        obs_P_in_hour = 0  # no compromise
        D = 0
        DOC_ratio = 0

        peak_hour_volume = 0

        if p_link.link_id == "201102BA":
            debug_flag = 1

        # consider volume in peak hour
        # move between congestion duration per interval
        for t in range(peak_hour_t0_in_interval, peak_hour_t3_in_interval):
            if self.avg_speed[t] >= 1:
                total_speed_value += self.avg_speed[t]
                volume = self.get_avg_volume(
                    t, p_link, self.avg_speed[t], highest_speed)

                if volume < 0:
                    idebug = 1
                    self.get_avg_volume(
                        t, p_link, self.avg_speed[t], highest_speed)
                peak_hour_volume += volume / 12  # 12 5-min interval per hour
                total_speed_count += 1

        mean_speed_BPR = total_speed_value / \
            max(1.0, total_speed_count)

        plf = min(1, V / max(1.0, L) /
                            max(1.0, peak_hour_volume))
        # unit: demand: # of vehicles, lane_capacity # of vehicles per hours: dc ratio has a unit of hour, but it is different from P
        VOC_ratio = peak_hour_volume / \
            max(1.0, p_link.lane_capacity)

        mean_speed_QVDF = FD_vcutoff

        if b_t0_found_flag == False and b_t3_found_flag == True:
            obs_t0_in_hour = assign_period_t2_peak_in_hour
            b_t0_found_flag = True  # reset

        if b_t0_found_flag == True and b_t3_found_flag == False:
            obs_t3_in_hour = assign_period_t2_peak_in_hour
            b_t3_found_flag = True

        if b_t0_found_flag == False or b_t3_found_flag == False:  # two boundaries are not found or P < 1;

            # - 30 min
            obs_t0_in_interval = int(t_mid - 60 / 2 / 5)
            obs_t3_in_interval = int(t_mid + 60 / 2 / 5)  # + 30 min

            obs_P_in_hour = 0 # no compromise
            D = 0
            DOC_ratio = 0

        else:
            D = 0
            total_speed_count = 0 # initial values
            total_speed_value = 0
            lowest_speed = FD_vcutoff
            time_int_with_lowest_speed = obs_t0_in_interval

            for t in range(obs_t0_in_interval, obs_t3_in_interval + 1):
                # move between congestion duration per interval
                if self.avg_speed[t] >= 1:
                    total_speed_value += self.avg_speed[t]
                    volume = self.get_avg_volume(t, p_link, self.avg_speed[t], highest_speed)
                    D += volume / 12 # 12 5-min interval per hour
                    total_speed_count += 1

                    if self.avg_speed[t] < lowest_speed:
                        lowest_speed = self.avg_speed[t]
                        time_int_with_lowest_speed = t

            # test
            obs_P_in_hour = (
                obs_t3_in_hour - obs_t0_in_hour)  # congestion duration P

            # unit: demand: # of vehicles, lane_capacity # of vehicles per hours: dc ratio has a unit of hour, but it is different from P
            DOC_ratio = D / max(1.0, p_link.lane_capacity)
            VOC_ratio = max(VOC_ratio, DOC_ratio)

            mean_speed_QVDF = total_speed_value / max(1.0, total_speed_count)

            # if we use a pure second order model, we should consider t2= 2/3(t3-t0)+ t0
            t2_speed = lowest_speed

            if obs_P_in_hour > 2.5:
                idebug = 1
            # calibration

            exact_plf = V / max(1, L) / max(0.001, peak_hour_volume)
            exact_bound = 1.0
            plf = min(exact_bound, exact_plf) # pure plf

            # P = cd * (D/C) ^n  --> log (P) = log(cd) + n *Log (D/C)
            part1 = (math.log(obs_P_in_hour) - math.log(Q_cd))
            part2 = math.log(DOC_ratio)

            if abs(part2) < 0.000001:
                part2 = 0.00001

            Q_n = part1 / part2  # assume Q_cd is fixed at 1 o other values close to 1

            if Q_n < 1.001:
                # default, to ensure the mu is decreasing pattern as a function of D/C
                Q_n = 1.124
                # Cd = P / (D / C) ^ n
                #  Peiheng, 02/22/22, g++ will treat pow(DOC_ratio, Q_n) as double but not clang++
                Q_cd = obs_P_in_hour / max(0.0001, float(DOC_ratio) ** Q_n)

            # vc / vt2 - 1 = cp * (P)^s, --> cp = [ vc/vt2 - 1] / (P^s)  // assume s is fixed
            #  Peiheng, 02/22/22, g++ will treat pow(obs_P_in_hour, Q_s) as double but not clang++
            Q_cp = (FD_vcutoff / max(0.0001, t2_speed) - 1.0) / max(0.00001, float(obs_P_in_hour) ** Q_s)
            # backward derivation

        # modified with Mohammad A. 02/15/2022
        Q_n = self.check_feasible_range(Q_n, 1.24, 1, 1.5)
        Q_s = self.check_feasible_range(Q_s, 1, 0.5, 4)
        Q_cd = self.check_feasible_range(Q_cd, 1, 0.5, 2)
        Q_cp = self.check_feasible_range(Q_cp, 0.2, 0.0, 2)
        largest_DOC_ratio = max(1.0, L)
        DOC_ratio = self.check_feasible_range(DOC_ratio, 0.5, 0.0, largest_DOC_ratio)
        plf = self.check_feasible_range(plf, 1.0, 0.0, 1)

        obs_P_in_hour = self.check_feasible_range(obs_P_in_hour, 0.0, 0.0, 10)
        t2_speed = self.check_feasible_range(t2_speed, FD_vcutoff, 0.0, 200)
        return obs_P_in_hour


def map_tmc_reading(ReadingDataFile: str) -> pd.DataFrame:

    # TDD development
    if not isinstance(ReadingDataFile, str):
        raise TypeError('ReadingDataFile must be a string')

    if ReadingDataFile.split('.')[-1] != 'csv':
        raise TypeError('ReadingDataFile must be a csv file')

    col_names = ["tmc_code", "measurement_tstamp", "speed", "reference_speed"]
    col_names_not_in_file = ["volume_pl", "ROADNAME"]

    df_reading = pd.read_csv(ReadingDataFile)

    #  applied data conversion
    for i in range(len(df_reading)):
        tmc = df_reading.loc[i, "tmc_code"]
        measurement_tstamp = df_reading.loc[i, "measurement_tstamp"]
        speed = df_reading.loc[i, "speed"]
        volume_ppl = df_reading.loc[i, "volume_pl"]
        reference_speed = df_reading.loc[i, "reference_speed"]
        road_name = df_reading.loc[i, "ROADNAME"]

        # index_instance =

        bMatched_flag = False
        day_of_week_flag = 0
        day_of_year = 0
        length_of_measurement_tstamp = len(measurement_tstamp)

        global_time = g_measurement_tstamp_parser(measurement_tstamp, day_of_week_flag, day_of_year)

    # get column existed in file
    df = df[col_names]

    # get column not existed in file and fill with NaN
    for col_name in col_names_not_in_file:
        df[col_name] = None

    return df


def g_day_of_week(year: int, month: int, day: int) -> int:
    return datetime.datetime(year, month, day).timetuple().tm_wday


def g_day_of_year(year: int, month: int, day: int) -> int:
    return datetime.datetime(year, month, day).timetuple().tm_yday


def convert_tstamp_to_iso(time_str: str):
    return pd.to_datetime(time_str).isoformat()


def g_measurement_tstamp_parser(time_str: str, day_of_week_flag: int, day_of_year: int) -> float:

    datetime_time = pd.to_datetime(time_str)
    yyyy = datetime_time.year
    month = datetime_time.month
    day = datetime_time.day

    buf_hh = [0] * 32
    buf_mm = [0] * 32
    buf_ss = [0] * 32

    # day_of_week_flag = g_day_of_week(yyyy, month, day)
    day_of_year = g_day_of_year(yyyy, month, day)

    g_dayDataMap = {}
    g_dayDataMap[day_of_year] = month * 100 + day

    # string_len = len(time_str)
    string_line = time_str
    char_link_distance_VDF = len(string_line)

    global_minute = 0
    dd = hh = mm = 0
    buffer_i = buffer_k = buffer_j = 0
    num_of_colons = 0
    # num_of_underscore = 0
    # char_link_distance_VDF_yymmdd = 10

    i = 11
    while i < char_link_distance_VDF:
        ch = string_line[i]
        i += 1

        if num_of_colons == 0 and ch != "_" and ch != ":":
            buf_hh[buffer_i] = ch
            buffer_i += 1
        elif num_of_colons == 1 and ch != ":":
            buf_mm[buffer_k] = ch
            buffer_k += 1
        elif num_of_colons == 2 and ch != ":":
            buf_ss[buffer_j] = ch
            buffer_j += 1

        if i == char_link_distance_VDF:
            hh1 = buf_hh[0]
            hh2 = buf_hh[1]
            mm1 = buf_mm[0]
            mm2 = buf_mm[1]

            hhf1 = (float(hh1) - 48)
            hhf2 = (float(hh2) - 48)
            mmf1 = (float(mm1) - 48)
            mmf2 = (float(mm2) - 48)

            dd = 0
            hh = hhf1 * 10 * 60 + hhf2 * 60
            mm = mmf1 * 10 + mmf2

            global_minute = dd + hh + mm

            buffer_i = 0
            buffer_j = 0
            buffer_k = 0
            num_of_colons = 0
            break

        if ch == ":":
            num_of_colons += 1
    return global_minute


def g_output_tmc_file() -> None:
    cbi_col_1 = ["link_id", "tmc", "tmc_corridor_name", "tmc_corridor_id",
                 "tmc_road_order", "tmc_road_sequence", "tmc_road", "tmc_direction",
                 "tmc_intersection", "tmc_highest_speed", "link_no",
                 "from_node_id", "to_node_id", "link_type"]

    cbi_col_2 = ["link_type_code", "FT", "AT", "vdf_code",
                 "nlanes", "link_distance_VDF", "free_speed",
                 "capacity", "k_critical", "vcutoff", "highest_speed",
                 "vcutoff_updated", "vcutoff_ratio", "v_critical_s3"]


def g_output_qvdf_file() -> None:
    pass


if __name__ == "__main__":
    df = map_tmc_reading("./data_input/Reading.csv")
