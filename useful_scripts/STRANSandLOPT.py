#Enjoy, email me errors, thanks!
""" 
Created using Python 2.7 



1. "convert linelist script NAME" (in folder 1)
2. "2_runstrans for all elements NAME" (in folder 2)
3. This script!

Recommended to run before this script is "convert linelist script NAME" 
to convert the cln file from xgremlin into a STRANS format. The 
"2_runstrans for all elements NAME " script will run strans for all 
elements of interest. 

(Converting into a strans read-able file is sometimes difficult, as 
the method of shortening energy level labels vary with ion. Therefore, 
each new file currently requires a unique function. However, I should
make a function to create a STRANS input without changing the columns. 
Work on it florence! )

In this program we run STRANS using the WORKING file (usually contains
less energy levels to determine these certain levels with higher
accuracy). 

This script will also run LOPT:
 - It creates a LOPT input from the STRANS output. Here it may 
	also remove spectral lines that should not be used for energy level 
	fitting, and any misidentification of lines that STRANS has made. 
 - Run LOPT using created LOPT input. 
 - Will use LOPT output files to create a formatted LOPT output file. 
	This file will contain details of the fitted energy levels and the
	lines used to determine them. 

This script can also create a "merged" linelist. This linelist contains 
the details of spectral lines from our cln file and are matched to 
identifications of elements STRANS has made (in this script:
"2_runstrans for all elements NAME" (in folder 2). 

I am also in the process of creating a function to check the lines
expected to see and their log(gf) values as predicted by Kurucz, with 
those identified for every energy level examined. This may make more 
sense to check from every lower energy level to prevent repeat checks.

Highlight potential problem lines, as lines that are close together?
These may be lines that are very close together and should be fit as a
single CoG fit line (rather than multiple lsqfit lines). This would also
highlight lines that are far apart enough to be lsqfit but overlap and 
so should be labelled problem (?). 


line 246 lines 287 onwards need change in 
"""

#remove?
from datetime import datetime as d
from collections import OrderedDict

from _convertXgrem2strans import create_linelist_STRANSinp

from _create_bat_inp import create_bat_inp
from _create_bat_inp import run_STRANS

### Dont remove: 
import numpy as np
import os



########################################################################
########################################################################
########################################################################

# Create the merged linelist including all possible line identifications.
########################################################################

global cln_file
global unc_file
global badln_file
global badid_filename


""" Is the file containing the data of the lines Xgremlin or csv/tsv?

If not Xgremlin .cln: 
1. set Xgremlin_cln 	= False
2. File should contain: peak, width, wavenumber, fit tag (e.g. L, G) 
3. Lines to ignore should have '#' at the start
4. csv_indices, first column = 0.
""" 

#########################################

cln_file 		= "../1_wn_calib/tmpfe3.cln"
#~ cln_file 		= "../1_wn_calib/del.csv"
#~ Xgremlin_cln 	= False
Xgremlin_cln 	= True

csv_index_peak  = 0
csv_index_width = 1
csv_index_wn	= 2
csv_index_fittag= 3

#########################################

unc_file 		= "../1_wn_calib/tmpfe3.unc"
csv_format		= False
#~ csv_format		= True

unc_index_wn	= 1
unc_index_tot	= 3

#########################################

""" badline file should contain the wavenumber, and the tag or comment """
badln_file 		= "../3_working_files/fe3.badln"

badln_index_wn	= 0
badln_index_tag	= 1

#########################################

badid_filename 	= "../3_working_files/fe3.badid"

#########################################
""" for run_STRANS_true = False, has not been tested!!"""
run_STRANS_true	= True
path_to_STRANS	= ""
ion				= "fe3"	
STRANS_inp		= "working.sinp"
STRANS_out_dat	= "zzz_del.out"
STRANS_out_lines= "zzz_del.lin"
					


#########################################
""" If the location of LOPT is the current directory, leave empty string: '' """
path_to_LOPT 	= "../4_LOPT/"
LOPT_inp		= "test.linp"

""" if additional lines need to be added to the lopt input, for example: 
'     9999     63425.4900 cm-1 0.0001  gr          4G4s 5G6 '
and use '\n' for new lines. """
additional_lopt = '     9999     63425.4900 cm-1 0.0001  gr          4G4s 5G6 '
#~ additional_lopt = ""

