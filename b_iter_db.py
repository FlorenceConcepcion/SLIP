import sqlite3
import pandas as pd
import os 
from a_init_db import run_STRANS
from collections import OrderedDict

"""
Key: 
B 		Blended line (in spectrum)
M		Multiple identifications
"""



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
		
def to_csv(database_name, delimiter = "\t"):
	""" This function is used to export the table to a .csv file. 
	The delimiter can be changed (for example to a tab, "\t"). """
	db = sqlite3.connect(database_name)
	cursor = db.cursor()
	cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
	tables = cursor.fetchall()
	for table_name in tables:
		table_name = table_name[0]
		table = pd.read_sql_query("SELECT * from %s" % table_name, db)
		table.to_csv(table_name + '.csv', index=False, sep=delimiter)
	db.close()


########################################################################

def remove_problem_lines():
	""" This function loads up the problem lines from the 
	'bad lines' file """
	open_file 	= open(badln_file, "r")  
	file_data 	= open_file.readlines();
	prob_list 	= file_data[:]		;	open_file.close()
	prob_list	= [i.strip() for i in prob_list]
	prob_list	= [i for i in prob_list if i != ""]
	prob_list	= [i for i in prob_list if i[0] != "#"]
	
	#~ prob_lines = []
	for prob_line in prob_list:
		prob_line = prob_line.split(",")
		wn_str 		= prob_line[0]
		prob_tag 	= prob_line[1]
		SET_txt = " prob_tag = " + "'" + prob_tag + "' , LOPT_err = '3.0'"
		c.execute("UPDATE "+ table_name + " SET " + SET_txt + \
					" WHERE wn_txt = " + wn_str )
	conn.commit()


def remove_badID_lines():
	badid_file 	= open(badid_filename, "r")  # input linelist file
	badid_list 	= badid_file.readlines()
	badid_list 	= badid_list[:]		;	badid_file.close()
	badid_list 	= [i.strip() for i in badid_list]
	badid_list	= [i for i in badid_list if i != ""]
	badid_list	= [i for i in badid_list if i[0] != "#"]

	
	#~ badids = []
	for badid in badid_list:
		badid = [i for i in badid.split(",") if i != ""]
		badid = [i.strip() for i in badid]
		#~ badid[-1] = [i.strip(" ") for i in " ".join(badid[-1].split("-")).split(" ") if i != ""]
		
		wn_str 		= badid[0]
		element_name= badid[1]
		trans 		= badid[2]
		
		c.execute("SELECT " + element_name + \
				", extra_matches, wn_txt, " + element_name + \
				"_tran  FROM "+ \
				table_name + " WHERE wn_txt = " + "'" + wn_str + "'" + " ")
		a = c.fetchall()	;	line = a[0]
		if len(a) > 1: print("WARNING: Multiple entries for ", wn_str)
		""" Firstly let's remove the match if it is in the element 
		column (if). Otherwise, remove the match from the 'extra_matches'
		column (else)."""
		if line[3].strip() == trans.strip():
			SET_txt = element_name + " = '', " + \
					element_name + "_wndiff = '', " + \
					element_name + "_tran = '', " + \
					" matches = matches - 1 "
		else:
			new_extra_matches_list = []
			for trans_match in line[1].split(","):     
				
				trans_match = trans_match.split("_")              
				#~ print (trans_match, trans)               
				if trans_match[0] == "fe3" and \
					trans_match[-1].strip() == trans.strip():
					pass
				else: new_extra_matches_list.append("_".join(trans_match))
			extra_matches_txt = "".join(new_extra_matches_list)
			SET_txt = " extra_matches = '" + extra_matches_txt + \
							"', matches = matches - 1 "
		c.execute("UPDATE "+ table_name + " SET " + SET_txt + \
							" WHERE wn_txt = '" + wn_str  + "'")
	conn.commit()


########################################################################

