import sqlite3
import pandas as pd
import os 
import numpy as np

"""
Key: 
B 		Blended line

"""

parameter_filename = "1_init_db.par"
			   
"""
types of variables: NULL INTEGER REAL TEXT BLOB
NULL. 		The value is a NULL value.
INTEGER. 	The value is a signed integer, stored in 1, 2, 3, 4, 6,
				or 8 bytes depending on the magnitude of the value.
REAL. 		The value is a floating point value, stored as an 8-byte
				IEEE floating point number.
TEXT. 		The value is a text string, stored using the database 
				encoding (UTF-8, UTF-16BE or UTF-16LE).
BLOB. 		The value is a blob of data, stored exactly as it was input.	   
"""		   



def to_csv(database_name, delimiter = ","):
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


########################################################################

def stat_err_obs(fwhm, snr, limit):
	""" returns the statistical error: snr limited to 100 so as not to
	give an unreasonable estimate of uncertainty. """
	fwhm, snr, limit = float(fwhm), float(snr), float(limit)
	if snr > limit:
			snr = limit
	return fwhm / (2.0 * snr)

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
		

def create_table(database_name):
	""" Let's create the database will all the spectral lines and it's 
	properties. """

	conn = sqlite3.connect(database_name)
	c = conn.cursor()
	
	print("Creating database, table name: ", table_name)
	""" To initialise we will need to create the table """
	create_table_txt = "CREATE TABLE "+ table_name + " ("
	
	c.execute(create_table_txt + """line_ID INTEGER UNIQUE,
									wavenumber REAL,
									wn_txt TEXT,
									SNR INTEGER,
									fwhm INTEGER,
									EQ_width REAL,
									fit_tag TEXT,
									stat_err REAL, 
									total_err REAL, 
									matches INTEGER,
									extra_matches TEXT, 
									prob_tag TEXT, 
									LOPT_err TEXT
									)""")
			   
	cln_file = open(cln_filename, 'r')
	cln_data = [i for i in cln_file]; cln_file.close()
	cln_data = cln_data[4:] ; 	i = 0
	for obs_line in cln_data:
		line_ID_i 	= i ; i += 1
		wavenumber 	= float(obs_line[6:20].strip()) 
		snr_obs 	= float(obs_line[21:30].strip())
		fwhm_obs 	= float(obs_line[31:41].strip()) / 1000.
		EQ_width 	= obs_line[49:60].strip()
		fit_tag		= obs_line[73:74].strip() 
		
		if stat_unc_method.split("_")[0] == "FWHM":
			limit = stat_unc_method.split("_")[1]
			stat_unc_obs = stat_err_obs(fwhm_obs, snr_obs, limit)
			
			# to propagate the previous calib uncertainties
			calib_unc_obs = float(Nave_unc) + (float(keff_err) * wavenumber)  # to propagate the Fe II uncertainties
			tot_unc_obs = np.sqrt(np.power(stat_unc_obs, 2) + np.power(calib_unc_obs, 2))  # addition in quadtrature of uncertainties

		#~ print("Florence sort out this error column")
		row_data = (line_ID_i, wavenumber,'{0:.4f}'.format(wavenumber),\
					snr_obs, '{0:.6f}'.format(fwhm_obs), str(EQ_width), \
					fit_tag, '{0:.6f}'.format(stat_unc_obs), \
					'{0:.6f}'.format(tot_unc_obs), 0, "", "", "")
										
		c.execute("INSERT INTO "+ table_name + " VALUES " + str(row_data))

	conn.commit()
	conn.close()
 
