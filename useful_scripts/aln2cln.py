"""
Python 3
@author: Florence Concepcion

This program calibrates an xGremlin writelines output file (.aln), 
with a given calibration factor, creating a calibrated linelist (.cln)
file and uncertainty file. Uncertainty file has wavenumber, statistical 
error, total error (includes calibration error). 
"""

import matplotlib.pyplot as plt
import numpy as np



keff 				= -5.0967E-07
keff_err 			= 1.7313E-08
unc_nave 			= 4.0* np.power(10.0, -8.0)

aln_filename 		= "nfe3.aln"
cln_filename		= "del.cln"
unc_filename		= "del.unc"

########################################################################
########################################################################

def stat_err_obs(fwhm, snr):
	""" returns the statistical error
	snr limited to 100 so as not to give an unreasonable 
	estimate of uncertainty. """
	if snr > 100.0: snr = 100
	return fwhm / (2.0 * snr)


def create_unc_file(keff, keff_err):
	### Uncertainty file writing ###
	cal_file = open(unc_filename, 'w')
		
	cal_file.write('# Correction factor = ' + '{0:.4E}'.format(keff) + '\n')
	cal_file.write('# Calibration uncertainty = ' + '{0:.4E}'.format(keff_err) + '\n')
	cal_file.write('# Line \tWavenumber \tStatisitcal Unc. \tTotal Unc. \n')
		
	# Get the aln feii/fe iii linelist 
	obs_file 		= open(aln_filename, 'r')  # linelist to be calibrated in .cln
	obs_lines_all 	= obs_file.readlines()
	obs_header 		= obs_lines_all[:4]
	obs_lines 		= obs_lines_all[4:]
		
	for line in obs_lines:
		wn_obs = float(line[6:20].strip())
		snr_obs = float(line[21:32].strip())
		fwhm_obs = float(line[31:41].strip()) / 1000.
		
		corrected_wavenum = wn_obs * (1 + keff) # correct wavenumber with correction factor
			
		stat_unc_obs = stat_err_obs(fwhm_obs, snr_obs)														
		calib_unc_obs = unc_nave + (keff_err * corrected_wavenum)  # to propagate the Ar II uncertainties
		
		tot_unc_obs = np.sqrt(np.power(stat_unc_obs, 2) + np.power(calib_unc_obs, 2))  # addition in quadtrature of uncertainties
		
		stat_unc_obs = '{0:.6f}'.format(stat_unc_obs)
		tot_unc_obs = '{0:.6f}'.format(tot_unc_obs)      
			
		cal_file.write(line[2:6] + '\t')
		cal_file.write('{0:.6f}'.format(corrected_wavenum) + '\t')
		cal_file.write(stat_unc_obs + '\t')
		cal_file.write(tot_unc_obs + '\n') 
		
	cal_file.close()


def create_cln(keff, keff_err):
	### .cln calibrated linelist file ###
	obs_file 		= open(aln_filename, 'r')  # linelist to be calibrated in .cln
	obs_lines_all 	= obs_file.readlines()
	obs_header 		= obs_lines_all[:4]
	obs_lines 		= obs_lines_all[4:]
	obs_file.close()

	cln_filedata = open(cln_filename, 'w')

	### Get header and write to .cln file ###
	cln_filedata_header = ''.join(obs_header).split('0.0000000000000000')
	cln_filedata_header = cln_filedata_header[0] + str(keff) + cln_filedata_header[1]
	cln_filedata_header = cln_filedata_header.split("\n")
	cln_filedata_header[0] =  '  wavenumber correction applied. (wavcorr factor =' + str(keff) + " used.)"
	cln_filedata.write("\n".join(cln_filedata_header))
		
	### write out each line from the uncalibrated linelist with the corrected wavenumber ###
	for line in obs_lines:
		wn_obs = float(line[6:20].strip())
		corrected_wavenum = '{0:.6f}'.format((wn_obs) * (1 + keff)) # correct wavenumber with correction factor
		  
		if float(corrected_wavenum) < 10000.0:  # to correct layout of cln files for 4 digit wavenumbers
			space_corr = '   '
		else: 		space_corr = '  '
		cln_filedata.write(line[:6] + space_corr + str(corrected_wavenum) + line[20:])


create_unc_file(keff, keff_err)
create_cln(keff, keff_err)