def create_LOPT_input():

	element_name = "working"
	select_txt = "SNR, wn_txt, total_err, LOPT_err, prob_tag, " + \
					element_name + ", " + element_name + "_wndiff, " + \
					element_name + "_tran "
	c.execute("SELECT " + select_txt + " FROM " + table_name + \
				" WHERE " + element_name + " != ''")
	a = c.fetchall()
	write_data = []
	for line in a:
		[peak, wn_txt, total_err, LOPT_err, prob_tag, \
			working_col, working_col_wndiff, working_col_tran]  = line
		if LOPT_err == "": LOPT_err = total_err
		LOPT_err = '{:.4f}'.format(float(LOPT_err))
		working_col_tran =  "".join(working_col_tran.split("-"))
		peak = str(int(peak))
		format_list = ['{:>9s}'.format(peak) , \
				  '{:>15s}'.format(wn_txt) , " cm-1", \
				  '{:>7s}'.format(LOPT_err) , \
				  '{:>23s}'.format(working_col_tran), "     ", \
				  '{:<2s}'.format(prob_tag) ]
		return_text = "".join(format_list)
		write_data.append(return_text + "\n")
	
	if LOPT_additions == "": pass
	else: 
		additions_file = open(LOPT_additions, 'r')
		add_data = [i for i in additions_file]; additions_file.close()
		add_data = [i for i in add_data if i.strip("\n") != ""]
		add_data = [i for i in add_data if i[0] != "#"]
		for add_row in add_data:
			write_data.append(add_row + "\n")

	LOPT_in_file = open(path_to_LOPT + LOPT_input_filename, "w")  
	for write_line in write_data:
		if write_line == "\n": pass
		else: LOPT_in_file.write(write_line.strip("\n") + "\n")
	LOPT_in_file.close()


def run_LOPT():
	cur_location = os.getcwd()
	os.chdir(cur_location + "/" + path_to_LOPT)
	print(LOPT_par_filename)
	os.system("perl LoptJava.pl " + LOPT_par_filename)
	os.chdir(cur_location)

def return_kurucz_label_dict():
	label_dict = {}
	if Kurucz_alt_label != "":
		file_open 		= open(Kurucz_alt_label, 'r') 
		all_lines 		= file_open.readlines() ; file_open.close()
		all_lines		= [i.strip("\n") for i in all_lines if i[0] != "#"]
		all_lines		= [i for i in all_lines if i != ""]
		for line in all_lines: 
			our_label, k_label = line.split(":")
			label_dict[our_label.strip()] = k_label.strip()
	return label_dict
	
	

def return_mylabel_dict():
	label_dict = {}
	if Kurucz_alt_label != "":
		file_open 		= open(Kurucz_alt_label, 'r') 
		all_lines 		= file_open.readlines() ; file_open.close()
		all_lines		= [i.strip("\n") for i in all_lines if i[0] != "#"]
		all_lines		= [i for i in all_lines if i != ""]
		for line in all_lines: 
			our_label, k_label = line.split(":")
			label_dict[k_label.strip()] = our_label.strip()
	return label_dict
	

def get_Kurucz_line(energy_lvl1, energy_lvl2):
	""" This has been written to work for the fe3 kurucz file """
	elvl_labels = [energy_lvl1, energy_lvl2]
	elvl_labels = [i.strip() for i in elvl_labels]
	J_values	= [i[-1] for i in elvl_labels]
	if J_value_integer   == "True" 	: J_txt = ".0"
	elif J_value_integer == "False" : J_txt = ".5"
	J_values = [i + J_txt for i in J_values]
	parent = [i.split(" ")[0] for i in elvl_labels]
	parent = ["(" + i[:-2] + ")" + i[-2:] for i in parent]
	term = [i.split(" ")[1][:-1] for i in elvl_labels]
	new_elvl_labels = [J_values[i] + " " + v + " " + term[i] \
						for i, v in enumerate(parent)]

	try:  new_elvl_labels[0] = k_label_dict[energy_lvl1]
	except: pass
	try:  new_elvl_labels[1] = k_label_dict[energy_lvl2]
	except: pass
			
	grep_text = 'grep "'+ new_elvl_labels[0] + '" ' + Kurucz_file + \
			' | grep "' + new_elvl_labels[1] + '" > k_line.tmp'
	os.system(grep_text)
	file_open 		= open("k_line.tmp", 'r') 
	all_lines 		= file_open.readlines() ; file_open.close()
	if len(all_lines) == 1: 
		line = all_lines[0].strip("\n")
		line = [i for i in line.split(" ")  if i != ""]
		k_loggf = line[1] ; k_low 	= line[3] ; k_high 	= line[7]
		k_wn	= float(k_high) - float(k_low)
		k_wn_str= '{:.4f}'.format(k_wn)
		if k_loggf[0] == "-" : pass
		else: k_loggf = " " + k_loggf
		return [k_wn_str, k_loggf]
	else:
		print("No Kurucz match found for levels:", energy_lvl1, ",", energy_lvl2)
		return ["", ""]





