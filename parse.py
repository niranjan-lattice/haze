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

def getAllowedServices(allowedServices):
	if allowedServices.startswith('$'):
		allowedServices = allowedServices[1:]
	return float(allowedServices.replace(',',''))

def getAllowedCharges(allowedCharges):
	if allowedCharges.startswith('$'):
		allowedCharges = allowedCharges[1:]
	return float(allowedCharges.replace(',',''))

def updateAvgCost(row):
	modifier = str(row['MODIFIER'])
	if modifier == 'TOTAL':
		codeToAvg[lastSeenCode] =  getAllowedCharges(row['ALLOWED CHARGES'])/ getAllowedServices(row['ALLOWED SERVICES'])

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
for a in ailmentToCode:
	print a, len(ailmentToCode[a])
