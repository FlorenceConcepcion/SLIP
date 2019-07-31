# Choose file type:
file_type				= "cln"				# cln or csv file

input_filename 			= "../tmpfe3.cln"  # Calibrated linelist as output from Xgremlin

# if file type is csv
delimiter 				= ","				
waveNum_col				=  0	# column number with wavenumber, starting at 0
SNR_col					=  1	# column number with SNR value, starting at 0
fwhm_col 				=  2	# column number with FWHM, starting at 0
skip_lines				=  0	# number of lines to skip (

# Strans inp filename
STRANS_filename  = "tmp.del" # If True, name of filename created

use_database			= "False"		# Set true if a database has been made. Do not recommend using. 
database_name           = "wfe3.db"     # Database file name

######################################################################

def vacToAir(wavelength):
	""" created by C. Clear: 
	convert vac wavelengths to air 
	(from Morton, 2000, ApJ. Suppl., 130, 403) """
	wavelength = float(wavelength)
	s = 10.0**4 / wavelength
	n = 1.0 + 0.0000834254 + (0.02406147 / (130.0 - s**2)) + \
								(0.00015998 / (38.9 - s**2))
	return wavelength/n 
 

def create_STRANSinp_from_csv():
	""" Convert linelist in csv file into STRANS inp """
	linelist_file 	= open(csv_filename, "r")  # input linelist file
	stransLines		= open(STRANS_filename, "w")  # output STRANS formatted file
					 
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

	stransLines.write("EOF")
	stransLines.close()

def create_linelist_STRANSinp():
	""" this converts the Xgremlin linelist into STRANS input """
	linelist_file = open(cln_filename, "r")  # input linelist file
	stransLines = open(STRANS_filename, "w")  # output STRANS formatted file
					 
	linelist = linelist_file.readlines(); linelist_file.close()
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
				stransLines.write('{:>6s}'.format(peak) +
								  '{:>4s}'.format(width) +
								  '{:>11s}'.format(waveLength) + 
								  '{:>19s}'.format(waveNum) + '\n')
		else:
			waveLength = '{:.4f}'.format(waveLength)
			stransLines.write('{:>6s}'.format(peak) +
								  '{:>4s}'.format(width) +
								  '{:>11s}'.format(waveLength) + 
								  '{:>19s}'.format(waveNum) + '\n')
	stransLines.write("EOF")
	stransLines.close()

def format_cln_STRANSinp():
	""" this created a file formatted to fit the STRANS input from the 
	database"""
	
	conn = sqlite3.connect(database_name)
	c = conn.cursor()
	table_name = "spec_db"

	stransLines = open(STRANS_filename, "w")  # output STRANS formatted file
		
	c.execute("SELECT wavenumber, wn_txt, SNR, fwhm FROM " + table_name + "")
	linelist = c.fetchall()
	conn.close()

	datalines = []	 
	for line in linelist:
		wavenumber, wn_txt, SNR, fwhm = line
		waveNum = float(wavenumber)  # rounds to 4 decimal places, keeping trailing zeros
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
		stransLines.write(data_line)
		
		if float(waveNum) < 50000.0 :  # for non-VUV wavelengths
			waveLength =  vacToAir(waveLength)
			waveLength = '{:.4f}'.format(waveLength)
			if float(waveLength) < 2000.:
				print ("LINE OMITTED: wavenumber, " + waveNum + \
									"; wavelength, " + waveLength)
			else:		
				datalines.append(data_line)
				stransLines.write(data_line)
		else:
			datalines.append(data_line)
			stransLines.write(data_line)
			
	print("This has not been tested.  ")	
	datalines.append("EOF")
	stransLines.write("EOF")
	stransLines.close()
	return datalines

########################################################################


if file_type == "cln":
	cln_filename = input_filename
	if use_database == "True": format_cln_STRANSinp()
	else: create_linelist_STRANSinp()
	print("Created linelist formatted for STRANS input file, " + cln_to_STRANS_filename + ".")

elif file_type == "csv":
	print("WARNING csv option not yet tested. ")
	csv_filename = input_filename
	print("Created linelist formatted for STRANS input file, " + cln_to_STRANS_filename + ".")
else: 
	print("ERROR DID NOT create STRANS input file, " + cln_to_STRANS_filename + ". Check file_type")








