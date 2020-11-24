import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import time
import os
import glob
import scipy.interpolate
from datetime import datetime

# The following inputs will need to be set based on the experiment DBRE configuration #
start_time = datetime(2020, 10, 27, 15, 0, 0) #start of experiment
filename = 'A_DBRE_#1' #default filename whose number will be updated throughout script
reset_time = 1 	#number of seconds to wait if the script encounters an empty DBRE file (i.e. amount of time between DBREs)
#				If DBRE is not currently running, then set equal to 0.01
max_time = 600 #do not plot or evaluate past this number of seconds, to reduce amount of data
slope_threshold = 0.008 #default max value for slope of plateau, 0.008 works well
con_threshold = 0.001 #default max value for second derivative of plateau, 0.001 works well
min_plateau_length = 15 #minimum number of points needed to have a plateau, where each point is 0.1 s apart
#						It is better to set this between 10-15 so that a fake plateau isn't detected due to noise
printplots = True #whether or not you'd like to print each plot

#stop loop should be set to False by default.
stop_loop = False #whether to try reducing threshold if no plateau detected

def DBRE_analyzer(filename, slope_threshold, con_threshold, stop_loop):
	global df, reset_time, max_time, num_measurements, min_plateau_length, printplots
	try: #to read the text file
		raw_data = pd.read_csv(filename + '.DTA',sep = '\t',header = None, usecols = [2,3], skiprows = 64, names = ['Time','Voltage'])
	except: #if file is empty, wait reset_time
		time.sleep(reset_time)
		return DBRE_analyzer(filename, slope_threshold, con_threshold, stop_loop)

	#check again if file is empty, and if so, wait reset_time before retrying
	if raw_data.empty:
		time.sleep(reset_time)
		return DBRE_analyzer(filename, slope_threshold, con_threshold, stop_loop)

	#extract date, time, charging time, then convert to hours elapsed
	experimentnumber = filename[8:]
	f = open(filename + '.DTA', 'r')
	lines = f.readlines()
	datestamp = lines[3].split('\t')[2]
	timestamp = lines[4].split('\t')[2]
	datetimestamp = datetime.strptime(datestamp + ' ' + timestamp, '%m/%d/%Y %H:%M:%S')
	dt = datetimestamp - start_time
	hours = dt.total_seconds()/3600
	charging_time = float(lines[11].split('\t')[2])
	print(datetimestamp)
	f.close()

	#create derivative and concavity columns. Concavity is based on spline of voltage over time to reduce noise.
	raw_data['Derivative'] = np.gradient(raw_data.Voltage,raw_data.Time)
	spl = scipy.interpolate.splrep(raw_data.Time,raw_data.Voltage,k=3,s=0.0005)
	raw_data['Concavity'] = scipy.interpolate.splev(raw_data.Time,spl,der=2)

	#filter out times past the maximum time
	raw_data = raw_data[raw_data.Time <= max_time]

	#save raw data in Excel file, and produce plots
	if printplots:
		fig, (top,mid,bottom) = plt.subplots(3,sharex=True)
		plt.subplots_adjust(hspace=.07)
		plt.suptitle('Discharge for run #'+ experimentnumber)
		#VOLTAGE PLOT
		top = plt.subplot(3,1,1)
		plt.plot(raw_data.Time, scipy.interpolate.splev(raw_data.Time,spl))
		plt.axis([-10, max_time, min(raw_data.Voltage), raw_data['Voltage'].iloc[-1]+0.05])
		plt.ylabel('Voltage (V)')
		#DERIVATIVE PLOT
		mid = plt.subplot(3,1,2)
		plt.plot (raw_data.Time, raw_data.Derivative)
		plt.axis([-10, max_time, -0.002, 0.05])
		plt.ylabel('Derivative')
		plt.hlines(slope_threshold,-10,max_time,linestyles='dashed',label='Threshold')
		plt.hlines(slope_threshold,-10,max_time,linestyles ='dashed',label = 'Threshold')
		#CONCAVITY PLOT
		bottom = plt.subplot(3,1,3)
		plt.plot (raw_data.Time, raw_data.Concavity)
		plt.axis([-10, max_time, -0.0015, 0.0025])
		plt.xlabel('Time (s)')
		plt.ylabel('Concavity')
		plt.hlines(con_threshold,-10,max_time,linestyles='dashed',label='Threshold')
		plt.hlines(-con_threshold,-10,max_time,linestyles ='dashed',label = 'Threshold')
	raw_data.to_excel(filename + '.xlsx')

	#extract voltage and plateau length using threshold on derivatives
	raw_data = raw_data[raw_data.Time > charging_time]
	raw_data = raw_data.reset_index()

	#detect plateau based on concavity
	reached_plateau_1 = False
	plateau_start_1 = 0
	count_1 = -1
	for i in raw_data.Concavity:
		count_1 = count_1 + 1
		if i > -con_threshold and abs(i) < con_threshold:
			reached_plateau_1 = True
			if plateau_start_1 == 0:
				plateau_start_1 = count_1
		if i > con_threshold and reached_plateau_1 == True and abs(count_1-plateau_start_1) > min_plateau_length:
			break
	plateau_end_1 = max([count_1,0])

	#detect plateau based on first derivative
	reached_plateau_2 = False
	plateau_start_2 = 0
	count_2 = -1
	for i in raw_data.Derivative: #go through voltage readings until derivative exceeds threshold
		count_2 = count_2 + 1
		if i < slope_threshold:
			reached_plateau_2 = True #make sure that initial steepness is ignored
			if plateau_start_2 == 0:
				plateau_start_2 = count_2
		if i > slope_threshold and reached_plateau_2 is True and abs(count_2-plateau_start_2) > min_plateau_length: #end loop
			break
	plateau_end_2 = max([count_2,0])

	#get tightest plateau 	
	if plateau_end_2 < plateau_end_1:
		plateau_end = plateau_end_2
		plateau_start = plateau_start_2
	else:
		plateau_start = plateau_start_1
		plateau_end = plateau_end_1

	#if still didn't find plateau, repeat with reduced threshold and plateau length
	if raw_data.Time[plateau_end] >= max_time and not stop_loop:
		plt.close()
		print('uh oh')
		min_plateau_length /= 1.5
		return DBRE_analyzer(filename, slope_threshold/5, con_threshold/3, True)
	#afterwards, evert to original values
	if stop_loop:
		print('made it')
		stop_loop = False
		slope_threshold *= 5
		con_threshold *= 3
		min_plateau_length *= 1.5
	
	#add plateau points to plots
	if printplots:
		top.set_xlim(-10,min([raw_data.Time[plateau_end]+80,600]))
		mid.set_xlim(-10,min([raw_data.Time[plateau_end]+80,600]))
		bottom.set_xlim(-10,min([raw_data.Time[plateau_end]+80,600]))
		top.plot(raw_data.Time[plateau_start],raw_data.Voltage[plateau_start],'or', markersize=6)
		top.plot(raw_data.Time[plateau_end],raw_data.Voltage[plateau_end],'or', markersize=6)
		bottom.plot(raw_data.Time[plateau_start],raw_data.Concavity[plateau_start],'or', markersize=6)
		bottom.plot(raw_data.Time[plateau_end],raw_data.Concavity[plateau_end],'or', markersize=6)
		mid.plot(raw_data.Time[plateau_start],raw_data.Derivative[plateau_start],'or', markersize=6)
		mid.plot(raw_data.Time[plateau_end],raw_data.Derivative[plateau_end],'or', markersize=6)
		#save the plot
		plt.savefig('plot#'+experimentnumber+'.png', dpi=300) # Save the figure
		plt.close()

	#filter raw data to only contain plateau
	raw_data.drop(raw_data.tail(len(raw_data.index)-plateau_end).index, inplace = True)
	raw_data.drop(raw_data.head(plateau_start).index, inplace = True)

	#calculate plateau length, average potential, and uncertainty
	ones = 1+0*raw_data.Time
	plateau = np.trapz(ones,x = raw_data.Time) #time of plateau length
	voltage = -np.trapz(raw_data.Voltage, x = raw_data.Time)/plateau #numerical integral to average voltage
	uncertainty = (max(raw_data.Voltage) - min(raw_data.Voltage))/2 #estimate uncertainty as voltage window divided by 2

	#add info to overall Excel file, DBRE_Summary.xlsx
	df = df.append({'Hours': hours, 'Date': datestamp,'Time': timestamp,'Potential': voltage,'Uncertainty': uncertainty, 'Plateau_Length': plateau},ignore_index = True) #add values to overall dataframe
	df.to_excel('DBRE_Summary.xlsx')

	#plot salt potential over time after each trial is done
	plt.figure()
	plt.suptitle('Salt Potential Over Time')
	plt.errorbar(df.Hours, df.Potential, yerr = df.Uncertainty, color = 'blue', ecolor = 'black', fmt = 'o',capsize = 5)
	plt.xlabel('Time (hr)')
	plt.ylabel('Salt Potential (V vs Be|Be2+)')
	plt.ticklabel_format(axis = 'x', style = 'plain', useOffset = False)
	plt.savefig('DBRE_Summary.png', dpi=300)
	plt.close()

	#prepare to either read next file or stop
	new_number = int(filename[8:]) + 1
	if new_number > num_measurements:		
		return 'Done'
	new_filename = filename[:8]
	new_filename = new_filename + str(new_number)
	return DBRE_analyzer(new_filename, slope_threshold, con_threshold, stop_loop) #recursive loop until all files parsed


