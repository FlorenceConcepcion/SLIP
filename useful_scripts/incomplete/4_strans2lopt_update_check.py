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

import os
from datetime import datetime as d
from collections import OrderedDict

from _convertXgrem2strans import vacToAir
from _convertXgrem2strans import create_linelist_STRANSinp

from _create_bat_inp import create_bat_inp
from _create_bat_inp import run_STRANS

########################################################################
########################################################################
########################################################################

# Create the merged linelist including all possible line identifications.
########################################################################

global cln_file
global unc_file
global badln_file
global badid_filename

cln_file = "../1_wn_calib/tmpfe3.cln"
unc_file = "../1_wn_calib/tmpfe3.unc"
badln_file = "../3_working_files/fe3.badln"
badid_filename = "../3_working_files/fe3.badid"


def create_cln_dict(highlight_prob = True):
	""" create the dictionary of the cln file.
	The key is a string formed of the peak, width and wavelength."""
	
	linelist_file = open(cln_file, "r")  # input linelist file

	linelist = linelist_file.readlines()
	cln_header = linelist[0]
	linelist = linelist[4:]
	linelist_file.close()
	
	#~ cln_dict = {}
	cln_dict = OrderedDict()
	for line in linelist: 
		waveNum = '{:.4f}'.format(float(line[8:20]))  # rounds to 4 decimal places, keeping trailing zeros
		peak = '{:.0f}'.format(float(line[21:30]))
		width = '{:.0f}'.format(float(line[33:39]))
		fit_tag_obs = line[73:74].strip() 
		
		waveLength = (1 / (float(waveNum) * 100)) * (10**10)  # convert to vac wavenumber (angstroms)
		
		if float(waveNum) < 50000.0 :  # for non-VUV wavelengths
			waveLength =  vacToAir(waveLength)
			
		waveLength = '{:.4f}'.format(waveLength)
		
		#~ print '{:>6s}'.format(peak) + \
						  #~ '{:>4s}'.format(width) +\
						  #~ '{:>11s}'.format(waveLength) + \
						  #~ '{:>19s}'.format(waveNum) + '\n'
						  
		#~ if line[:21] == 
		key = '{:>6s}'.format(peak) + '{:>4s}'.format(width) +\
						  '{:>11s}'.format(waveLength)
						  
		cln_dict[key] = [peak, width, waveLength, waveNum, fit_tag_obs]
	
	if highlight_prob == True:
		for line_i, line in enumerate(linelist[:-1]): 
			waveNum_current = float(line[8:20]) 
			waveNum_next = float(linelist[line_i + 1][8:20]) 
			if abs(waveNum_next - waveNum_current) < 1.0:
				print "### possible issue with this line!!!"
				print line, linelist[line_i + 1]
				
			
	
	return cln_header, cln_dict

def create_unc_dict():
	""" create the dictionary of the unc file.
	The key is the wavenumber (rounded to 4dp)"""

	file_open = open(unc_file, "r")  # input linelist file

	linelist = file_open.readlines()
	unc_header = linelist[:2]
	unc_header = "; ".join([i.strip("\n") for i in unc_header]) + "\n"

	linelist = linelist[3:]
	file_open.close()
	
	unc_dict = {}
	for line in linelist:
		line = line.strip("\n").split("\t")
		wavenumber 	= line[1].strip(" ")
		wavenumber	= '{:.4f}'.format(float(wavenumber))
		stat_unc 	= line[2]
		total_unc 	= line[3]
		unc_dict[wavenumber] = [stat_unc, total_unc]
	return unc_header, unc_dict



def prob_lines():
	""" This function loads up the problem lines from the 
	'bad lines' file """
	open_file 	= open(badln_file, "r")  # input linelist file
	file_data 	= open_file.readlines();	header 	= file_data[0]
	prob_list 	= file_data[1:]		;	open_file.close()
	prob_lines = []
	for prob_line in prob_list:
		prob_line = prob_line.strip("\n").split("\t")
		prob_line = [i.strip(" ") for i in prob_line]
		if prob_line[0][0] == "#": 	pass
		else: 					prob_lines.append(prob_line)
	return prob_lines	
	
	
def update_cln0():
	"""  This fucntion 'updates' the spectral lines' details from the 
	cln file with uncertainty information (in the cln_dict) """
	cln_header, cln_dict = create_cln_dict()
	#~ print cln_header, cln_dict
	unc_header, unc_dict = create_unc_dict()
	#~ print  unc_header, unc_dict

	prob_lines_list = prob_lines()
	prob_lines_list_4 = [i[:4] for i in prob_lines_list]
	
	for cln_key in cln_dict:
		[peak, width, waveLength, waveNum, fit_tag_obs] = cln_dict[cln_key]
		[stat_unc, total_unc] = unc_dict[waveNum]
		if [peak, width, waveLength, waveNum] in prob_lines_list_4: 
			prob_tag = "P"
		else: prob_tag = " "
		cln_dict[cln_key] = [[peak, width, waveLength, waveNum, fit_tag_obs, stat_unc, total_unc, prob_tag]]
	return cln_header, cln_dict, unc_header, unc_dict