LOPT_param_file = "temp_del.par"
LOPT_out_lev	= "temp.lev"
LOPT_out_lin	= "temp.lin" 

LOPT_out_format	= "temp_formatlopt.out"
print("HAVE YOU UPDATED THE LOPT PARAM FILE?")



"""
The create LOPT input function here is for these parameters:: 
N                 ; OMIT calc. wavelengths in ANGSTROMS in the output (Y/N)?
Y                 ; TUNE single-line levels (Y/N)?
N                 ; Print listing of correlated-lines uncert. effects (Y/N)?
Y       ; CALCULATE predicted line UNCERTAINTIES (Y/N)?
Y       ; Write virtual lines (Y/N)?
Y       ; Divide levels into independent groups (Y/N)?
5000    ; MIN. wavenumber for AIR wavelength [cm-1]
50000   ; MAX. wavenumber for AIR wavelength [cm-1]
99.9999 ; ROUND-OFF threshold for output LEVELS
99.9999 ; ROUND-OFF threshold for output LINES
   1    ; 1st column of LINE INTENSITY in the transitions-input file
   11   ; LAST column of LINE INTENSITY in the transitions-input file
 13     ; 1st column of WAVELENGTH in the transitions-input file
 25     ; LAST column of WAVELENGTH in the transitions-input file
26      ; 1st column of wavelength UNITS in the transitions-input file (width=4 chars)
  31    ;1st column of wavelength UNCERTAINTY in the transitions-input file
  37    ;LAST column of wavelength UNCERTAINTY in the transitions-input file
  1000  ;1st column of line WEIGHT in the transitions-input file
  1000  ;LAST column of line WEIGHT in the transitions-input file
38      ;1st column of LOWER LEVEL LABEL in the transitions-input file
48      ;LAST column of LOWER LEVEL LABEL in the transitions-input file
50      ;1st column of UPPER level LABEL in the transitions-input file (width must be same as for lower level)
65      ;1st column for LINE FLAGS (B=blend,Q=questionable,M=masked,P=predicted,A=air wavelength,V=vacuum wavelength; width=5 chars; CORRELATION GROUP No. is entered here!)
Y       ; tab-delimited output [Y/N] ?
"""
########################################################################
########################################################################
########################################################################
########################################################################

def vacToAir(wavelength):
	""" created by C. Clear: 
	convert vac wavelengths to air 
	(from Morton, 2000, ApJ. Suppl., 130, 403) """
	wavelength = float(wavelength)
	s = 10.0**4 / wavelength
	n = 1.0 + 0.0000834254 + (0.02406147 / (130.0 - s**2)) + (0.00015998 / (38.9 - s**2))
	return wavelength/n 

def create_cln_dict():
	""" create the dictionary of the cln file.
	The key is a string formed of the peak, width and wavelength."""
	
	linelist_file = open(cln_file, "r")  # input linelist file
	linelist_data = linelist_file.readlines() ; linelist_file.close()
	cln_dict = OrderedDict()

	if Xgremlin_cln == True:
		#~ cln_header = linelist_data[3]
		linelist = linelist_data[4:]
	if Xgremlin_cln == False:
		linelist = [i for i in linelist_data if i[0] != "#"]
		
	
	for line in linelist: 
		if Xgremlin_cln == True:
			waveNum = '{:.4f}'.format(float(line[8:20]))  # rounds to 4 decimal places, keeping trailing zeros
			peak = '{:.0f}'.format(float(line[21:30]))
			width = '{:.0f}'.format(float(line[33:39]))
			fit_tag_obs = line[73:74].strip() 
		if Xgremlin_cln == False:
			line = line.split(",")
			waveNum 	= '{:.4f}'.format(float(line[csv_index_wn]))  # rounds to 4 decimal places, keeping trailing zeros
			peak 		= '{:.0f}'.format(float(line[csv_index_peak]))
			width 		= '{:.0f}'.format(float(line[csv_index_width]))
			fit_tag_obs = line[csv_index_fittag].strip() 
			
		waveLength = (1 / (float(waveNum) * 100)) * (10**10)  # convert to vac wavenumber (angstroms)
		if float(waveNum) < 50000.0 :  waveLength =  vacToAir(waveLength)
		waveLength = '{:.4f}'.format(waveLength)

		key = '{:>6s}'.format(peak) + '{:>4s}'.format(width) +\
						  '{:>11s}'.format(waveLength)		  
		cln_dict[key] = [peak, width, waveLength, waveNum, fit_tag_obs]	
	return cln_dict
	
	
