/* Portions Copyright 2019-2021 Xuesong Zhou and Peiheng Li, Cafer Avci

 * If you help write or modify the code, please also list your names here.
 * The reason of having Copyright info here is to ensure all the modified version, as a whole, under the GPL
 * and further prevent a violation of the GPL.
 *
 * More about "How to use GNU licenses for your own software"
 * http://www.gnu.org/licenses/gpl-howto.html
 */

 // Peiheng, 02/03/21, remove them later after adopting better casting
#pragma warning(disable : 4305 4267 4018 )
// stop warning: "conversion from 'int' to 'float', possible loss of data"
#pragma warning(disable: 4244)
#pragma warning(disable: 4267)
#pragma warning(disable: 4477)



#ifdef _WIN32
#include "pch.h"
#endif

#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <string>
#include <cstring>
#include <cstdio>
#include <ctime>
#include <cmath>
#include <algorithm>
#include <functional>
#include <stack>
#include <list>
#include <vector>
#include <map>
#include <omp.h>
#include "config.h"
#include "utils.h"


using std::max;
using std::min;
using std::cout;
using std::endl;
using std::string;
using std::vector;
using std::map;
using std::ifstream;
using std::ofstream;
using std::istringstream;

#include "DTA.h"
#include "geometry.h"



void g_detector_file_open_status()
{
	FILE* g_pFilePathMOE = nullptr;

	fopen_ss(&g_pFilePathMOE, "final_summary.csv", "w");
	if (!g_pFilePathMOE)
	{
		cout<< "File final_summary.csv cannot be opened." << endl;
		g_program_stop();
	}
	else
	{
		fclose(g_pFilePathMOE);
	}

}
void g_read_input_data(Assignment& assignment)
{
	g_detector_file_open_status();

	assignment.g_LoadingStartTimeInMin = 99999;
	assignment.g_LoadingEndTimeInMin = 0;

	assignment.g_LoadingStartTimeInMin = 99999;
	assignment.g_LoadingEndTimeInMin = 0;

	//step 0:read demand period file
	CCSVParser parser_demand_period;
	cout<< "_____________" << endl;
	cout<< "Step 1: Reading input data" << endl;
	cout<< "_____________" << endl;

	cout<< "Step 1.1: Reading section [demand_period] in setting.csv..." << endl;

	parser_demand_period.IsFirstLineHeader = false;

	//AM
	CDemand_Period demand_period;
	vector<float> global_minute_vector;



	demand_period.demand_period_id = 1;
	demand_period.demand_period = "AM";
	demand_period.default_plf = 1;
	global_minute_vector.push_back(6 * 60);
	global_minute_vector.push_back(9 * 60);

	demand_period.starting_time_slot_no = global_minute_vector[0] / MIN_PER_TIMESLOT;  // read the data
	demand_period.ending_time_slot_no = global_minute_vector[1] / MIN_PER_TIMESLOT;    // read the data from setting.csv
	demand_period.time_period_in_hour = (global_minute_vector[1] - global_minute_vector[0]) / 60.0;
	demand_period.t2_peak_in_hour = (global_minute_vector[0] + global_minute_vector[1]) / 2 / 60;
	assignment.g_DemandPeriodVector.push_back(demand_period);

	// noon mid day
	global_minute_vector.clear();
	demand_period.demand_period_id = 2;
	demand_period.demand_period = "MD";
	demand_period.default_plf = 1;
	global_minute_vector.push_back(9 * 60);
	global_minute_vector.push_back(15 * 60);

	demand_period.starting_time_slot_no = global_minute_vector[0] / MIN_PER_TIMESLOT;  // read the data
	demand_period.ending_time_slot_no = global_minute_vector[1] / MIN_PER_TIMESLOT;    // read the data from setting.csv
	demand_period.time_period_in_hour = (global_minute_vector[1] - global_minute_vector[0]) / 60.0;
	demand_period.t2_peak_in_hour = (global_minute_vector[0] + global_minute_vector[1]) / 2 / 60;
	assignment.g_DemandPeriodVector.push_back(demand_period);

	// afternoon
	global_minute_vector.clear();
	demand_period.demand_period_id = 2;
	demand_period.demand_period = "PM";
	demand_period.default_plf = 1;
	global_minute_vector.push_back(15 * 60);
	global_minute_vector.push_back(19 * 60);


	demand_period.starting_time_slot_no = global_minute_vector[0] / MIN_PER_TIMESLOT;  // read the data
	demand_period.ending_time_slot_no = global_minute_vector[1] / MIN_PER_TIMESLOT;    // read the data from setting.csv
	demand_period.time_period_in_hour = (global_minute_vector[1] - global_minute_vector[0]) / 60.0;
	demand_period.t2_peak_in_hour = (global_minute_vector[0] + global_minute_vector[1]) / 2 / 60;
	assignment.g_DemandPeriodVector.push_back(demand_period);


	cout<< "_____________" << endl;
	cout<< "Step 1: Reading input data" << endl;
	cout<< "_____________" << endl;

	cout<< "number of link types = " << assignment.g_LinkTypeMap.size() << endl;

	assignment.g_number_of_nodes = 0;
	assignment.g_number_of_links = 0;  // initialize  the counter to 0

	int internal_node_seq_no = 0;
	// step 3: read node file

	std::map<string, int> long_lat_string_to_node_id_mapping;

	
	CCSVParser parser;

	cout<< "Step 1.4: Reading node data in TMC_identification.csv..." << endl;
	std::map<int, int> zone_id_to_analysis_district_id_mapping;

		// master file: reading nodes

		string file_name = "TMC_Identification.csv";


		if (parser.OpenCSVFile(file_name.c_str(), true))
		{
			// create a node object
			CNode node;

			while (parser.ReadRecord())  // if this line contains [] mark, then we will also read field headers.
			{

				double x_coord_from;
				double y_coord_from;
				parser.GetValueByFieldName("start_longitude", x_coord_from,true,false);
				parser.GetValueByFieldName("start_latitude", y_coord_from, true, false);

				string start_longitude;
				string start_latitude;

				parser.GetValueByFieldName("start_longitude", start_longitude);
				parser.GetValueByFieldName("start_latitude", start_latitude);

				double x_coord_to;
				double y_coord_to;

				parser.GetValueByFieldName("end_longitude", x_coord_to, true, false);
				parser.GetValueByFieldName("end_latitude", y_coord_to, true, false);

				string end_latitude;
				string end_longitude;

				parser.GetValueByFieldName("end_longitude", end_longitude);
				parser.GetValueByFieldName("end_latitude", end_latitude);
				
				string direction;
				parser.GetValueByFieldName("direction", direction);

				DTA_Direction dir = DTA_NULL;

				if (direction == "N")
				{
					dir = DTA_North;
				}
				if (direction == "E")
				{
					dir = DTA_East;
				}
				if (direction == "S")
				{
					dir = DTA_South;
				}
				if (direction == "W")
				{
					dir = DTA_West;
				}


				string tmc_corridor_name;
				parser.GetValueByFieldName("tmc_corridor_name", tmc_corridor_name, false);

				string long_lat_string_from;
				long_lat_string_from = start_longitude + "_" + start_latitude;

				string long_lat_string_to;
				long_lat_string_to = end_longitude + "_" + end_latitude;

				
				CTMC_Corridor_Info corridor;

				if (g_tmc_corridor_vector.find(tmc_corridor_name) == g_tmc_corridor_vector.end())
				{
					corridor.tmc_corridor_id = g_tmc_corridor_vector.size() + 1;
					corridor.m_dir = dir;
					g_tmc_corridor_vector[tmc_corridor_name] = corridor;


					//establish the corridor 
				}
				

					


				if (long_lat_string_to_node_id_mapping.find(long_lat_string_from) == long_lat_string_to_node_id_mapping.end())
				{
					// micro network filter:
					GDPoint pt;
					pt.x = x_coord_from;
					pt.y = y_coord_from;

					int node_id = assignment.g_node_id_to_seq_no_map.size()+1;
					long_lat_string_to_node_id_mapping[long_lat_string_from] = node_id;
						
					assignment.g_node_id_to_seq_no_map[node_id] = internal_node_seq_no;
					node.node_id = node_id;
					node.node_seq_no = internal_node_seq_no;
					node.x = x_coord_from;
					node.y = y_coord_from;
					node.agent_id = tmc_corridor_name;
					// push it to the global node vector
					g_node_vector.push_back(node);
					
					g_tmc_corridor_vector[tmc_corridor_name].node_no_vector.push_back(internal_node_seq_no);
					pt.node_no = node.node_seq_no;
					g_tmc_corridor_vector[tmc_corridor_name].point_vector.push_back(pt);

					internal_node_seq_no++;

					

					assignment.g_number_of_nodes++;
				}

				if (long_lat_string_to_node_id_mapping.find(long_lat_string_to) == long_lat_string_to_node_id_mapping.end())
				{
					// micro network filter:
					GDPoint pt;
					pt.x = x_coord_to;
					pt.y = y_coord_to;

					int node_id = assignment.g_node_id_to_seq_no_map.size() + 1;
					long_lat_string_to_node_id_mapping[long_lat_string_to] = node_id;
					assignment.g_node_id_to_seq_no_map[node_id] = internal_node_seq_no;
					node.node_id = node_id;
					node.node_seq_no = internal_node_seq_no;
					node.x = x_coord_to;
					node.y = y_coord_to;
					node.agent_id = tmc_corridor_name;
					// push it to the global node vector
					g_node_vector.push_back(node);
					g_tmc_corridor_vector[tmc_corridor_name].node_no_vector.push_back(internal_node_seq_no);
					pt.node_no = node.node_seq_no;
					g_tmc_corridor_vector[tmc_corridor_name].point_vector.push_back(pt);
					assignment.g_number_of_nodes++;
					internal_node_seq_no++;
				}

				if (assignment.g_number_of_nodes % 5000 == 0)
					cout<< "reading " << assignment.g_number_of_nodes << " nodes.. " << endl;
			}

			cout<< "number of nodes = " << assignment.g_number_of_nodes << endl;

			// fprintf(g_pFileOutputLog, "number of nodes =,%d\n", assignment.g_number_of_nodes);
			parser.CloseCSVFile();
		}
		else
		{
			cout<< "file TMC_Identification.csv cannot be opened. Please check!" << endl;
			g_program_stop();
		}

		CCSVParser parser_link;

		int link_type_warning_count = 0;
		bool length_in_km_waring = false;


		file_name = "TMC_Identification.csv";

		if (parser_link.OpenCSVFile(file_name.c_str(), true))
		{
			// create a link object
			CLink link;

			while (parser_link.ReadRecord())  // if this line contains [] mark, then we will also read field headers.
			{
				string link_type_name_str;
				parser_link.GetValueByFieldName("link_type_name", link_type_name_str, false);


				string start_longitude;
				string start_latitude;

				parser_link.GetValueByFieldName("start_longitude", start_longitude);
				parser_link.GetValueByFieldName("start_latitude", start_latitude);


				string end_latitude;
				string end_longitude;

				parser_link.GetValueByFieldName("end_longitude", end_longitude);
				parser_link.GetValueByFieldName("end_latitude", end_latitude);


				string long_lat_string_from;
				long_lat_string_from = start_longitude + "_" + start_latitude;

				string long_lat_string_to;
				long_lat_string_to = end_longitude + "_" + end_latitude;


				long from_node_id = -1;
				long to_node_id = -1;

				if (long_lat_string_to_node_id_mapping.find(long_lat_string_from) != long_lat_string_to_node_id_mapping.end())
				{
					from_node_id = long_lat_string_to_node_id_mapping[long_lat_string_from];
				}

				if (long_lat_string_to_node_id_mapping.find(long_lat_string_to) != long_lat_string_to_node_id_mapping.end())
				{
					to_node_id = long_lat_string_to_node_id_mapping[long_lat_string_to];
				}


				if (from_node_id == -1 || from_node_id == -1)
					continue;


				string linkID;
				parser_link.GetValueByFieldName("tmc", linkID, false);
				// add the to node id into the outbound (adjacent) node list

				if (assignment.g_node_id_to_seq_no_map.find(from_node_id) == assignment.g_node_id_to_seq_no_map.end())
				{

					cout << "Error: from_node_id " << from_node_id << " in file TMC_Identification.csv is not defined in node.csv." << endl;
					continue; //has not been defined
				}

				if (assignment.g_node_id_to_seq_no_map.find(to_node_id) == assignment.g_node_id_to_seq_no_map.end())
				{


					cout << "Error: to_node_id " << to_node_id << " in file TMC_Identification.csv is not defined in node.csv." << endl;
					continue; //has not been defined
				}

				//if (assignment.g_link_id_map.find(linkID) != assignment.g_link_id_map.end())
				//    cout<< "Error: link_id " << linkID.c_str() << " has been defined more than once. Please check link.csv." << endl;

				int internal_from_node_seq_no = assignment.g_node_id_to_seq_no_map[from_node_id];  // map external node number to internal node seq no.
				int internal_to_node_seq_no = assignment.g_node_id_to_seq_no_map[to_node_id];

				link.from_node_seq_no = internal_from_node_seq_no;
				link.to_node_seq_no = internal_to_node_seq_no;
				link.link_seq_no = assignment.g_number_of_links;
				link.to_node_seq_no = internal_to_node_seq_no;
				link.link_id = linkID;
				link.tmc_code = linkID;

				assignment.g_link_id_map[link.link_id] = 1;

				//// TMC reading 
				string tmc_code;

				parser_link.GetValueByFieldName("tmc", link.tmc_code, false);

				if (link.tmc_code.size() == 0)
				{

				cout << "tmc in TMC_identification.csv is not defined." << endl;
				return;
				}

				string road, direction;
				parser_link.GetValueByFieldName("road", road, false);
				parser_link.GetValueByFieldName("direction", direction, false);

				link.tmc_road_sequence = 1;
				link.tmc_corridor_name = road + "_" + direction;

				parser_link.GetValueByFieldName("road", link.tmc_corridor_name, true);
				parser_link.GetValueByFieldName("road_order", link.tmc_road_sequence,true);
				double free_speed = 60.0;
				parser_link.GetValueByFieldName("free_speed", free_speed, true);

				if (g_tmc_corridor_vector.find(link.tmc_corridor_name) != g_tmc_corridor_vector.end())
				{
					link.tmc_corridor_id = g_tmc_corridor_vector[link.tmc_corridor_name].tmc_corridor_id;

					//establish the corridor 
				}

				int link_type = 2;

				double length = 1.0; // km or mile

				double cutoff_speed = 1.0;
				double k_jam = assignment.g_LinkTypeMap[link.link_type].k_jam;
				double bwtt_speed = 12;  //miles per hour

				double lane_capacity = 1800;
				parser_link.GetValueByFieldName("miles", length);  // in meter
			
				link.free_flow_travel_time_in_min = length/ free_speed * 60;  // link_distance_VDF in meter 
				float fftt_in_sec = link.free_flow_travel_time_in_min * 60;  // link_distance_VDF in meter 

				link.length_in_meter = length*1609;
				link.link_distance_VDF = length;
				link.link_distance_mile = length;

				link.number_of_lanes = 1;
				link.lane_capacity = lane_capacity;

				link.vdf_type = assignment.g_LinkTypeMap[link.link_type].vdf_type;
				link.kjam = assignment.g_LinkTypeMap[link.link_type].k_jam;
				char VDF_field_name[50];

				// reading for VDF related functions 
				// step 1 read type

				//data initialization 

				for (int time_index = 0; time_index < MAX_TIMEINTERVAL_PerDay; time_index++)
				{
					link.model_speed[time_index] = free_speed;
					link.est_volume_per_hour_per_lane[time_index] = 0;
					link.est_avg_waiting_time_in_min[time_index] = 0;
					link.est_queue_length_per_lane[time_index] = 0;
				}


				for (int tau = 0; tau < assignment.g_number_of_demand_periods; ++tau)
				{
					//setup default values
					link.VDF_period[tau].vdf_type = assignment.g_LinkTypeMap[link.link_type].vdf_type;
					link.VDF_period[tau].lane_based_ultimate_hourly_capacity = lane_capacity;
					link.VDF_period[tau].nlanes = 1;

					link.VDF_period[tau].FFTT = link.link_distance_VDF / max(0.0001, link.free_speed) * 60.0;  // 60.0 for 60 min per hour
					link.v_congestion_cutoff = 0.7 * link.free_speed;
					link.VDF_period[tau].vf = link.free_speed;
					link.VDF_period[tau].v_congestion_cutoff = link.v_congestion_cutoff;
					link.VDF_period[tau].alpha = 0.15;
					link.VDF_period[tau].beta = 4;
					link.VDF_period[tau].preload = 0;

					link.VDF_period[tau].starting_time_in_hour = assignment.g_DemandPeriodVector[tau].starting_time_slot_no * MIN_PER_TIMESLOT / 60.0;
					link.VDF_period[tau].ending_time_in_hour = assignment.g_DemandPeriodVector[tau].ending_time_slot_no * MIN_PER_TIMESLOT / 60.0;
					link.VDF_period[tau].L = assignment.g_DemandPeriodVector[tau].time_period_in_hour;
					link.VDF_period[tau].t2 = assignment.g_DemandPeriodVector[tau].t2_peak_in_hour;
					link.VDF_period[tau].peak_load_factor = 1;

				}

				link.update_kc(free_speed);
				link.link_spatial_capacity = k_jam * 1 * link.link_distance_VDF;

				link.link_distance_VDF = max(0.00001, link.link_distance_VDF);
				for (int tau = 0; tau < assignment.g_number_of_demand_periods; ++tau)
					link.travel_time_per_period[tau] = link.link_distance_VDF / free_speed * 60;

				// min // calculate link cost based link_distance_VDF and speed limit // later we should also read link_capacity, calculate delay

				//int sequential_copying = 0;
				//
				//parser_link.GetValueByFieldName("sequential_copying", sequential_copying);

				g_node_vector[internal_from_node_seq_no].m_outgoing_link_seq_no_vector.push_back(link.link_seq_no);  // add this link to the corresponding node as part of outgoing node/link
				g_node_vector[internal_to_node_seq_no].m_incoming_link_seq_no_vector.push_back(link.link_seq_no);  // add this link to the corresponding node as part of outgoing node/link

				g_node_vector[internal_from_node_seq_no].m_to_node_seq_no_vector.push_back(link.to_node_seq_no);  // add this link to the corresponding node as part of outgoing node/link
				g_node_vector[internal_from_node_seq_no].m_to_node_2_link_seq_no_map[link.to_node_seq_no] = link.link_seq_no;  // add this link to the corresponding node as part of outgoing node/link


				g_link_vector.push_back(link);

				assignment.g_number_of_links++;

				if (assignment.g_number_of_links % 10000 == 0)
					cout<< "reading " << assignment.g_number_of_links << " links.. " << endl;
			}

			parser_link.CloseCSVFile();

			cout<< "number of links =" << g_link_vector.size() << endl;
		}

		g_OutputModelFiles();

	// we now know the number of links

	cout<< "number of links =" << assignment.g_number_of_links << endl;
	
	assignment.summary_file << "Step 1: read TMC_identification "<< endl;
	assignment.summary_file << ",# of nodes = ," << g_node_vector.size() << endl;
	assignment.summary_file << ",# of links =," << g_link_vector.size() << endl;

	assignment.summary_file << ",summary by multi-modal and demand types,demand_period,agent_type,# of links,avg_free_speed,total_length_in_km,total_capacity,avg_lane_capacity,avg_length_in_meter," << endl;
	for (int tau = 0; tau < assignment.g_DemandPeriodVector.size(); ++tau)
		for (int at = 0; at < assignment.g_AgentTypeVector.size(); at++)
		{
			assignment.summary_file << ",," << assignment.g_DemandPeriodVector[tau].demand_period.c_str() << ",";
			assignment.summary_file << assignment.g_AgentTypeVector[at].agent_type.c_str() << ",";

			int link_count = 0;
			double total_speed = 0;
			double total_length = 0;
			double total_lane_capacity = 0;
			double total_link_capacity = 0;

			for (int i = 0; i < g_link_vector.size(); i++)
			{
				if (g_link_vector[i].link_type >= 0 && g_link_vector[i].AllowAgentType(assignment.g_AgentTypeVector[at].agent_type, tau))
				{
					link_count++;
					total_speed += g_link_vector[i].free_speed;
					total_length += g_link_vector[i].length_in_meter * g_link_vector[i].number_of_lanes;
					total_lane_capacity += g_link_vector[i].lane_capacity;
					total_link_capacity += g_link_vector[i].lane_capacity * g_link_vector[i].number_of_lanes;
				}
			}
			assignment.summary_file << link_count << "," << total_speed / max(1, link_count) << "," <<
				total_length/1000.0 << "," <<
				total_link_capacity << "," <<
				total_lane_capacity / max(1, link_count) << "," << total_length / max(1, link_count) << "," << endl;
		}
	/// <summary>
	/// ///////////////////////////
	/// </summary>
	/// <param name="assignment"></param>
	assignment.summary_file << ",summary by road link type,link_type,link_type_name,# of links,avg_free_speed,total_length,total_capacity,avg_lane_capacity,avg_length_in_meter," << endl;
	std::map<int, CLinkType>::iterator it_link_type;
	int count_zone_demand = 0;
	for (it_link_type = assignment.g_LinkTypeMap.begin(); it_link_type != assignment.g_LinkTypeMap.end(); ++it_link_type)
	{
		assignment.summary_file << ",," << it_link_type->first << "," << it_link_type->second.link_type_name.c_str() << ",";

		int link_count = 0;
		double total_speed = 0;
		double total_length = 0;
		double total_lane_capacity = 0;
		double total_link_capacity = 0;

		for (int i = 0; i < g_link_vector.size(); i++)
		{
			if (g_link_vector[i].link_type >= 0 && g_link_vector[i].link_type == it_link_type->first)
			{
				link_count++;
				total_speed += g_link_vector[i].free_speed;
				total_length += g_link_vector[i].length_in_meter * g_link_vector[i].number_of_lanes;
				total_lane_capacity += g_link_vector[i].lane_capacity;
				total_link_capacity += g_link_vector[i].lane_capacity * g_link_vector[i].number_of_lanes;
			}
		}
		assignment.summary_file << link_count << "," << total_speed / max(1, link_count) << "," <<
			total_length/1000.0 << "," <<
			total_link_capacity << "," <<
			total_lane_capacity / max(1, link_count) << "," << total_length / max(1, link_count) << "," << endl;
	}


}


