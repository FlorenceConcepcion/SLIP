# SLIP
STRANS LOPT Iteration Program

The new code I have currently (31 July 2019). These code are particularly tailored to my fe3 work:
+ a_init_db.py : Code to create a database from cln file.
+ b_iter_db.py : Carries a linelist and set of energy levels from a working STRANS input through STRANS and LOPT. It will then also reformat the LOPT output in a mor readable format. 
+ c_save_iter.py : Save the files needed. May need to make 2 code for seperate iteration saves (one for LEVHAMS and one for STRANS > LOPT)


These are more general:

+ useful_scripts/linelist_to_STRANSinp.py : Code to create the linelist section of the STRANS input file from an Xgremlin .cln file or linelist in .csv file.
+ useful_scripts/Elvl_to_STRANSinp.py : Code to create the complete STRANS input (energy levels and linelist) from cln or csv file for linelist and csv file for energy levels. 