def create_unc_dict():
	""" create the dictionary of the unc file.
	The key is the wavenumber (rounded to 4dp)"""

	file_open = open(unc_file, "r")  # input linelist file
	linelist = file_open.readlines(); file_open.close()

	if csv_format == False:
		linelist = linelist[3:]
	if csv_format == True:
		linelist = [i for i in linelist if i[0] != "#"]
	
	unc_dict = {}
	for line in linelist:
		if csv_format == False:
			line = line.strip("\n").split("\t")
			wavenumber 	= line[1].strip(" ")
			wavenumber	= '{:.4f}'.format(float(wavenumber))
			total_unc 	= line[3]
		if csv_format == True:
			line = line.strip().split(",")
			wavenumber 	= '{:.4f}'.format(float(line[unc_index_wn]))
			total_unc 	= line[unc_index_tot].strip()
		unc_dict[wavenumber] = [total_unc]
	return unc_dict
	

def prob_lines():
	""" This function loads up the problem lines from the 
	'bad lines' file """
	open_file 	= open(badln_file, "r")  # input linelist file
	file_data 	= open_file.readlines();	open_file.close()
	prob_list 	= [i for i in file_data if i[0] != "#"]
	prob_lines = []
	for prob_line in prob_list:
		prob_line = [i.strip(" ") for i in prob_line.strip().split(",")]
		wavenum   = prob_line[badln_index_wn]
		wavenum	  = '{:.4f}'.format(float(wavenum))
		prob_tag  = prob_line[badln_index_tag]
		prob_lines.append([wavenum, prob_tag])
	return prob_lines	
	

def update_cln0():
	"""  This fucntion 'updates' the spectral lines' details from the 
	cln file with uncertainty information (in the cln_dict) """
	cln_dict = create_cln_dict()
	unc_dict = create_unc_dict()

	prob_lines_list = prob_lines()
	
	for cln_key in cln_dict:
		[peak, width, waveLength, waveNum, fit_tag_obs] = cln_dict[cln_key]
		[total_unc] = unc_dict[waveNum]		; prob_tag = ""
		for prob_line in prob_lines_list: 
			if prob_line[0] == waveNum: prob_tag += prob_line[1] 
		cln_dict[cln_key] = [[peak, width, waveLength, waveNum, fit_tag_obs, total_unc, prob_tag]]
	return cln_dict, unc_dict


########################################################################
########################################################################

def run_STRANS():
	
	cur_location = os.getcwd()
	os.chdir(cur_location + "/" + path_to_STRANS)

	file_open = open("strans.bat.inp", "w") 
	
	file_open.write(STRANS_inp + "\n")
	file_open.write(STRANS_out_dat + "\n")
	file_open.write(STRANS_out_lines + "\n")
	file_open.close()
	
	os.system("./strans.bat")
	os.chdir(cur_location)



########################################################################
########################################################################

def bad_ids():
	badid_file 	= open(badid_filename, "r")  # input linelist file
	badid_list 	= badid_file.readlines();	badid_file.close()
	badid_list 	= [i for i in badid_list if i[0] != "#"]
	badids = []
	for badid_line in badid_list:
		badid_line = [i.strip() for i in badid_line.strip().split(",")]
		badids.append(badid_line)
	return badids	


def update_cln_singleion(cln_dict, unc_dict):
	""" Adds to the cln_dict all the identifications """
	badids = bad_ids()  ; badid_len = 0  
	
	""" IF IT IS NOT WORKING, CHANGE THE EXCEPTION? THEN RE-RUN IT """
	file_open 		= open(STRANS_out_lines, 'r') 
	all_lines 		= file_open.readlines() ; file_open.close()
	for data_line in all_lines:
		badid_true = False
		
		transtion_txt = data_line[56:].strip("\n")
		transtion_txt = transtion_txt[:transtion_txt.index("*")] + \
					" " + transtion_txt[transtion_txt.index("*")+1:]

		level_wn = data_line[29:40] ; wn_diff = data_line[40:48]
		data_line_keep = [ion, level_wn, wn_diff] + [transtion_txt]
		strans_trans = [i.strip(" ") for i in " ".join(data_line_keep[-1].split("-")).split(" ") if i != ""]

		for badid_line in badids:
			trans_badid = [i.strip(" ") for i in " ".join(badid_line[-1].split("-")).split(" ") if i != ""]
			if strans_trans == trans_badid:
				badid_len +=1 ; badid_true = True
				
		if badid_true == False: 
			cln_dict[data_line[:21]].append(data_line_keep)

	print(str(len(badids)) +  " bad identification(s) found in file.\n" + \
			str( badid_len) + " bad identification(s) removed. ")
	return cln_dict, unc_dict
	