def get_Kurucz_level_data(e_lvl):
	""" Get the strongest lines predicted by Kurucz from 
	the energy levels we are using.
	This has been written to work for the fe3 kurucz file """
	
	
	headers = [""] 
	
	e_lvl 		= e_lvl.strip()
	J_values	= e_lvl[-1] 
	if J_value_integer   == "True" 	: J_txt = ".0"
	elif J_value_integer == "False" : J_txt = ".5"
	J_values 	= J_values + J_txt 
	parent 		= e_lvl.split(" ")[0]
	parent 		= "(" + parent[:-2] + ")" + parent[-2:]
	term 		= e_lvl.split(" ")[1][:-1] 
	new_e_lvl 	= J_values + " " + parent + " " + term
	
	try:  new_e_lvl = k_label_dict[new_e_lvl]
	except: pass

	grep_text = 'grep "' + new_e_lvl + '" ' + Kurucz_file + ' > k_lvl.tmp'
	os.system(grep_text)
	file_open 		= open("k_lvl.tmp", 'r') 
	all_lines 		= file_open.readlines() ; file_open.close()
	
	lines_for_level = []
	for elvl_i in elvl_list:
		if new_e_lvl == elvl_i: pass
		else:
			for line in all_lines: 
				if elvl_i in line:
					line = line.strip("\n")
					line = [i for i in line.split(" ")  if i != ""]
					k_loggf = line[1] ; k_low 	= line[3] ; k_high 	= line[7]
					k_wn	= float(k_high) - float(k_low)
					k_wn_str= '{:.4f}'.format(k_wn)
					if k_loggf[0] == "-" : pass
					else: k_loggf = " " + k_loggf
					
					try:  elvl_i = my_label_dict[elvl_i]
					except: pass
					lines_for_level.append([elvl_i, k_wn_str, k_loggf])
	
	lines_for_level.sort(key=lambda x: float(x[2]), reverse = True)
	return lines_for_level
		
	
def get_elvl_list_stransinp():
	e_lvl_list = []
	strans_file = open(path_to_STRANS + working_STRANSinp, 'r')
	strans_lines = strans_file.readlines() ; strans_file.close()
	strans_lines = [i.strip("\n") for i in strans_lines]
	strans_lines = [i for i in strans_lines if i != ""]

	for strans_line in strans_lines:
		if len(strans_line.split()) == 5:
			level, term, J, wn, parity = strans_line.split()
			level, term, J = level.strip(), term.strip(), J.strip()
			parent 		= "(" + level[:-2] + ")" + level[-2:]
			term		= term[:-1] ; J_values = J
			new_e_lvl 	= J_values + " " + parent + " " + term
			
			try:  new_e_lvl = k_label_dict[new_e_lvl]
			except: pass
			e_lvl_list.append(new_e_lvl)
	return e_lvl_list
			
	