def label_neon(match_lim = 0.03):
	open_file = open(Neon_cln, 'r')
	file_data = [i for i in open_file]; open_file.close()
	file_data = [float(i.strip("\n")) for i in file_data]
	c.execute("ALTER TABLE "+ table_name + " ADD COLUMN Neon_tag TEXT;")
	c.execute("ALTER TABLE "+ table_name + " ADD COLUMN Neon_wndiff TEXT;")
	for Ne_wn in file_data: 
		Ne_wn_low 	= str(Ne_wn - match_lim)
		Ne_wn_high 	= str(Ne_wn + match_lim)
		
		
		c.execute("SELECT line_ID, Neon_tag, Neon_wndiff, extra_matches, wavenumber FROM "\
					+ table_name + " WHERE wavenumber < " +\
					Ne_wn_high + " AND wavenumber > " + Ne_wn_low )
		lines = c.fetchall()
		for line in lines: 
			if line[1] == None: 		
				SET_txt = " Neon_tag = 'Ne', Neon_wndiff = round(wavenumber - " +\
								str(Ne_wn) + ", 4), matches = matches + 1 "
			else: 
				extra_matches_txt = line[3] + "'" + "Ne_" + \
						'{0:.4f}'.format(float(line[4]) - float(Ne_wn)) + ",'"
				SET_txt = " extra_matches = " + extra_matches_txt + \
							", matches = matches + 1 "
			c.execute("UPDATE "+ table_name + " SET " + SET_txt + \
									" WHERE line_ID = "	+ str(line[0]) )
	conn.commit()



def create_STRANS_fe1(linelist_filename, path_to_STRANS, match_lim = 0.05):
	
	# output STRANS formatted file created
	stranslevels = open(path_to_STRANS + fe1_sinp, "w") 
	 
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
	
	title = "Fe1 " + linelist_filename
	stranslevels.write(" " + match_lim + flags + "  " + air_vac_change_wave \
						+ "07" + "   " + low_wavelength + "   " + \
						high_wavelength+ "   " + title + "  " + '\n')
	
	# Get the energy list 
	file_open 		= open(fe1_lev, 'r')  
	all_lines 		= file_open.readlines()
	file_header 	= all_lines[:1]
	file_data 		= all_lines[1:]
	
	file_header = file_header[0].strip("\n").split(",")
	file_data 		= [i.strip("\n") for i in file_data][:-1]
	#~ print file_header, len(file_header)

	for data_line in file_data:
		data_line = data_line.split(",")
		data_line = [i.strip('"=') for i in data_line]

		Configuration	= data_line[0]
		Term		 	= data_line[1]
		J 				= data_line[2]
		Energy 			= data_line[3]
		
		"""If J is like a fraction:
		J_float = float(J.split("/")[0])/float(J.split("/")[1])
		"""
		J_str = J + ".0"
		
		if Term[-1] == "*": parity = 1
		else:				parity = 0
		parity = str(parity)
		
		Term = "".join(Term.strip("*").split(" "))
		
		#~ Term = Term.strip(" ").strip("*")
		try:

			# Here we need to round down the number in the brackets of terms
			frac = Term[Term.index("[")+1: Term.index("]")]
			Term = Term[:Term.index("[")] + \
					str(float(frac.split("/")[0])/float(frac.split("/")[1])).split(".")[0] + \
					Term[Term.index("]")+1:]
		except:
			pass
		
		Term = Term + J_str[0]
		
		if Configuration == "":
			Configuration 	= "unk"
			Term 			= "unk"
		try:
			Configuration = ".".join(Configuration.split(" "))
		except: pass
			
		if Configuration == "3d8": Configuration = "d8"
		if Configuration == "3d6.4s2": Configuration = "d6s2"
		if len(Configuration.split(".")) == 1:
			pass
		else:
			Configuration_lis = Configuration.split(".")[1:]
			Configuration_lis = [i.strip(")").strip("(") for i in \
									Configuration.split(".")[1:]]


			new_Configuration_lis = []
			for config in Configuration_lis:
				if config == "3P*": config = "3"
				if config == "1P*": config = "1"
				try:
					frac = config[config.index("<")+1: config.index(">")]
					config = config[:config.index("<")] + \
								str(float(frac.split("/")[0])/float(frac.split("/")[1])).split(".")[0] \
								+ config[config.index(">")+1:]
					
				except:
					pass
				new_Configuration_lis.append(config)
			Configuration_lis = new_Configuration_lis
			

			Configuration = "".join(Configuration_lis).strip("*")		
			try:
				Configuration = Configuration[:Configuration.index("4s4p")] \
								+ "sp" + \
								Configuration[Configuration.index("4s4p")+4:]
			except:
				pass
		
		#~ if len(Configuration) >8: print Configuration, Term
		#~ if len(Term.strip(" ").strip("*")) >3: print Term.strip(" ").strip("*")


		level_label = " " * (7 - len(Configuration)) + Configuration + \
						" " + " " * (5 - len(Term)) + Term

		Energy_0 = " " * (12 - len(Energy.split(".")[0])) + Energy.split(".")[0]
		Energy_1 = Energy.split(".")[1] + " " * (4 - len(Energy.split(".")[1])) 
		Energy_str = Energy_0 + "." + Energy_1

		stranslevels.write(level_label + "   " + J_str+ Energy_str +\
								"       " + parity + '\n')

	stranslevels.write("EOF" + "\n")
	
	spect_linelist = format_cln_STRANSinp()
	for line in spect_linelist:
		stranslevels.write(line)
	
	stranslevels.close()
	