########################################################################
########################################################################
########################################################################
########################################################################
########################################################################
########################################################################
########################################################################

def format_cln0(cln0):
	""" This formats the spectral line details for the merged linelist
	"""
	[peak, width, waveLength, waveNum, fit_tag_obs,\
						total_unc, prob_tag] = cln0
	 
	format_list = ['{:>4s}'.format(peak), '{:>4s}'.format(width), \
			'{:>11s}'.format(waveLength), '{:>11s}'.format(waveNum), \
			'{:>3s}'.format(fit_tag_obs), \
			'{:>9s}'.format(total_unc), '{:>2s}'.format(prob_tag)]
	return_text = "\t".join(format_list)
	return return_text

def format_match(match):
	""" This formats the line identifications for the merged linelist
	"""
	[ion,level_wn, wn_diff, transtion_txt] = match
	format_list = ['{:>4s}'.format(ion) , \
					  '{:>12s}'.format(level_wn) ,\
					  '{:>9s}'.format(wn_diff) , \
					  '{:>25s}'.format(transtion_txt) ]
	return_text = "\t".join(format_list)
	return return_text
	
	
def create_merged_linelist_file():
	# This cln dictionary will have all the possible line identifications. 
	cln_dict, unc_dict = update_cln_singleion()
	
	merged_file = open("../3_working_files/fe3_STRANSout.mer", "w")  # output merged formatted file
	merged_file.write("File created: " + d.utcnow().isoformat(" ").split(".")[0] + "\n" )
	merged_file.write("from cln: " + cln_header )
	merged_file.write("from unc: " + "".join(unc_header))

	for cln_key in cln_dict:
		data_line = format_cln0(cln_dict[cln_key][0])
		for match in cln_dict[cln_key][1:]:
			data_line += "\t" + format_match(match)
		merged_file.write(data_line + "\n")

	merged_file.close()


########################################################################
########################################################################
########################################################################
########################################################################
########################################################################
########################################################################
########################################################################

# Create LOPT input file.
########################################################################

def create_LOPT(cln_dict, unc_dict, additions = True):	
	global ion	
	LOPT_in_file = open(path_to_LOPT + LOPT_inp, "w") 

	for cln_key in cln_dict:
		[peak, width, waveLength, waveNum, fit_tag_obs, \
					total_unc, prob_tag] = cln_dict[cln_key][0]
		for match in cln_dict[cln_key][1:]:
			
			if match[0] == ion:
				if len(cln_dict[cln_key][1:]) > 1:
					tag = "DoubleID" ; total_unc = "2.0"
				else: tag = ""
				if prob_tag != "": total_unc = "3.0"

				[ion,level_wn, wn_diff, transtion_txt] = match
				
				transtion_txt =  "".join(transtion_txt.split("-"))
				total_unc = '{:.4f}'.format(float(total_unc))

				format_list = ['{:>9s}'.format(peak) , \
					  '{:>15s}'.format(waveNum) , " cm-1", \
					  '{:>7s}'.format(total_unc) , \
					  '{:>23s}'.format(transtion_txt), "     ", \
					  '{:<2s}'.format(prob_tag[:1]) ]
				return_text = "".join(format_list)
				
				LOPT_in_file.write(return_text + "\n")
								
				cln_dict[cln_key][0] = [peak, width, waveLength, waveNum, \
						fit_tag_obs, total_unc, prob_tag + " " + tag] 
	LOPT_in_file.write(additional_lopt)
	LOPT_in_file.close()

"""
Problem lines and bad ids should have been removed, have been checked. 


Checks need to be made:
1. Has the line or blend been stated as unlikely? These lines are found in 
   the incorrect identification file: fe203r.badid
   
2. Remove lines that are a "problem", lines that are bad in the spectrum. 
   These will be identified in the output of LOPT.
   The file name is fe203r.badln
   
   
   feed the matches through file one and the JCP lines throught the 2.
"""



