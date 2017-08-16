import pandas as pd

ailment = None
lastSeenCode = None
ailmentToCode = {}
codeToAvg = {}

def setAilment(row):
	global ailment
	if str(row['DESCRIPTION']) != 'nan':
		ailment = str(row['DESCRIPTION'])
		return True
	else:
		return False

def updateCodeMap(row):
	global lastSeenCode
	code = str(row['HCPCS'])
	if code != 'nan':
		if ailment not in ailmentToCode:
			ailmentToCode[ailment] = []
		ailmentToCode[ailment].append(code)
		lastSeenCode = code

def updateAvgCost(row):
	modifier = str(row['MODIFIER'])
	if modifier == 'TOTAL':
		codeToAvg[lastSeenCode] = float(row['ALLOWED CHARGES'][1:].replace(',','')) / float(row['ALLOWED SERVICES'].replace(',',''))

def getCSVs():
	from os import listdir
	from os.path import isfile, join
	mypath = './data'
	return [f for f in listdir(mypath) if isfile(join(mypath, f))]

for file_name in getCSVs():
	global ailment
	csv = pd.read_csv('./data/'+file_name, skiprows=4, dtype=str)
	ailment = None
	for idx, row in csv.iterrows():
		if not ailment and not setAilment(row):
			continue
		updateCodeMap(row)
		updateAvgCost(row)
print ailmentToCode