def create_STRANS_fe2(linelist_filename, path_to_STRANS, match_lim = 0.02):						
	""" create the energy levels input for fe2, incl line with tolarance
	""" 
	
	elevel_file 	= open(fe2_lev, "r")  # input energy level list file
	elevel_file_all	= elevel_file.readlines()
	elevel_header 	= elevel_file_all[:19]
	elevels_data	= elevel_file_all[19:]
	elevel_file.close()
	
	# output STRANS formatted file
	#~ stranslevels = open("del.inp", "w")  
	stranslevels = open(path_to_STRANS + fe2_sinp, "w") 

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
	
	title = "Fe2" + linelist_filename
	stranslevels.write(" " + match_lim + flags + "  " + air_vac_change_wave \
						+ "07" + "   " + low_wavelength + "   " + \
						high_wavelength+ "   " + title + "  " + '\n')

	for data_line in elevels_data:
		Configuration = data_line[:20].strip(" ")
		Term_orig = data_line[21:26]
		J = data_line[27:31]
		Energy = data_line[32:43]
		
		J_float = float(J.split("/")[0])/float(J.split("/")[1])
		J_str = str(J_float)
		
		Term = Term_orig.strip(" ").strip("*")
		try:
			Term = Term[:Term.index("[")] + \
						Term[Term.index("[")+1: Term.index("]")] \
						+ Term[Term.index("]")+1:]
		except:
			pass
		
		Term = Term + J_str[0]
		
		if len(Configuration.split(".")) == 1:
			if Configuration == "3d7":	Configuration = "d7"
			else: Configuration = Configuration[-3:] + " "
		else:
			Configuration_lis = Configuration.split(".")[1:] 
			Configuration_lis = [i.strip(")").strip("(") for i in \
										Configuration.split(".")[1:]]
			new_Configuration_lis = []
			for config in Configuration_lis:
				if config == "3P*": config = "3"
				if config == "1P*": config = "1"
				try:
					config = config[:config.index("<")] + \
								config[config.index("<")+1: config.index(">")] +\
								 config[config.index(">")+1:]
				except:
					pass
				new_Configuration_lis.append(config)
			Configuration_lis = new_Configuration_lis
			
			#~ print Configuration_lis
			
			if len(Configuration_lis) == 1:
				Configuration = Configuration_lis[0]
			elif len(Configuration_lis) == 2 or len(Configuration_lis) == 3:
				Configuration = "".join(Configuration_lis)
			else:
				#~ print Configuration_lis
				Configuration = "".join(Configuration_lis).strip("*")		
			try:
				Configuration = Configuration[:Configuration.index("4s4p")] \
								+ "sp" + Configuration[Configuration.index("4s4p")+4:]
			except:
				pass
		
		if Configuration[:2] == "4s":
			Configuration = "s" + Configuration[2:]
		else: pass
		
		#~ if len(Term.strip(" ").strip("*")) >3: print Term.strip(" ").strip("*")
		
		level_label = " " * (8 - len(Configuration)) + Configuration + \
						"" + " " * (5 - len(Term)) + Term
		level_label = " " * 3 + Configuration + \
					" " * (10 - len(Configuration)- len(Term)) + Term



		Energy_0 = " " * (12 - len(Energy.split(".")[0])) + Energy.split(".")[0]
		Energy_1 = Energy.split(".")[1] + " " * (4 - len(Energy.split(".")[1])) 
		Energy_str = Energy_0 + "." + Energy_1
		
		if Term_orig.strip(" ")[-1] == "*":
			parity = 1
		else: parity = 0
		parity = str(parity)
		
		stranslevels.write(level_label + "   " + J_str+ Energy_str +\
									"       " + parity + '\n')
	
	stranslevels.write("EOF" + "\n")
	spect_linelist = format_cln_STRANSinp()
	for line in spect_linelist:
		stranslevels.write(line)
	stranslevels.close()