########################################################################
########################################################################
########################################################################
########################################################################
########################################################################
########################################################################


########################################################################



def run_LOPT():
	cur_location = os.getcwd()
	os.chdir(cur_location + "/" + path_to_LOPT)
	os.system("perl LoptJava.pl " + LOPT_param_file)
	os.chdir(cur_location)

	
def reformat_LOPT_output():
	
	file_open 		= open(path_to_LOPT + LOPT_out_lev, 'r') 
	all_lines 		= file_open.readlines()
	file_open.close()
	file_header 	= all_lines[:1]
	file_data 		= all_lines[1:]
	
	levels_header = file_header[0].strip("\n").split("\t")
	levels_header[0] = "Configuration"
	levels_header[1] = "Energy (cm-1)"
	levels_header = levels_header[:4] + levels_header[5:]
	
	levels_header_str = ['{:<14s}'.format(i) for i in levels_header]
	levels_header_str = "".join(levels_header_str)	
	levels_data 	  = [i.strip("\n").split("\t") for i in file_data]
	
	levels_dict = OrderedDict()
	for data_line in levels_data:
		data_line = data_line[:4] + data_line[5:]
		levels_dict [data_line[0]] = [data_line]
	
	##################################################################
	
	file_open 		= open(path_to_LOPT + LOPT_out_lin, 'r') 
	all_lines 		= file_open.readlines()
	file_open.close()
	file_header 	= all_lines[:1][0].strip("\n").split("\t")
	file_data 		= all_lines[1:]
	
	lines_header = file_header
	lines_header[0] = "SNR"
	lines_header[1] = "Wn_obs(cm-1)"
	lines_header[2] = "tot_Wn_unc"
	lines_header[11] = "d_Wn(Obs-C)"
	#~ lines_header[12] = lines_header[12] + "?"
	
	lines_data = [i.strip("\n").split("\t") for i in file_data]
	
	desired_indices = [0, 1, 2, 11, 13, 14, 15, 16]
	#~ desired_indices = range(15)
	
	for data_point in lines_data:
		lines_header_reduced = []
		data_point_reduced = []
		for des_in in desired_indices:
			data_point_reduced.append(data_point[des_in])
			lines_header_reduced.append(lines_header[des_in])
			
		lines_header_reduced.append("Level")
		
		levels_dict[data_point[13]].append(data_point_reduced + [data_point[14]])
		levels_dict[data_point[14]].append(data_point_reduced + [data_point[13]])
	
	lines_header_reduced = lines_header_reduced[:-5] + lines_header_reduced[-1:]
	lines_header = [""] + lines_header_reduced + ["Tag", "Comment"]
	lines_header_str = ["     " + lines_header[1] + "  "] + \
					   ['{:<14s}'.format(i) for i in lines_header[2:-2]] + \
					   ['{:<5s}'.format(i) for i in lines_header[-2:-1]] + \
					   ['{:<12s}'.format(i) for i in lines_header[-1:]] 
	lines_header_str = "".join(lines_header_str)	
	
	##################################################################	
	##################################################################

	formatted_lopt_out = open(path_to_LOPT + LOPT_out_format, "w") 
	
	for level in levels_dict:
		level_data 	= levels_dict[level][0]
		level_data_str = ['{:<14s}'.format(i) for i in level_data]
		level_data_str = "".join(level_data_str)
		
		lines 		= sorted(levels_dict[level][1:])
		formatted_lopt_out.write("-"* 50 + "\n")
		formatted_lopt_out.write(levels_header_str + "\n")
		formatted_lopt_out.write(level_data_str + "\n\n")
		formatted_lopt_out.write(lines_header_str + "\n")
		
		for lvl_line in lines:
			fit_tag = " " ; blend_tag = "?" ; comment = ""
			cln_dict_matches = []
			
			line_trans = " " * (9 - len(lvl_line[-5])) + lvl_line[-5] + \
						"  " + " " * (9 - len(lvl_line[-4])) + lvl_line[-4]
			line_trans = line_trans.strip(" ")
			for dict_key in cln_dict:
				for match in cln_dict[dict_key][1:]:
					match_trans = "".join(match[-1].strip(" ").split("-")) 
					if line_trans == match_trans:
						cln_dict_matches.append(cln_dict[dict_key])
						
			if len(cln_dict_matches) == 0:
				comment = "No match??"
				lvl_line[2] = '{:.4f}'.format(float(lvl_line[2])) 
			else:
				if len(cln_dict_matches) == 1:
					cln_match = cln_dict_matches[0]
					
				if len(cln_dict_matches) > 1:
					comment = "Multiple matches??  I have written no code for this bit.. "
					
				if len(cln_match[1:]) > 1: 		blend_tag = "B" 
				else: 							blend_tag = " "
				fit_tag = cln_match[0][4]
				comment = cln_match[0][6]

				lopt_wn_tot_unc = '{:.4f}'.format(float(lvl_line[2])) 
				cln_wn_tot_unc = '{:.4f}'.format(float(cln_match[0][5]))
				if lopt_wn_tot_unc == cln_wn_tot_unc: lvl_line[2] = lopt_wn_tot_unc
				elif lopt_wn_tot_unc[0] != "0":	lvl_line[2] = lopt_wn_tot_unc
				else: 					lvl_line[2] = cln_wn_tot_unc
				
				lvl_line[1] = cln_match[0][3]
				ritz_wm 	= float(lvl_line[-2]) - float(lvl_line[-3])
				lvl_line[3] = '{:.4f}'.format(float(lvl_line[1]) - ritz_wm)
								
			tot_wn_unc 	= float(lvl_line[2])
			del_wn 		= float(lvl_line[3])
			if abs(del_wn) >= 1.5 * abs(tot_wn_unc):
					fit_tag = "* " + fit_tag
			else: 	fit_tag = "  " + fit_tag
			
			lvl_line[3] = '{:.4f}'.format(float(lvl_line[3])) 
			if lvl_line[3][0] == "-":	pass
			else: 						lvl_line[3] = " " + lvl_line[3]

			lvl_line = lvl_line[:-5] + lvl_line[-1:]
			lvl_line = [fit_tag] + lvl_line + [blend_tag, comment]
			lvl_line[1] = lvl_line[1].strip(" ")
			data_line_str = [lvl_line[0] + \
							'{:>5s}'.format(lvl_line[1]) + "  "] + \
							['{:<14s}'.format(i) for i in lvl_line[2:-2]] + \
							['{:<5s}'.format(i) for i in lvl_line[-2:-1]] + \
							['{:<12s}'.format(i) for i in lvl_line[-1:]] 
			data_line_str = "".join(data_line_str)
			#~ print(levels_header_str)
			formatted_lopt_out.write(data_line_str + "\n") 
		formatted_lopt_out.write("-"* 50 + "\n\n")
	formatted_lopt_out.close()
		
		

	
