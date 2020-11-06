import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import time
from datetime import datetime
# The following inputs will need to be set based on the DBRE configuration #
charging_time = 3 #chronopotentiometry time in seconds
cycle_time = 1 #amount of seconds between DBRE measurements. If you'd like to go through a bunch at once, set equal to 1.
reset_time = 300 #an appropriate fraction of cycle time to delay by when the script loses synchronization
threshold = 0.01 #decide on value for slope of plateau... or we can find this numerically each time
filename = 'A_DBRE_#1' #will be updated throughout script
num_measurements = 2 #expected number of files to go through
def DBRE_analyzer(filename, charging_time, cycle_time, reset_time, threshold, num_measurements):
	global df
	try: #to read the text file
		raw_data = pd.read_csv(filename + '.DTA',sep = '\t',header = None, usecols = [2,3], skiprows = 64, names = ['Time','Voltage'])
	except pd.io.common.EmptyDataError: #if file is empty, wait reset_time
		time.sleep(reset_time)
		DBRE_analyzer(filename, charging_time, cycle_time, reset_time, threshold, num_measurements)
	#extract date and time
	f = open(filename + '.DTA', 'r')
	lines = f.readlines()
	datestamp = lines[3].split('\t')[2]
	timestamp = lines[4].split('\t')[2]
	f.close()
	#save voltage vs time in Excel file just in case
	raw_data.to_excel(filename + '.xlsx')
	#extract voltage and plateau length using threshold
	raw_data = raw_data[raw_data.Time > charging_time]
	raw_data['Derivative'] = np.gradient(raw_data.Voltage,raw_data.Time)
	count = 0
	reached_plateau = False
	plateau_start = 0
	for i in raw_data.Derivative: #go through voltage readings until derivative exceeds threshold
		if i < threshold:
			reached_plateau = True #make sure that initial steepness is ignored
			if plateau_start == 0:
				plateau_start = count
		if i > threshold and reached_plateau is True: #end loop
			break
		count = count + 1
	raw_data.drop(raw_data.tail(len(raw_data.index)-count).index, inplace = True)
	raw_data.drop(raw_data.head(plateau_start).index, inplace = True)
	#increase threshold if script didn't find plateau
	if raw_data.empty:
		threshold = threshold*2
		return DBRE_analyzer(filename, charging_time, cycle_time, reset_time, threshold, num_measurements)
	#^ not sure if this will work
	ones = 1+0*raw_data.Time
	plateau = np.trapz(ones,x = raw_data.Time) #time of plateau length
	voltage = np.trapz(raw_data.Voltage, x = raw_data.Time)/plateau #numerical integral to average voltage
	uncertainty = (max(raw_data.Voltage) - min(raw_data.Voltage))/2 #estimate uncertainty as voltage window divided by 2
	df = df.append({'Date': datestamp,'Time': timestamp,'Potential': voltage,'Uncertainty': uncertainty, 'Plateau_Length': plateau},ignore_index = True) #add values to overall dataframe
	df.to_excel('DBRE.xlsx')
	new_number = int(filename[-1]) + 1
	if new_number > num_measurements:
		print(df)
		return 'Done'
	time.sleep(cycle_time)
	new_filename = filename[:-1]
	new_filename = new_filename + str(new_number)
	DBRE_analyzer(new_filename, charging_time, cycle_time, reset_time, threshold, num_measurements) #recursive loop until all files parsed
# Now, create the dataframe that will store the readings. It will be written to an Excel file after each measurement.
df = pd.DataFrame(columns = ['Date','Time','Potential','Uncertainty','Plateau_Length'])
#run function
DBRE_analyzer(filename, charging_time, cycle_time, reset_time, threshold, num_measurements)