def create_STRANS_fe3(linelist_filename, path_to_STRANS, match_lim = 0.05):
		
	# output STRANS formatted file created
	stranslevels = open(path_to_STRANS + fe3_sinp, "w") 
	
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
	file_open 		= open(fe3_lev, 'r') 
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
		if len(Configuration) >5 : print (Configuration)
		
		level_label = "    "+ " " * (5 - len(Configuration)) + Configuration + \
						"" + " " * (4 - len(Term)) + Term

		Energy_0 = " " * (12 - len(Energy.split(".")[0])) + Energy.split(".")[0]
		Energy_1 = Energy.split(".")[1] + " " * (4 - len(Energy.split(".")[1])) 
		Energy_str = Energy_0 + "." + Energy_1

		stranslevels.write(level_label + "   " + J_str+ Energy_str +\
									"       " + parity + '\n')

	stranslevels.write("EOF" + "\n")
	spect_linelist = format_cln_STRANSinp()
	for line in spect_linelist:
		stranslevels.write(line)
	stranslevels.close()

########################################################################

########################################################################

def vacToAir(wavelength):
	""" created by C. Clear: 
	convert vac wavelengths to air 
	(from Morton, 2000, ApJ. Suppl., 130, 403) """
	wavelength = float(wavelength)
	s = 10.0**4 / wavelength
	n = 1.0 + 0.0000834254 + (0.02406147 / (130.0 - s**2)) + \
								(0.00015998 / (38.9 - s**2))
	return wavelength/n 
   
def format_cln_STRANSinp():
	""" this formats the STRANS input """

	if cln_to_STRANS_format == "True":
		stransLines = open(cln_to_STRANS_filename, "w")  # output STRANS formatted file
		
	c.execute("SELECT wavenumber, wn_txt, SNR, fwhm FROM " + table_name + "")
	linelist = c.fetchall()

	datalines = []	 
	for line in linelist:
		wavenumber, wn_txt, SNR, fwhm = line
		waveNum = float(wavenumber)  # rounds to 4 decimal places, keeping trailing zeros
		if waveNum == "49994.1138": print ("WARNING LINE 49994.1138 (141) REMOVED")
		else:
			peak = '{:.0f}'.format(float(SNR))
			width = '{:.0f}'.format(float(fwhm)* 1000.)
			waveLength = (1.0 / (float(waveNum) * 100.)) * (10.**10.)  # convert to vac wavenumber (angstroms)
			
			if float(waveNum) < 50000.0 :  # for non-VUV wavelengths
				waveLength =  vacToAir(waveLength)
			waveLength = '{:.4f}'.format(waveLength)
			data_line = '{:>6s}'.format(peak) + '{:>4s}'.format(width) +\
						'{:>11s}'.format(waveLength) + \
						'{:>19s}'.format(wn_txt) + '\n'					
			datalines.append(data_line)
			if cln_to_STRANS_format == "True":
				stransLines.write(data_line)
		
	datalines.append("EOF")
	if cln_to_STRANS_format == "True":
		stransLines.write("EOF")
		stransLines.close()
	return datalines

