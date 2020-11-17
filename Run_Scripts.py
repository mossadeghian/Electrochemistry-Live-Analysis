import os
import pandas as pd
for folder in folders:
	os.chdir(folder)
	if os.path.isfile('DBRE_Script.py'):
		exec(open("./DBRE_Script.py").read())
	os.chdir('..')