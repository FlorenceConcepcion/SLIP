global air_vac_change_wave
global low_wavelength
global high_wavelength


######################################################################
file_type				= "cln"				# cln or csv file


# if file type is csv
delimiter 				= ","				
waveNum_col				=  0	# column number with wavenumber, starting at 0
SNR_col					=  1	# column number with SNR value, starting at 0
fwhm_col 				=  2	# column number with FWHM, starting at 0
skip_lines				=  0	# number of lines to skip (


input_filename           = "../tmpfe3.cln"  # Calibrated linelist as output from Xgremlin
Elvl_to_STRANS_filename  = "tmpfe3.sinp" # If True, name of filename created
Elvl_to_STRANS_filename  = "tmpE.del" # If True, name of filename created

#### Energy level file
elvl_filename 			= "Fe3_Kurucz.csv" 	# Put # before lines that dont contain data
delimiter 				= ","				# Either set as character or None
# None: if file is not seperated by a delimiter, but instead columns are at set characters

# Either column number (starting at 0) or character limits (["0,3"]) 
elvl_label_col			= 0				
J_col					= 1
elvl_value_col			= 2
parity_col 				= 3

air_vac_change_wave		= 2000. 		# Keep at 2000. 
low_wavelength 			= 1700.			# Lowest wavelength in linelist
high_wavelength 		= 3000.			# Highest wavelength in linelist

element					= "Fe3"
######################################################################

air_vac_change_wave = str(air_vac_change_wave).split(".")[0] + "."
low_wavelength = str(low_wavelength).split(".")[0] + "."
high_wavelength = str(high_wavelength).split(".")[0] + "."

######################################################################

def format_J(J_value):
	try:
		a 		= [float(i) for i in J_value.split("/")]
		J_value = str(a[0]/a[1])
	except: 
		J_value = str(float(J_value))
	return J_value

def create_elvl_STRANSinp(match_lim = 0.05):
	# output STRANS formatted file created
	stranslevels = open(Elvl_to_STRANS_filename, "w") 	
	
	match_lim = str(match_lim)
	if len(match_lim) < 5:
		match_lim = match_lim + "0" * (5 - len(match_lim))

	del_S_flag = 0 ; del_J_flag = 1 ; Parent_flag = 0
	flags = str(del_S_flag) + str(del_J_flag) + str(Parent_flag)
	
	title = element + " " + Elvl_to_STRANS_filename.split(".")[0]
	stranslevels.write(" " + match_lim + flags + "  " + air_vac_change_wave \
						+ "07" + "   " + low_wavelength + "   " + \
						high_wavelength+ "   " + title + "  " + '\n')
	
	# Get the energy list 
	file_open 		= open(elvl_filename, 'r') 
	all_lines 		= file_open.readlines()
	file_data 		= [i for i in all_lines[:] if i[0] != "#"]
	file_data 		= [i.strip("\n") for i in file_data]
	file_data 		= [i for i in file_data if i != ""]
	
	for data_line in file_data:
		data_line = data_line.split(",")
		data_line = [i.strip(' ') for i in data_line]
		
		elvl_label	= data_line[elvl_label_col]
		J_value		= data_line[J_col]
		Energy		= data_line[elvl_value_col]
		parity		= data_line[parity_col]



		if len(elvl_label) > 9:
			print ("WARNING: Level labels must be 9 characters or less:", \
					elvl_label)
		try:
			Energy.index(".")
		except: 
			Energy = str(float(Energy))
		
		level_label = "    " + '{:>9s}'.format(elvl_label) 
		Energy_0 = " " * (12 - len(Energy.split(".")[0])) + Energy.split(".")[0]
		Energy_1 = Energy.split(".")[1] + " " * (4 - len(Energy.split(".")[1])) 
		Energy_str = Energy_0 + "." + Energy_1

		stranslevels.write(level_label + "   " + format_J(J_value) \
					+ Energy_str + "       " + parity + '\n')

	stranslevels.write("EOF" + "\n")

	if file_type == "cln": spect_linelist = create_linelist_STRANSinp()
	if file_type == "csv": spect_linelist = create_STRANSinp_from_csv()
	for line in spect_linelist:
		stranslevels.write(line)
	stranslevels.close()

