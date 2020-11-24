import os
import pandas as pd
folders = [d.name for d in os.scandir('.') if d.is_dir()]
for folder in folders:
	if folder.isdir()
		os.chdir(folder)
		if os.path.isfile('DBRE_Script.py'):
			exec(open("./DBRE_Script.py").read())
		os.chdir('..')