def run_STRANS(sinp_filename, path_to_STRANS, element_name, working=False):
	cur_location = os.getcwd()
	os.chdir(cur_location + "/" + path_to_STRANS)
	ele = element_name
	print (ele)

	file_open = open("strans.bat.inp", "w") 
	file_open.write(sinp_filename + "\n")
	file_open.write(ele + ".out" + "\n")
	file_open.write(ele + ".lines" + "\n")
	file_open.close()

	os.system("./strans.bat")
	if STRANS_products_loc == "": pass
	else:
		os.system("mv " + ele + ".out " + cur_location + "/" + STRANS_products_loc)
		os.system("mv " + ele + ".lines " + cur_location + "/" + STRANS_products_loc)	
	os.chdir(cur_location)
	
	ele_cols = [element_name, element_name + "_wndiff", element_name+ "_tran"]
	if working == True:
		ele_cols.append(element_name + "_low")
		ele_cols.append(element_name+ "_high")

	conn = sqlite3.connect(database_name)
	c = conn.cursor()
	for col in ele_cols:
		print ("Created col", col)
		c.execute("ALTER TABLE "+ table_name + " ADD COLUMN " + col + " TEXT;")

	file_open 		= open(STRANS_products_loc + ele + ".lines", 'r')  
	all_lines 		= file_open.readlines()
	file_data 		= all_lines
	for data_line in file_data:
		transtion_txt = data_line[56:].strip("\n")
		transtion_txt = " ".join(transtion_txt.split("*"))
		wn_str = data_line[29:40].strip() ; wn_diff = data_line[40:48].strip()
		wn_Ritz = float(wn_str) - float(wn_diff)
		
		if working==False:
			c.execute("SELECT " + element_name + \
						", extra_matches, wn_txt FROM "+\
						table_name + " WHERE wn_txt = " + "'" + wn_str + "'" + " ")
			a = c.fetchall()	;	line = a[0]
			if line[0] == None: 
				SET_txt = element_name + " = '"+ element_name + "', " + \
						element_name + "_wndiff = " + wn_diff + ", " + \
						element_name + "_tran = '" + transtion_txt + "', " + \
						" matches = matches + 1 "
			else: 
				extra_matches_txt = "'" + line[1] + element_name + "_" + \
						wn_diff + "_" + transtion_txt + ",'"
				SET_txt = " extra_matches = " + extra_matches_txt + \
								", matches = matches + 1 "
			c.execute("UPDATE "+ table_name + " SET " + SET_txt + \
						" WHERE wn_txt = " + wn_str )
		if working == True: 
			lower, upper = [i.strip() for i in transtion_txt.split("-")]
			
			SET_txt = element_name + " = '"+ element_name + "', " + \
						element_name + "_wndiff = " + wn_diff + ", " + \
						element_name + "_tran = '" + transtion_txt + "', " + \
						element_name + "_low = '" + lower + "', " + \
						element_name+ "_high = '" + upper + "', " + \
						" matches = matches + 1 "
			c.execute("UPDATE "+ table_name + " SET " + SET_txt + \
							" WHERE wn_txt = '" + wn_str + "' ")
			
	c.execute("SELECT * FROM "+ table_name + " WHERE " +element_name + \
				" ='" + element_name+ "'")
	matched_lines = c.fetchall()	
	print(len(matched_lines), element_name + " lines identified")
	if len(matched_lines) != len(file_data):
		print ("-"*30, "WARNING", len(file_data) - len(matched_lines), "lines not recorded. " )
	conn.commit()


########################################################################
""" Get the parameters """
get_parameters(parameter_filename)
if path_to_STRANS[-1] == "/": pass
else: path_to_STRANS = path_to_STRANS + "/" 
table_name = "spec_db"

""" Only include this in the testing phase. No longer needed """
os.system("rm " + database_name)

########################################################################
""" Connect to database """
conn = sqlite3.connect(database_name)
c = conn.cursor()

""" Create detebase with spectral lines """
create_table(database_name)

########################################################################
""" Label Neon lines (using JCP linelist) """
label_neon()

########################################################################
""" Sort out STRANS identified lines """
linelist_filename = cln_filename.split(".")[0]

""" Create STRANS input for fe1 """
create_STRANS_fe1(linelist_filename, path_to_STRANS=path_to_STRANS)
""" Run STRANS for fe1 """
run_STRANS(fe1_sinp, path_to_STRANS, element_name = "fe1")

""" Create STRANS input for fe2 """
create_STRANS_fe2(linelist_filename, path_to_STRANS=path_to_STRANS)
""" Run STRANS for fe1 """
run_STRANS(fe2_sinp, path_to_STRANS, element_name = "fe2")

#~ """ Create STRANS input for fe2 """
#~ create_STRANS_fe3(linelist_filename, path_to_STRANS=path_to_STRANS)
#~ """ Run STRANS for fe1 """
#~ run_STRANS(fe3_sinp, path_to_STRANS, element_name = "fe3")

########################################################################
""" run STRANS for other desired elements listed in other_element_sinp """

if other_element_sinp == "": pass
else: 
	other_element_sinp = other_element_sinp.split(",")
	other_element_names = other_element_names.split(",")

	for sinp_i, sinp in enumerate(other_element_sinp):
		run_STRANS(sinp, path_to_STRANS, element_name = other_element_names[sinp_i])

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