#run function in all subfolders
folders = [d.name for d in os.scandir('.') if d.is_dir()]
for folder in folders:
	os.chdir(folder)
	if os.path.isfile('A_DBRE_#1.DTA'):
		#Script detects number of measurements from number of DBRE files present.
		num_measurements= len(glob.glob1('.',"A*.DTA")) #expected number of files to go through
		# Now, create the dataframe that will store the readings. It will be written to an Excel file after each measurement.
		df = pd.DataFrame(columns = ['Hours','Date','Time','Potential','Uncertainty','Plateau_Length'])
		DBRE_analyzer(filename, slope_threshold, con_threshold, stop_loop)
	os.chdir('..')


#Compile data into one file
df_sum = pd.DataFrame(columns = ['Hours','Date','Time','Potential','Uncertainty','Plateau_Length'])
folders = [d.name for d in os.scandir('.') if d.is_dir()]
for folder in folders:
	os.chdir(folder)
	if os.path.isfile('DBRE_Summary.xlsx'):
		data = pd.read_excel('DBRE_Summary.xlsx')
		df_sum = df_sum.append(data)
	os.chdir('..')
plt.figure()
plt.suptitle('Salt Potential Over Time')
plt.errorbar(df_sum.Hours, df_sum.Potential, yerr = df_sum.Uncertainty, color = 'blue', ecolor = 'black', fmt = 'o',capsize = 1, markersize = 1, elinewidth = 0.2, capthick = 0.2)
plt.xlabel('Time (hr)')
plt.ylabel('Salt Potential (V vs Be|Be2+)')
plt.ticklabel_format(axis = 'x', style = 'plain', useOffset = False)
plt.savefig('DBRE_Summary.png', dpi=300)
plt.close()
df_sum.to_excel('DBRE_Summary.xlsx')