/* Portions Copyright 2019-2021 Xuesong Zhou and Peiheng Li, Cafer Avci

 * If you help write or modify the code, please also list your names here.
 * The reason of having Copyright info here is to ensure all the modified version, as a whole, under the GPL
 * and further prevent a violation of the GPL.
 *
 * More about "How to use GNU licenses for your own software"
 * http://www.gnu.org/licenses/gpl-howto.html
 */

 // Peiheng, 02/03/21, remove them later after adopting better casting
#pragma warning(disable : 4305 4267 4018)
// stop warning: "conversion from 'int' to 'float', possible loss of data"
#pragma warning(disable: 4244)

#ifdef _WIN32
#include "pch.h"
#endif

#include "config.h"
#include "utils.h"

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

std::ofstream g_summary_file;

void g_program_stop()
{
	cout << "DTALite Program stops. Press any key to terminate. Thanks!" << endl;
	getchar();
	exit(0);
}

void g_program_exit()
{
	cout << "DTALite Program completes. Thanks!" << endl;

	exit(0);
}


__int64 g_get_cell_ID(double x, double y, double grid_resolution)
{
	__int64 xi;
	xi = floor(x / grid_resolution);

	__int64 yi;
	yi = floor(y / grid_resolution);

	__int64 x_code, y_code, code;
	x_code = fabs(xi) * grid_resolution * 1000000000000;
	y_code = fabs(yi) * grid_resolution * 100000;
	code = x_code + y_code;
	return code;
};

string g_get_cell_code(double x, double y, double grid_resolution, double left, double top)
{
	std::string s("ABCDEFGHIJKLMNOPQRSTUVWXYZ");
	std::string str_letter;
	std::string code;

	__int64 xi;
	xi = floor(x / grid_resolution) - floor(left / grid_resolution);

	__int64 yi;
	yi = ceil(top / grid_resolution) - floor(y / grid_resolution);

	int digit = (int)(xi / 26);
	if (digit >= 1)
		str_letter = s.at(digit % s.size());

	int reminder = xi - digit * 26;
	str_letter += s.at(reminder % s.size());

	std::string num_str = std::to_string(yi);

	code = str_letter + num_str;

	return code;

}

#include "DTA.h"

// some basic parameters setting
std::vector<CNode> g_node_vector;
std::vector<CLink> g_link_vector;
std::map<string, CVDF_Type> g_vdf_type_map;
std::map<string, CCorridorInfo>  g_corridor_info_base0_map, g_corridor_info_SA_map;

int g_related_zone_vector_size;

Assignment assignment;

std::map<string, CTMC_Corridor_Info> g_tmc_corridor_vector;

#include "input.h"
#include "output.h"
#include "cbi_tool.h"

std::vector<CTMC_Link> g_TMC_vector;