def reformat_LOPT_output():
	""" Open level LOPT output file """
	file_open 		= open(path_to_LOPT + LOPT_lvls_out, 'r') 
	all_lines 		= file_open.readlines()
	file_open.close()
	file_header 	= all_lines[:1]
	file_data 		= all_lines[1:]
	
	levels_header = file_header[0].strip("\n").split("\t")
	levels_header[0] = "Configuration"
	levels_header[1] = "Energy (cm-1)"
	levels_header = levels_header[:4] + levels_header[5:]
	
	if compare_Kurucz == "True":
		levels_header = levels_header+ ["Kurucz "]
	
	levels_header_str = ['{:<14s}'.format(i) for i in levels_header]
	levels_header_str = "".join(levels_header_str)	
	levels_data 	  = [i.strip("\n").split("\t") for i in file_data]
	
	levels_dict = OrderedDict()
	for data_line in levels_data:
		data_line = data_line[:4] + data_line[5:]
		levels_dict [data_line[0]] = [data_line]
	
	##################################################################
	""" Open lines LOPT output file """
	file_open 		= open(path_to_LOPT + LOPT_lines_out, 'r') 
	all_lines 		= file_open.readlines()
	file_open.close()
	file_header 	= all_lines[:1][0].strip("\n").split("\t")
	file_data 		= all_lines[1:]
	
	lines_header = file_header
	lines_header[0] = "SNR"
	lines_header[1] = "Wn_obs(cm-1)"
	lines_header[2] = "tot_Wn_unc"
	lines_header[11] = "d_Wn(Obs-C)"
	
	lines_data = [i.strip("\n").split("\t") for i in file_data]
	desired_indices = [0, 1, 2, 11, 13, 14, 15, 16]
	
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
	print("headers", lines_header_reduced)

	lines_header = [""] + lines_header_reduced + ["  Tag"]
	lines_header = lines_header[:2] + ["    EQw"] + lines_header[2:]
	lines_header_str = ['{:>5s}'.format(lines_header[1]) + "  "] + \
					   ['{:<10s}'.format(i) for i in lines_header[2:3]] + \
					   ['{:<14s}'.format(i) for i in lines_header[3:-2]] + \
					   ['{:<12s}'.format(i) for i in lines_header[-2:]]  
	lines_header_str = "".join(lines_header_str)	
		
	if compare_Kurucz == "True":
		lines_header_str+= "Kurucz wn    loggf"
		

	##################################################################
	
	#~ cln_header, cln_dict, unc_header, unc_dict = update_cln_all_ids()
	
	##################################################################

	formatted_lopt_out = open(formatted_LOPTout, "w") 
	

	levels_dict.pop('gr', None)
	for level in levels_dict:
		level_data 	= levels_dict[level][0]
		level_data_str = ['{:<14s}'.format(i) for i in level_data]
		level_data_str = "".join(level_data_str)
		""" First item (levels_dict[level][0]) is details of the level.
		The otheres are line details.  """
		lines 		= sorted(levels_dict[level][1:], reverse = True)
		formatted_lopt_out.write("-"* 50 + "\n")
		formatted_lopt_out.write(levels_header_str + "\n")
		formatted_lopt_out.write(level_data_str + "\n")
		
		text_toadd_formatted_lopt_out = []
		if compare_Kurucz == "True":
			lines_for_level = get_Kurucz_level_data(level)

		for lvl_line in lines:
			
			if lvl_line[4] == "gr": pass
			else: 
				element_name = "working"
				select_txt = "SNR, wn_txt, total_err, LOPT_err, prob_tag, fit_tag, matches, EQ_width " 
								#~ element_name + ", " + element_name + "_wndiff, " + \
								#~ element_name + "_tran, " + element_name + "_low, " + \
								#~ element_name + "_high " 
				c.execute("SELECT " + select_txt + " FROM " + table_name + \
							" WHERE " + element_name + "_low = '" + \
							lvl_line[4] + "' AND " + element_name + \
							"_high = '" + lvl_line[5] + "'")		


				a = c.fetchall() 
				

				if len(a) > 1:
					print("WARNING MULTIPLE MATCHES FOUND IN STRANS OUTPUT --")
				if len(a) == 0: 
					print("WARNING NO MATCH, ERROR WHERE FLORENCE WHERE")
					prob_tag = "No match??"
				if len(a) == 1: 
					spectral_line = a[0]
					SNR 		=spectral_line[0]
					wn_txt		=spectral_line[1]
					total_err	=spectral_line[2]
					LOPT_err	=spectral_line[3]
					prob_tag	=spectral_line[4]
					fit_tag		=spectral_line[5]
					matches		=spectral_line[6]
					EQ_width	=spectral_line[7]
					
					matches = int(matches)
					if matches > 1: 
						try: 
							prob_tag.index("M")
						except:
							prob_tag = prob_tag + "M"
					tot_wn_unc 	= float(lvl_line[2])
					del_wn 		= float(lvl_line[3])
					if abs(del_wn) >= 1.5 * abs(tot_wn_unc):
							try:
								prob_tag.index("*")
							except:
								prob_tag = prob_tag + " *" 
	
																
					lopt_wn_tot_unc = '{:.4f}'.format(float(lvl_line[2])) 
					cln_wn_tot_unc = '{:.4f}'.format(float(total_err))
					
					if lopt_wn_tot_unc == cln_wn_tot_unc: lvl_line[2] = lopt_wn_tot_unc
					elif lopt_wn_tot_unc[0] != "0":	lvl_line[2] = lopt_wn_tot_unc
					else: 					lvl_line[2] = cln_wn_tot_unc
					
					lvl_line[1] = wn_txt
					ritz_wm 	= float(lvl_line[-2]) - float(lvl_line[-3])
					lvl_line[3] = '{:.4f}'.format(float(lvl_line[1]) - ritz_wm)

					if lvl_line[3][0] == "-":	pass
					else: 				lvl_line[3] = " " + lvl_line[3]
					
					level_label = lvl_line[-1]
					
					lvl_line = lvl_line[:-5] + lvl_line[-1:]
					lvl_line = lvl_line + [fit_tag, prob_tag]
					lvl_line = lvl_line[:1] + [str(int(EQ_width))] + lvl_line[1:]
					lvl_line[0] = lvl_line[0].strip(" ")
					#~ print (lvl_line)


					data_line_str = ['{:>5s}'.format(lvl_line[0]) + "  "] + \
									['{:>8s}'.format(lvl_line[1]) + "  "] + \
									['{:<14s}'.format(i) for i in lvl_line[2:-3]] + \
									['{:<11s}'.format(i) for i in lvl_line[-3:-2]] + \
									['{:<3s}'.format(i) for i in lvl_line[-2:]]
					data_line_str = "".join(data_line_str)
					

					if compare_Kurucz == "True":						
						e_lvl 		= level_label.strip()
						J_values	= e_lvl[-1] 
						if J_value_integer   == "True" 	: J_txt = ".0"
						elif J_value_integer == "False" : J_txt = ".5"
						J_values 	= J_values + J_txt 
						parent 		= e_lvl.split(" ")[0]
						parent 		= "(" + parent[:-2] + ")" + parent[-2:]
						term 		= e_lvl.split(" ")[1][:-1] 
						new_e_lvl 	= J_values + " " + parent + " " + term
							
						for line_i in lines_for_level:
							if new_e_lvl in line_i:
								[e_label, k_wn_str, k_loggf] = line_i
								data_line_str += "       " + k_wn_str + "   " + k_loggf
								lines_for_level.remove(line_i)

					text_toadd_formatted_lopt_out.append(data_line_str + "\n") 
		
		formatted_lopt_out.write("\n" + lines_header_str + "\n")

		if compare_Kurucz == "True":
			for lin in lines_for_level:
				""" lin [elvl_i, k_wn_str, k_loggf] """
				if float(lin[-1]) < -1.5: pass
				else: formatted_lopt_out.write(" " * 79 + "   ".join(lin) + "\n")	
		formatted_lopt_out.write("\n")
		for asd in text_toadd_formatted_lopt_out: formatted_lopt_out.write(asd)
		
		formatted_lopt_out.write("-"* 50 + "\n\n")
		
	
		
		
	formatted_lopt_out.close()
		
		

	
	
