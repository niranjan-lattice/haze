import pandas as pd
import math

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

def updateCodeMap(row, year):
	global lastSeenCode
	code = str(row['HCPCS'])
	if code != 'nan':
		if year not in ailmentToCode:
			ailmentToCode[year] = {}
		if ailment not in ailmentToCode[year]:
			ailmentToCode[year][ailment] = []
		ailmentToCode[year][ailment].append(code)
		lastSeenCode = code

def getFormattedVal(unformatted):
	unformatted = str(unformatted)
	if unformatted != 'nan' and unformatted.startswith('$'):
		unformatted = unformatted[1:]
	formatted = float(unformatted.replace(',',''))
	return formatted

def updateValsFromRow(row, year):
	updateForCols = ['ALLOWED CHARGES', 'ALLOWED SERVICES', 'PAYMENT']
	modifier = str(row['MODIFIER'])
	if modifier == 'TOTAL':
		if not year in codeToVal:
			codeToVal[year] = {}
		if not lastSeenCode in codeToVal[year]:
			codeToVal[year][lastSeenCode] = {}
			for updateFor in updateForCols:
				codeToVal[year][lastSeenCode][updateFor] = 0.0
		for updateFor in updateForCols:
			codeToVal[year][lastSeenCode][updateFor] += getFormattedVal(row[updateFor])

def getYears():
	from os import walk
	for (dirpath, years, filenames) in walk('./data'):
		return years

def getCSVs(year):
	from os import listdir
	from os.path import isfile, join
	mypath = './data/'+year
	return [f for f in listdir(mypath) if isfile(join(mypath, f))]

def parse_csvs():
	for year in getYears():
		print year
		for file_name in getCSVs(year):
			global ailment
			csv = pd.read_csv('./data/'+str(year)+'/'+file_name, skiprows=3, dtype=str)
			ailment = None
			for idx, row in csv.iterrows():
				if not ailment and not setAilment(row):
					continue
				updateCodeMap(row, year)
				updateValsFromRow(row, year)

def printJson(year):
	vals_json = []
	hist_arr = []
	totals_json = {'name':'Ailments','children':[]}
	for a in ailmentToCode[year]:
		vals_item = {'name':a, 'children':[]}
		totals_item = {'name':a, 'children':[]}
		ailment_totals = {
			"charges": 0.0,
			"payment": 0.0,
			"services": 0.0
		}
		for code in ailmentToCode[year][a]:
			if code in codeToVal[year]:
				avg_pay = avg_charges = 0
				ailment_totals["charges"] += codeToVal[year][code]['ALLOWED CHARGES']
				ailment_totals["payment"] += codeToVal[year][code]['PAYMENT']
				ailment_totals["services"] += codeToVal[year][code]['ALLOWED SERVICES']
				avg_pay = codeToVal[year][code]['PAYMENT']/codeToVal[year][code]['ALLOWED SERVICES']
				avg_charges = codeToVal[year][code]['ALLOWED CHARGES']/codeToVal[year][code]['ALLOWED SERVICES']
				if avg_charges > 0.0:
					percentage_paid = (avg_pay/avg_charges)*100
					if not math.isnan(percentage_paid):
						hist_arr.append(percentage_paid)
					vals_item['children'].append({'name':code, 'children':[{'name':percentage_paid}]})
		vals_json.append(vals_item)
		ailment_avg = ((ailment_totals['payment']/ailment_totals['services'])/(ailment_totals['charges']/ailment_totals['services']))*100
		ailment_avg = str(round(ailment_avg, 2))
		totals_item['children'].append({'name':ailment_avg})
		totals_json['children'].append(totals_item)
	generate_hist(hist_arr, year)

def generate_hist(hist_arr, year):
	import numpy as np
	import matplotlib.pyplot as plt
	fig = plt.figure()
	x = np.asarray(hist_arr)

	ax1 = fig.add_subplot(211)
	ax1.hist(x, 100, normed=1, facecolor='g', alpha=0.75)
	ax1.set_xlabel('Paid Percentage')
	ax1.set_ylabel('Probability')
	ax1.set_title('Histogram of Payment %')
	ax1.axis([0, 105, 0, 0.4])
	ax1.grid(True)

	ax2 = fig.add_subplot(212)
	ax2.hist(x, 50, normed=1, facecolor='b', alpha=0.75)
	ax2.set_xlabel('Paid Percentage')
	ax2.set_ylabel('Probability')
	ax2.set_title('Histogram of Payment %')
	ax2.axis([0, 105, 0, 0.4])
	ax2.grid(True)
	
	plt.show()

parse_csvs()