void  CLink::calculate_dynamic_VDFunction(int inner_iteration_number, bool congestion_bottleneck_sensitivity_analysis_mode, int VDF_type_no)
{
	RT_waiting_time = 0; // reset RT_travel time for each end of simulation iteration 

	if (VDF_type_no == 0 || VDF_type_no == 1)  // BPR, QVDF
	{
		// for each time period
		for (int tau = 0; tau < assignment.g_number_of_demand_periods; ++tau)
		{
			double link_volume_to_be_assigned = PCE_volume_per_period[tau] + VDF_period[tau].preload + VDF_period[tau].sa_volume;

			if (link_id == "7422")
			{
				int idebug = 1;
			}
			if (VDF_period[tau].nlanes == 0)
			{
				int idebug;
				idebug = 1;
			}

			travel_time_per_period[tau] = VDF_period[tau].calculate_travel_time_based_on_QVDF(
				link_volume_to_be_assigned,
				this->model_speed, this->est_volume_per_hour_per_lane);

			VDF_period[tau].link_volume = link_volume_to_be_assigned;
//			VDF_period[tau].travel_time_per_iteration_map[inner_iteration_number] = travel_time_per_period[tau];
		}
	}
	else  // VDF_type_no = 2: 
	{
		// to do
		//calculate time-dependent travel time across all periods
		// and then assign the values to each periodd
		// for loop
		// for each time period
		// initialization 
		for (int tau = 0; tau < assignment.g_number_of_demand_periods; ++tau)
		{
			VDF_period[tau].queue_length = 0;
			VDF_period[tau].arrival_flow_volume = PCE_volume_per_period[tau];
			VDF_period[tau].discharge_rate = VDF_period[tau].lane_based_ultimate_hourly_capacity * VDF_period[tau].nlanes;

			// dependend on the downstream blockagge states 

			VDF_period[tau].avg_waiting_time = 0;
		}
		//time-slot based queue evolution
		for (int tau = 1; tau < assignment.g_number_of_demand_periods; ++tau)
		{
			VDF_period[tau].queue_length = max(0.0f, VDF_period[tau - 1].queue_length + VDF_period[tau].arrival_flow_volume - VDF_period[tau].discharge_rate);

			if (inner_iteration_number == 1 && g_node_vector[this->from_node_seq_no].node_id == 1 &&
				g_node_vector[this->to_node_seq_no].node_id == 3)
			{
				int idebug = 1;

			}
		}

		// slot based total waiting time 
		for (int tau = 0; tau < assignment.g_number_of_demand_periods; ++tau)
		{
			float prevailing_queue_length = 0;

			if (tau >= 1)
				prevailing_queue_length = VDF_period[tau - 1].queue_length;


			float total_waiting_time = (prevailing_queue_length + VDF_period[tau].queue_length) / 2.0 * VDF_period[tau].L;  // unit min
			// to do: 

			VDF_period[tau].avg_waiting_time = total_waiting_time / max(1.0f, VDF_period[tau].arrival_flow_volume);
			VDF_period[tau].avg_travel_time = VDF_period[tau].FFTT + VDF_period[tau].avg_waiting_time;
			VDF_period[tau].DOC = (prevailing_queue_length + VDF_period[tau].arrival_flow_volume) / max(0.01, VDF_period[tau].lane_based_ultimate_hourly_capacity * VDF_period[tau].nlanes);
			//to do:


			this->travel_time_per_period[tau] = VDF_period[tau].avg_waiting_time + VDF_period[tau].FFTT;

			// apply queue length at the time period to all the time slots included in this period
			for (int slot_no = assignment.g_DemandPeriodVector[tau].starting_time_slot_no; slot_no < assignment.g_DemandPeriodVector[tau].ending_time_slot_no; slot_no++)
			{
				this->est_queue_length_per_lane[slot_no] = VDF_period[tau].queue_length / max(1.0, this->number_of_lanes);
				this->est_avg_waiting_time_in_min[slot_no] = VDF_period[tau].avg_waiting_time;
				float number_of_hours = assignment.g_DemandPeriodVector[tau].time_period_in_hour;  // unit hour
				this->est_volume_per_hour_per_lane[slot_no] = VDF_period[tau].arrival_flow_volume / max(0.01f, number_of_hours) / max(1.0, this->number_of_lanes);
			}
		}
	}
}

double network_assignment(int assignment_mode, int column_generation_iterations, int column_updating_iterations, int ODME_iterations, int sensitivity_analysis_iterations, int simulation_iterations, int number_of_memory_blocks)
{
	g_summary_file.open("summary.csv");
	clock_t start_t0, end_t0, total_t0;
	int signal_updating_iterations = 0;
	start_t0 = clock();
	// k iterations for column generation
	// 0: link UE: 1: path UE, 2: Path SO, 3: path resource constraints

	assignment.assignment_mode = dta;

	if (assignment_mode == 11)
		assignment.assignment_mode = cbi;

	//if (assignment_mode == 13)
	//	assignment.assignment_mode = cbsa;



	// step 1: read input data of network / demand tables / Toll
	g_read_input_data(assignment);

	assignment.map_tmc_reading();  // read reading file
		g_output_tmc_file();
		g_output_qvdf_file();

		for (int i = 0; i < g_link_vector.size(); ++i)
		{
			if (g_link_vector[i].tmc_code.size() > 0)
			{
				// step 1: travel time based on VDF
				g_link_vector[i].calculate_dynamic_VDFunction(0, false, g_link_vector[i].vdf_type);
			}

		}
	
	

	// at the end of simulation 
	// validation step if reading data are available
	bool b_sensor_reading_data_available = false;
	CCSVParser parser_reading;
	if (parser_reading.OpenCSVFile("Reading.csv", false))
	{
		parser_reading.CloseCSVFile();
		b_sensor_reading_data_available = true;
	}

	if (b_sensor_reading_data_available)
	{
		assignment.map_tmc_reading();  // read reading file
		g_output_tmc_file();
	}

	cout<< "Output for assignment with " << assignment.g_number_of_column_generation_iterations << " iterations. Traffic assignment completes!" << endl;

	cout<< "free memory.." << endl;

	g_summary_file.close();
	return 1;
}