########################################################################
########################################################################
########################################################################
""" Get the parameters """
parameter_filename = "2_iter_db.par"
get_parameters(parameter_filename)
if path_to_STRANS[-1] == "/": pass
else: path_to_STRANS = path_to_STRANS + "/" 
if path_to_LOPT[-1] == "/": pass
else: path_to_LOPT = path_to_LOPT + "/" 
table_name = "spec_db"

########################################################################
""" Kurucz label dict """
global k_label_dict
global my_label_dict
k_label_dict = return_kurucz_label_dict()
my_label_dict = return_mylabel_dict()

global elvl_list
elvl_list = get_elvl_list_stransinp()
########################################################################
""" Connect to database """
conn = sqlite3.connect(database_name)
c = conn.cursor()

########################################################################
""" Run STRANS for the working file """
run_STRANS(working_STRANSinp, path_to_STRANS, "working", working=True)

########################################################################
""" Label problematic lines from spectrum. """
remove_problem_lines()

""" Remove bad identification lines from database. """
remove_badID_lines()

########################################################################
""" Create input file for LOPT program"""
create_LOPT_input()
""" Run LOPT """
print("\nMake sure you have sorted the '.fixed' file for LOPT.\n")
run_LOPT()


""" Reformat LOPT output """
reformat_LOPT_output()	

########################################################################
########################################################################
""" To check things out """ 
#~ c.execute("SELECT * FROM spect_lines WHERE matches > 0")
#~ for i in c.fetchall():
	#~ print("\t".join(['{:>8s}'.format(str(j)) for j in i]))


########################################################################

""" Commite changes to database and close it"""
conn.commit()
conn.close()

########################################################################

""" To export the database to csv format"""
if csv_export == "True": to_csv(database_name= database_name, delimiter = "\t")


########################################################################
