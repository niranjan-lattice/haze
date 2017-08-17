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
	vals_json = []
	hist_arr = []
	totals_json = {'name':'Ailments','children':[]}
	for a in ailmentToCode:
		vals_item = {'name':a, 'children':[]}
		totals_item = {'name':a, 'children':[]}
		ailment_totals = {
			"charges": 0.0,
			"payment": 0.0,
			"services": 0.0
		}
		for code in ailmentToCode[a]:
			if code in codeToVal:
				avg_pay = avg_charges = 0
				ailment_totals["charges"] += codeToVal[code]['ALLOWED CHARGES']
				ailment_totals["payment"] += codeToVal[code]['PAYMENT']
				ailment_totals["services"] += codeToVal[code]['ALLOWED SERVICES']
				avg_pay = codeToVal[code]['PAYMENT']/codeToVal[code]['ALLOWED SERVICES']
				avg_charges = codeToVal[code]['ALLOWED CHARGES']/codeToVal[code]['ALLOWED SERVICES']
				if avg_charges > 0.0:
					percentage_paid = (avg_pay/avg_charges)*100
					hist_arr.append(percentage_paid)
					vals_item['children'].append({'name':code, 'children':[{'name':percentage_paid}]})
		vals_json.append(vals_item)
		ailment_avg = ((ailment_totals['payment']/ailment_totals['services'])/(ailment_totals['charges']/ailment_totals['services']))*100
		ailment_avg = str(round(ailment_avg, 2))
		totals_item['children'].append({'name':ailment_avg})
		totals_json['children'].append(totals_item)
	# print vals_json
	generate_hist(hist_arr)
	# print totals_json

def generate_hist(hist_arr):
	import numpy as np
	import matplotlib.pyplot as plt
	# Fixing random state for reproducibility
	np.random.seed(19680801)
	mu, sigma = 100, 15
	x = mu + sigma * np.random.randn(10000)
	print x
	# the histogram of the data
	n, bins, patches = plt.hist(x, 50, normed=1, facecolor='g', alpha=0.75)
	plt.xlabel('Smarts')
	plt.ylabel('Probability')
	plt.title('Histogram of IQ')
	plt.text(60, .025, r'$\mu=100,\ \sigma=15$')
	plt.axis([40, 160, 0, 0.03])
	plt.grid(True)
	plt.show()

printJson()