########################################################################
########################################################################
########################################################################
########################################################################

def compare_Kurucz():
	Kur_file_location = '../3_working_files/Kurucz/gf2602.lines'
	
	
	lvl1 = "'(4G)4s 5G'" ; lvl2 = "'4p'"
	grep_text = 'grep ' + lvl1 + " " +  Kur_file_location + "| grep " + lvl2
	found_lines = os.system(grep_text)
	
	#~ cur_location = os.getcwd()
	#~ os.chdir(cur_location + "/../4_LOPT/")
	#~ os.system("perl LoptJava.pl fe3_lopt.par")
	#~ os.chdir(cur_location)

	#~ file_open 		= open(', 'r') 
	#~ all_lines 		= file_open.readlines()
	#~ file_open.close()
	#~ file_header 	= all_lines[:1][0]
	#~ file_data 		= all_lines[1:]
	print(found_lines)

#~ compare_Kurucz()
	
########################################################################
########################################################################



if len(path_to_LOPT) > 0:
	if path_to_LOPT[-1] != "/":   path_to_LOPT = path_to_LOPT + "/" 
if len(path_to_STRANS) > 0:
	if path_to_STRANS[-1] != "/": path_to_STRANS = path_to_STRANS + "/" 

""" Run STRANS """
if run_STRANS_true == True: run_STRANS()

""" Gather the data""" 
cln_dict, unc_dict = update_cln0()
if run_STRANS_true == True: 
	cln_dict, unc_dict = update_cln_singleion(cln_dict, unc_dict)

""" Create LOPT input and run LOPT """
create_LOPT(cln_dict, unc_dict)
run_LOPT()
reformat_LOPT_output()
	
print("Finished! :) ")	



########################################################################
########################################################################

