import os
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

df = pd.DataFrame(columns = ['Hours','Date','Time','Potential','Uncertainty','Plateau_Length'])
folders = [d.name() for d in os.scandir('.') if d.is_dir()]
for folder in folders:
	os.chdir(folder)
	data = pd.read_excel('DBRE_Summary.xlsx')
	df = df.append(data)
	os.chdir('..')
plt.figure()
plt.suptitle('Salt Potential Over Time')
plt.errorbar(df.Hours, df.Potential, yerr = df.Uncertainty, color = 'blue', ecolor = 'black', fmt = 'o',capsize = 5)
plt.xlabel('Time (hr)')
plt.ylabel('Salt Potential (V vs Be|Be2+)')
plt.ticklabel_format(axis = 'x', style = 'plain', useOffset = False)
plt.savefig('DBRE_Summary.png', dpi=300)
plt.close()
df.to_excel('DBRE_Summary.xlsx')
