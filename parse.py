import pandas as pd

ailment = None
lastSeenCode = None
ailmentToCode = {}
codeToVal = {}

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

def getFormattedVal(unformatted):
	unformatted = str(unformatted)
	if unformatted != 'nan' and unformatted.startswith('$'):
		unformatted = unformatted[1:]
	formatted = float(unformatted.replace(',',''))
	return formatted

def updateValsFromRow(row):
	updateForCols = ['ALLOWED CHARGES', 'ALLOWED SERVICES', 'PAYMENT']
	modifier = str(row['MODIFIER'])
	if modifier == 'TOTAL':
		if not lastSeenCode in codeToVal:
			codeToVal[lastSeenCode] = {}
			for updateFor in updateForCols:
				codeToVal[lastSeenCode][updateFor] = 0.0
		for updateFor in updateForCols:
			codeToVal[lastSeenCode][updateFor] += getFormattedVal(row[updateFor])

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
		updateValsFromRow(row)

def printJson():
	# print 'id,value'
	vals_json = []
	for a in ailmentToCode:
		vals_item = {'name':a, 'children':[]}
		#print a, len(ailmentToCode[a])
		for code in ailmentToCode[a]:
			if code in codeToVal:
				avg_pay = avg_charges = 0
				avg_pay = codeToVal[code]['PAYMENT']/codeToVal[code]['ALLOWED SERVICES']
				avg_charges = codeToVal[code]['ALLOWED CHARGES']/codeToVal[code]['ALLOWED SERVICES']
				if avg_charges > 0.0:
					percentage_paid = (avg_pay/avg_charges)*100
					vals_item['children'].append({'name':code, 'children':[{'name':percentage_paid}]})
					# print a.replace(' ', '_')+"."+code+","+str(percentage_paid)
		vals_json.append(vals_item)
	print vals_json

printJson()