def vacToAir(wavelength):
	""" created by C. Clear: 
	convert vac wavelengths to air 
	(from Morton, 2000, ApJ. Suppl., 130, 403) """
	wavelength = float(wavelength)
	s = 10.0**4 / wavelength
	n = 1.0 + 0.0000834254 + (0.02406147 / (130.0 - s**2)) + \
								(0.00015998 / (38.9 - s**2))
	return wavelength/n 
   
def create_linelist_STRANSinp():
	""" this converts the Xgremlin linelist into STRANS input """
	linelist_file = open(input_filename, "r")  # input linelist file					 
	linelist = linelist_file.readlines(); linelist_file.close()
		
	spect_linelist = []
	for line in linelist[4:]:  # ignore header
		waveNum = '{:.4f}'.format(float(line[8:20]))  # rounds to 4 decimal places, keeping trailing zeros
		peak = '{:.0f}'.format(float(line[21:30]))
		width = '{:.0f}'.format(float(line[33:39]))
		waveLength = (1.0 / (float(waveNum) * 100)) * (10**10)  # convert to vac wavenumber (angstroms)
		
		if float(waveNum) < 50000.0 :  # for non-VUV wavelengths
			waveLength =  vacToAir(waveLength)
			waveLength = '{:.4f}'.format(waveLength)
			if float(waveLength) < 2000.:
				print ("LINE OMITTED: wavenumber, " + waveNum + \
									"; wavelength, " + waveLength)
			else:		
				spect_linelist.append('{:>6s}'.format(peak) +
								  '{:>4s}'.format(width) +
								  '{:>11s}'.format(waveLength) + 
								  '{:>19s}'.format(waveNum) + '\n')
		else:
			waveLength = '{:.4f}'.format(waveLength)
			spect_linelist.append('{:>6s}'.format(peak) +
								  '{:>4s}'.format(width) +
								  '{:>11s}'.format(waveLength) + 
								  '{:>19s}'.format(waveNum) + '\n')

	spect_linelist.append("EOF")
	return spect_linelist



def create_STRANSinp_from_csv():
	""" Convert linelist in csv file into STRANS inp """
	linelist_file 	= open(csv_filename, "r")  # input linelist file
	spect_linelist = []

	linelist = linelist_file.readlines(); linelist_file.close()
	linelist = [i for i in linelist if i.strip() ! = ""]
	for line in linelist[skip_lines:]:  # ignore header
		line = line.split(delimiter)
		waveNum = line[waveNum_col].strip()
		peak 	= line[SNR_col].strip()
		width 	= line[fwhm_col].strip()
		waveNum = '{:.4f}'.format(float(waveNum))  # rounds to 4 decimal places, keeping trailing zeros
		peak = '{:.0f}'.format(float(peak))
		width = '{:.0f}'.format(float(width))
		waveLength = (1.0 / (float(waveNum) * 100)) * (10**10)  # convert to vac wavenumber (angstroms)
		
		if float(waveNum) < 50000.0 :  # for non-VUV wavelengths
			waveLength =  vacToAir(waveLength)
			waveLength = '{:.4f}'.format(waveLength)
			if float(waveLength) < 2000.:
				print ("LINE OMITTED: wavenumber, " + waveNum + \
									"; wavelength, " + waveLength)
			else:		
				spect_linelist.append('{:>6s}'.format(peak) +
								  '{:>4s}'.format(width) +
								  '{:>11s}'.format(waveLength) + 
								  '{:>19s}'.format(waveNum) + '\n')
		else:
			waveLength = '{:.4f}'.format(waveLength)
			spect_linelist.append('{:>6s}'.format(peak) +
								  '{:>4s}'.format(width) +
								  '{:>11s}'.format(waveLength) + 
								  '{:>19s}'.format(waveNum) + '\n')


	spect_linelist.append("EOF")
	return spect_linelist

	
########################################################################


create_elvl_STRANSinp()



