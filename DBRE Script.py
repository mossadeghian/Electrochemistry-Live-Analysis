import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import time
import datetime
import sched
# The following inputs will need to be set based on the DBRE configuration #
cycle_time = #amount of seconds between DBRE measurements
reset_time = #an appropriate fraction of cycle time to use when the script loses synchronization
threshold = #decide on value for slope of plateau... or we can find this numerically each time
filename = 'DBRE_1' #will be updated throughout script
# Now, create the dataframe that will store the readings. It will be written to an Excel file after each measurement.

def DBRE_analyzer(filename, cycle_time, reset_time, threshold)
	try #to read the text file
	except #if file is empty, wait reset_time
	time.sleep(cycle_time)
	new_number = str2num(filename[-1]) + 1
	new_filename = filename[:-1]
	new_filename = new_filename + new_number
	DBRE_analyzer(new_filename, cycle_time, reset_time, threshold) #infinite loop

DBRE_analyzer(filename)