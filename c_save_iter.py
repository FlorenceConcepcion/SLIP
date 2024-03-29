"""
This code is to save relevant files such as: 

XXX.cln                 linelist file (as this does change as we find problem lines!)                
spec_db.csv         	linelist csv                                                                
-------------------------------------------------------------------------------------------- 
XXX.badid            	file with bad identifications from STRANS                                  
XXX.badlin           	file with bad spectral lines containing reasons why they are bad and a tag  
1_init_db.par      		parameter file for python script a_init_db.py                             
2_iter_db.par      		parameter file for python script b_iter_db.py                           
-------------------------------------------------------------------------------------------- 
XXX_work.sinp      		working STRANS input                                                        
working.lines        	working STRANS identified lines output                                     
working.out          	working STRANS output, predicted lines                                      
-------------------------------------------------------------------------------------------- 
lopt_additions.linp 	lines added manually to LOPT (as certain lines are removed from STRANS inp) 
XXX.linp          		working LOPT input                                                          
XXX_lopt.lev     		working LOPT output levels identified                                       
XXX_lopt.lin     		working LOPT output lines used   
----- parameter file?                                          
working_lopt.out    	formatted LOPT output                                                       
-------------------------------------------------------------------------------------------- 
For the use of LEVHAMS, these 5 files should be saved for every iteration:

 .bat       			LEVHAMD: Batch file to run LEVHAMD_64 with input file:       
 .inp       			LEVHAMD: This file helps keeps a record of the parameters used      
 .lev       			LEVHAMD: The file containing levels       
 .lines     			LEVHAMD: The file containing lines       
 .out       			LEVHAMD: The output file containing predicted levels.         
-------------------------------------------------------------------------------------------- 
"""

save_dir		= "/save_iter/"
items_saved		= "LEVHAMD"				# SLIP (STRANS, LOPT) or LEVHAMD

########################################################################
########################################################################
import os
from datetime import datetime

########################################################################	   
def get_parameters(parameter_filename):
	par_file = open(parameter_filename, 'r')
	par_data = [i for i in par_file]; par_file.close()
	par_data = [i for i in par_data if i.strip("\n") != ""]
	par_data = [i for i in par_data if i.strip(" ")[0]!="#"]
	for par_line in par_data:
		param = par_line.split("=")[0].strip(" \t")
		value = par_line.split('"')[1].strip(" \t")
		exec('global %s' % (param), globals(), globals())
		exec('%s=%s' % (param, repr(value)), globals(), globals())
		print(param, value)
########################################################################
""" Get the parameters """
parameter_filename 		= "2_iter_db.par"
get_parameters(parameter_filename)
parameter_filename 		= "3_save_runLEVHAM.par"
get_parameters(parameter_filename)
if path_to_STRANS[-1] 	== "/": pass
else: path_to_STRANS 	= path_to_STRANS + "/" 
if path_to_LOPT[-1] 	== "/": pass
else: path_to_LOPT 		= path_to_LOPT + "/" 
if save_dir[-1] 		== "/": pass
else: save_dir 			= save_dir + "/" 
if save_dir[0] 			== "/": pass
else: save_dir 			= "/" + save_dir
table_name 				= "spec_db"

cur_location = os.getcwd()

########################################################################



def ensure_dir(file_path):
	#~ print("Looking for:", file_path)
	if not os.path.exists(file_path):
		print ("Directory created:", file_path)
		os.makedirs(file_path)

def create_savedir_SLIP():
	ensure_dir(cur_location + save_dir)
	time_now = datetime.now().strftime('%Y%m%d_%H%M%S')
	descrip = input("Short name of iteration? (no spaces): ")
	datetime_dir = cur_location + save_dir + time_now + descrip + "/" 
	os.makedirs(datetime_dir)
	for dir_item in ["param", "STRANS", "LOPT"]:
		os.makedirs(datetime_dir + dir_item + "/")
	
	param_file_list = [cln_filename, table_name + '.csv', badid_filename, \
						badln_file, "1_init_db.par", "2_iter_db.par" ]
	for file_i in param_file_list:
		os.system("cp " + file_i + " " + datetime_dir + "/param/")
	
	global STRANS_products_loc
	if STRANS_products_loc == "": STRANS_products_loc = path_to_STRANS
	strans_file_list = [path_to_STRANS + working_STRANSinp, \
						STRANS_products_loc + "working.lines", \
						STRANS_products_loc + "working.out"]
	for file_i in strans_file_list:
		os.system("cp " + file_i + " " + datetime_dir + "/STRANS/")
		
		
	lopt_file_list = [LOPT_additions, path_to_LOPT + LOPT_input_filename, \
		path_to_LOPT + LOPT_par_filename, path_to_LOPT + LOPT_lvls_out, \
		path_to_LOPT + LOPT_lines_out, formatted_LOPTout]
	for file_i in lopt_file_list:
		os.system("cp " + file_i + " " + datetime_dir + "/LOPT/")

def create_savedir_LEVHAMD():
	ensure_dir(cur_location + save_dir)
	time_now = datetime.now().strftime('%Y%m%d_%H%M%S')
	descrip = input("Short name of iteration? (no spaces): ")
	datetime_dir = cur_location + save_dir + time_now + descrip + "/" 
	os.makedirs(datetime_dir)
	for dir_item in ["param", "LEVHAMD"]:
		os.makedirs(datetime_dir + dir_item + "/")
	
	param_file_list = [cln_filename, table_name + '.csv', "1_init_db.par",\
					"2_iter_db.par", "3_save_runLEVHAM.par", formatted_LOPTout ]
	for file_i in param_file_list:
		os.system("cp " + file_i + " " + datetime_dir + "/param/")
	
	global STRANS_products_loc
	if STRANS_products_loc == "": STRANS_products_loc = path_to_STRANS
	levham_file_list = [LEVHAMD_bat, LEVHAMD_inp, LEVHAMD_lev, \
						LEVHAMD_lines, LEVHAMD_out]
	for file_i in levham_file_list:
		os.system("cp " + "runLEVHAM/" + file_i + " " + datetime_dir + "/LEVHAMD/")
		
		
	
	
if items_saved == "SLIP":	create_savedir_SLIP()
elif items_saved == "LEVHAMD":	create_savedir_LEVHAMD()