def format_cln0(cln0):
	""" This formats the spectral line details for the merged linelist
	"""
	[peak, width, waveLength, waveNum, fit_tag_obs,\
						stat_unc, total_unc, prob_tag] = cln0
	 
	format_list = ['{:>4s}'.format(peak), '{:>4s}'.format(width), \
			'{:>11s}'.format(waveLength), '{:>11s}'.format(waveNum), \
			'{:>3s}'.format(fit_tag_obs), '{:>9s}'.format(stat_unc),\
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


def bad_ids():
	badid_file 	= open(badid_filename, "r")  # input linelist file
	badid_list 	= badid_file.readlines();	header 	= badid_list[0]
	badid_list 	= badid_list[1:]		;	badid_file.close()
	badids = []
	for badid in badid_list:
		badid = [i for i in badid.strip("\n").split("\t") if i != ""]
		badid = "".join(badid).split(",")
		badid = [i.strip(" ") for i in badid]
		badid[-1] = [i.strip(" ") for i in " ".join(badid[-1].split("-")).split(" ") if i != ""]
		if badid[0][0] == "#": 	pass
		else: 
			badids.append(badid)
	return badids	


def update_cln_all_ids():
	""" Adds to the cln_dict all the identifications 
	"""
	cln_header, cln_dict, unc_header, unc_dict = update_cln0()
	badids = bad_ids()  ; badid_len = 0  
	
	#~ print "\n\nbadids", badids
	#~ print "['fe3', '50089.7600', ' -0.4839', ' 4G4s   5G3 -4G4p   5G2 ']['fe3', '50089.2700', '  0.0061', ' 4G4s   5G2 -4G4p   5G2 ']"
	#~ print "\n\n"
	
	ions = ["fe1", "fe2", "fe3", "ne1", "ne2"]	
	
	""" IF IT IS NOT WORKING, CHANGE THE EXCEPTION? THEN RE-RUN IT """
	for ion in ions:
		if ion == "fe3": file_name = "../3_working_files/tfe3_work.lines" 
		else: file_name = "3_products/tfe3_" + ion +".lines" 
		file_open 		= open(file_name, 'r') 
		all_lines 		= file_open.readlines()
		file_data 		= all_lines
		for data_line in file_data:
			transtion_txt = data_line[56:].strip("\n")
			transtion_txt = transtion_txt[:transtion_txt.index("*")] +" " + transtion_txt[transtion_txt.index("*")+1:]
			
			data_line_list = [i for i in data_line.strip("\n").split(" ") if i!= ""]
			wn, wn_diff = data_line_list[4:6]
			wn = data_line[29:40] ; wn_diff = data_line[40:48]
			#~ level_wn = '{:.4f}'.format(float(wn) - float(wn_diff))
			level_wn = wn
			data_line_keep = [ion,level_wn, wn_diff] + [transtion_txt]
			# This removes bad identifications (unlikely or a bad blend ID), listed in badid file 
			#~ print data_line_keep[:]
			
			line_test = [i.strip(" ") for i in data_line_keep]
			line_test[-1] = [i.strip(" ") for i in " ".join(line_test[-1].split("-")).split(" ") if i != ""]
			line_test = line_test[:2] + [line_test[-1]]
			#~ print line_test[1], data_line[29:40].strip(" ")
			#~ if line_test[1].split(".")[0] == "50089":
				#~ print line_test, badids
			if line_test in badids:
				#~ print "removed", line_test
				badid_len +=1
			else: 
				#~ print cln_dict.keys()
				#~ '    10 398  1994.3789'
				#~ "cln_dict keys are from the cln file'and data line is
				#~ from .lines files"
				cln_dict[data_line[:21]].append(data_line_keep)
	print str(len(badids)) +  " bad identification(s) found in file.\n" + \
			str( badid_len) + " bad identification(s) removed. "
	return cln_header, cln_dict, unc_header, unc_dict
	
def create_merged_linelist_file():
	# This cln dictionary will have all the possible line identifications. 
	cln_header, cln_dict, unc_header, unc_dict = update_cln_all_ids()
	
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

def create_LOPT(additions = True):	
	
	LOPT_in_file = open("../4_LOPT/fe3_work_LOPT.inp", "w")  # output merged formatted file
	#~ LOPT_in_file = open("fe203r_LOPT_4G.inp", "w")  # output merged formatted file

	cln_header, cln_dict, unc_header, unc_dict = update_cln_all_ids()
	for cln_key in cln_dict:
		[peak, width, waveLength, waveNum, fit_tag_obs, \
					stat_unc, total_unc, prob_tag] = cln_dict[cln_key][0]
		for match in cln_dict[cln_key][1:]:
			
			if match[0] == "fe3":
				if len(cln_dict[cln_key][1:]) > 1:
					tag = "B" ; total_unc = "2.0"
				else: 
					tag = ""
				
				if prob_tag == "P":
					total_unc = "3.0"
				 	
				
				[ion,level_wn, wn_diff, transtion_txt] = match
				
				
				transtion_txt =  "".join(transtion_txt.split("-"))
				""" # When the transition text was formatted differently
				# in the STRANS inp file.
				new_transtion_txt = []
				for txt in transtion_txt.split("-"):
					if txt[-5] == " ":
						txt = 	txt[:-5] + txt[-4:]
						new_transtion_txt.append(txt)
					else:
						print "REMOVING CHARACTER OF TRANSTION TEXT:", txt	
				transtion_txt = " ".join(new_transtion_txt)
				"""
				
				total_unc = '{:.4f}'.format(float(total_unc))

				format_list = ['{:>9s}'.format(peak) , \
					  '{:>15s}'.format(waveNum) , " cm-1", \
					  '{:>7s}'.format(total_unc) , \
					  '{:>23s}'.format(transtion_txt), "     ", \
					  '{:<2s}'.format(tag) ]
				return_text = "".join(format_list)
						
				LOPT_in_file.write(return_text + "\n")
	
	LOPT_in_file.write("     9999     63425.4900 cm-1 0.0001  gr          4G4s 5G6        " + "\n")
	LOPT_in_file.write("     9999     70694.1700 cm-1 0.0001  gr          4G4s 3G5")
	if additions == True: 
		#~ pass
		LOPT_in_file.write("      194     50089.2761 cm-1 0.0025  4G4s  5G2  4G4p  5G2 " + "\n")

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



#~ create_LOPT()

########################################################################
########################################################################
########################################################################
########################################################################
	
def create_STRANS_fe3_limited(limited = True, \
						linelist_filename = "tfe3", match_lim = 0.20,\
						product_folder = "", \
						product_file = "tfe3_work_autogenerated.inp"):
	
	""" THIS SHOULD USE THE SAME/SIMILAR CODE TO convertLinelisttoSTRANS.py
	"""
	
	
	# output STRANS formatted file
	stranslevels = open(product_folder + product_file, "w") 
	 	
	# set the tolerance
	match_lim = str(match_lim)
	if len(match_lim) < 5:
		match_lim = match_lim + "0" * (5 - len(match_lim))
	
	del_S_flag = 0 ; del_J_flag = 1 ; Parent_flag = 0
	flags = str(del_S_flag) + str(del_J_flag) + str(Parent_flag)

	air_vac_change_wave = 2000.
	air_vac_change_wave = str(air_vac_change_wave).split(".")[0] + "."
	
	low_wavelength = 1700.
	low_wavelength = str(low_wavelength).split(".")[0] + "."
	high_wavelength = 3000.
	high_wavelength = str(high_wavelength).split(".")[0] + "."
	
	title = "Fe3 " + linelist_filename
	stranslevels.write(" " + match_lim + flags + "  " + air_vac_change_wave \
						+ "07" + "   " + low_wavelength + "   " + \
						high_wavelength+ "   " + title + "  " + '\n')
	
	# Get the energy list 
	file_open 		= open("1_input/Ekberg_levels.dat", 'r') 
	all_lines 		= file_open.readlines()
	file_header 	= all_lines[:1]
	file_data 		= all_lines[1:]
	
	file_header = file_header[0].strip("\n").split(",")
	file_data 		= [i.strip("\n") for i in file_data]
	
	for data_line in file_data:
		data_line = data_line.split(",")
		data_line = [i.strip(' ') for i in data_line]

		outer_e				= data_line[0]
		Parent_Term		 	= data_line[1]
		Energy 				= data_line[2]
		J 					= Parent_Term[-1]
		
		"""If J is like a fraction:
		J_float = float(J.split("/")[0])/float(J.split("/")[1])
		"""
		J_str = J + ".0"
		
		if outer_e == "3d6": parity = 0 ; outer_e = "d6"
		if outer_e == "4s": parity = 0
		if outer_e == "4p": parity = 1
		parity = str(parity)

		try:
			Parent = Parent_Term.split(")")[0][1:]
			Term = Parent_Term.split(")")[1]
		except:
			Parent = "" ; Term = Parent_Term
			
		
		Configuration = Parent + outer_e

		#~ level_label = " " * (7 - len(Configuration)) + Configuration + \
						#~ " " + " " * (5 - len(Term)) + Term
		level_label = "    "+ " " * (5 - len(Configuration)) + Configuration + \
						"" + " " * (4 - len(Term)) + Term
						
		Energy_0 = " " * (12 - len(Energy.split(".")[0])) + Energy.split(".")[0]
		Energy_1 = Energy.split(".")[1] + " " * (4 - len(Energy.split(".")[1])) 
		Energy_str = Energy_0 + "." + Energy_1

		if limited == True:
			if Parent == "4P":
				stranslevels.write(level_label + "   " + J_str+ Energy_str + "       " + parity + '\n')
		else:
			stranslevels.write(level_label + "   " + J_str+ Energy_str + "       " + parity + '\n')

	stranslevels.write("EOF" + "\n")
	
	fe203r_linelist = create_linelist_STRANSinp()
	for line in fe203r_linelist:
		stranslevels.write(line)
	
	stranslevels.close()



########################################################################
########################################################################

def copy_working(working_filename):
		
	ele = working_filename.split(".")[0]
	os.system("cp 3_products/" + ele + ".out ../3_working_files/")
	os.system("cp 3_products/" + ele + ".lines ../3_working_files/")


def run_LOPT():
	cur_location = os.getcwd()
	os.chdir(cur_location + "/../4_LOPT/")
	os.system("perl LoptJava.pl fe3_lopt.par")
	os.chdir(cur_location)

	
def reformat_LOPT_output():
	
	file_open 		= open("../4_LOPT/fe3_lopt.lev", 'r') 
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
	
	file_open 		= open("../4_LOPT/fe3_lopt.lin", 'r') 
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
	
	cln_header, cln_dict, unc_header, unc_dict = update_cln_all_ids()
	
	##################################################################

	formatted_lopt_out = open("../3_working_files/fe3_formatLOPT.out", "w") 
	
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
			
			line_trans = " " * (9 - len(lvl_line[-5])) + lvl_line[-5] +"  " + " " * (9 - len(lvl_line[-4])) + lvl_line[-4]
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
					min_wn_diff = []
					for spect_line in cln_dict_matches:
						min_wn_diff.append(abs(float(lvl_line[1])- float(spect_line[0][3])))
					cln_match = cln_dict_matches[min_wn_diff.index(min(min_wn_diff))]
					
				if len(cln_match[1:]) > 1: 		blend_tag = "B" 
				else: 							blend_tag = " "
				fit_tag = cln_match[0][4]
				comment = cln_match[0][7]

				lopt_wn_tot_unc = '{:.4f}'.format(float(lvl_line[2])) 
				cln_wn_tot_unc = '{:.4f}'.format(float(cln_match[0][6]))
				if lopt_wn_tot_unc == cln_wn_tot_unc: lvl_line[2] = lopt_wn_tot_unc
				elif lopt_wn_tot_unc[0] != "0":	lvl_line[2] = lopt_wn_tot_unc
				else: 					lvl_line[2] = cln_wn_tot_unc
				
				lvl_line[1] = cln_match[0][3]
				ritz_wm 	= float(lvl_line[-2]) - float(lvl_line[-3])
				lvl_line[3] = '{:.4f}'.format(float(lvl_line[1]) - ritz_wm)
				
				#~ print lvl_line
				
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
			#~ print levels_header_str
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
	print found_lines

#~ compare_Kurucz()
	
########################################################################
########################################################################
########################################################################
########################################################################

create_merged_linelist_file()


""" This creates a LOPT input file limited by a certain parent file. 
The product file is 'tfe3_work_autogenerated.inp'.  """
#~ create_STRANS_fe3_limited()

""" Now, manually, using the auto generated file, check the 
'tfe3_work.inp'
input file has the levels you want, 
(assuming you wont want ALL terms from a single parent).  """
############### FROM HERE #####################
create_STRANS_fe3_limited(limited = True)

working_filename = "tfe3_work.inp"

create_bat_inp(working_filename)
run_STRANS(working_filename)

""" Let's run STRANS and let's copy the produced files into the 
'../3_working files' folder. """

copy_working(working_filename)

""" Create LOPT input file in the '../4_LOPT/' folder"""
create_LOPT(additions = False)

""" Now let's run LOPT"""
run_LOPT()
""" and make the output file readable. """
reformat_LOPT_output()


create_merged_linelist_file()

########################################################################
########################################################################
########################################################################
########################################################################

