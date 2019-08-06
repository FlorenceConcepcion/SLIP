# SLIP
STRANS LOPT Iteration Program

The new code I have currently (06 Aug 2019). These code are particularly tailored to my fe3 work:
+ a_init_db.py : Code to create a database from cln file.
+ b_iter_db.py : Carries a linelist and set of energy levels from a working STRANS input through STRANS and LOPT. It will then also reformat the LOPT output in a mor readable format. 
+ c_save_iter.py : Save the files needed. May need to make 2 code for seperate iteration saves (one for LEVHAMS and one for STRANS > LOPT)


These are more general:

+ useful_scripts/linelist_to_STRANSinp.py : Code to create the linelist section of the STRANS input file from an Xgremlin .cln file or linelist in .csv file.
+ useful_scripts/Elvl_to_STRANSinp.py : Code to create the complete STRANS input (energy levels and linelist) from cln or csv file for linelist and csv file for energy levels. 


"examples" folder provides file samples, displaying appropriate format, etc.  

-------------------------------------------------------------------------------------------




c_save_iter.py saves: 


|file name                |  description |
|-------------------------|-------------------------------------------------------------------------- |
|XXX.cln             		   |      linelist file (as this does change as we find problem lines!)              |   
|spec_db.csv         		   |  	linelist csv                                                                 |
|_________________________|_________________________ |
|XXX.badid           		   |   	file with bad identifications from STRANS                             |      
|XXX.badlin         		    |   	file with bad spectral lines containing reasons why they are bad and a tag   |
|1_init_db.par      		    | 		parameter file for python script a_init_db.py                              |
|2_iter_db.par      		    | 		parameter file for python script b_iter_db.py                            |
|_________________________|_________________________  |
|XXX_work.sinp      		    | 		working STRANS input                                                       |  
|working.lines       		   |   	working STRANS identified lines output                               |       
|working.out         		   |   	working STRANS output, predicted lines                               |        
|_________________________|_________________________  |
|lopt_additions.linp   		 |	lines added manually to LOPT (as certain lines are removed from STRANS inp)  |
|XXX.linp         	    		 | working LOPT input                                                           |
|XXX_lopt.lev     		   		 |  working LOPT output levels identified                                        | 
|XXX_lopt.lin     		   		 |  working LOPT output lines used     |
|                         | Lopt parameter file? |
|working_lopt.out       		|	 formatted LOPT output |                                                       
|_________________________|_________________________  |
| .bat       	    		   	 	|	LEVHAMD: Batch file to run LEVHAMD_64 with input file:        |
| .inp       	    		 	    |	LEVHAMD: This file helps keeps a record of the parameters used  |     
| .lev               		 		|	LEVHAMD: The file containing levels        |
| .lines             		 		|	LEVHAMD: The file containing lines        |
| .out           		     		|	LEVHAMD: The output file containing predicted levels.    |
|_________________________|_________________________ |
| k_alt_label.txt         |  Kurucz alternative label text file    |

 
