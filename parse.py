import pandas as pd
import math

ailment = None
lastSeenCode = None
ailmentToCode = {}
codeToVal = {}

def setAilment(row):
	global ailment
	try:
		if str(row['DESCRIPTION']) != 'nan':
			ailment = str(row['DESCRIPTION'])
			return True
		else:
			return False
	except:
		print row
		raise

def updateCodeMap(row, year):
	global lastSeenCode
	try:
		code = str(row['HCPCS'])
		if code != 'nan':
			if year not in ailmentToCode:
				ailmentToCode[year] = {}
			if ailment not in ailmentToCode[year]:
				ailmentToCode[year][ailment] = []
			ailmentToCode[year][ailment].append(code)
			lastSeenCode = code
	except:
		print row
		raise

def getFormattedVal(unformatted):
	unformatted = str(unformatted)
	if unformatted != 'nan' and unformatted.startswith('$'):
		unformatted = unformatted[1:]
	formatted = float(unformatted.replace(',',''))
	return formatted

def updateValsFromRow(row, year):
	updateForCols = ['ALLOWED CHARGES', 'ALLOWED SERVICES', 'PAYMENT']
	try:
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
	except:
		print row
		raise

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
	yearsSkipRows = {
		'2000': 4,
		'2001': 4,
		'2002': 4,
		'2003': 4,
		'2004': 4,
		'2005': 4,
		'2006': 3,
		'2007': 3,
		'2008': 4,
		'2009': 4,
		'2013': 3,
		'2014': 3,
		'2015': 3
	}
	for year in getYears():
		for file_name in getCSVs(year):
			global ailment
			try:
				csv = pd.read_csv('./data/'+str(year)+'/'+file_name, skiprows=yearsSkipRows[str(year)], dtype=str)
				ailment = None
				for idx, row in csv.iterrows():
					if not ailment and not setAilment(row):
						continue
					updateCodeMap(row, year)
					updateValsFromRow(row, year)
			except:
				print './data/'+str(year)+'/'+file_name
				raise

def printJson():
	hist_arr = {}
	for year in getYears():
		vals_json = []
		hist_arr[year] = []
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
							hist_arr[year].append(percentage_paid)
						vals_item['children'].append({'name':code, 'children':[{'name':percentage_paid}]})
			vals_json.append(vals_item)
			ailment_avg = ((ailment_totals['payment']/ailment_totals['services'])/(ailment_totals['charges']/ailment_totals['services']))*100
			ailment_avg = str(round(ailment_avg, 2))
			totals_item['children'].append({'name':ailment_avg})
			totals_json['children'].append(totals_item)
	generate_hist(hist_arr)

def generate_hist(hist_data):
	import numpy as np
	import matplotlib.pyplot as plt
	fig = plt.figure()
	cols = len(hist_data)
	rows = 1
	years = [int(y) for y in hist_data.keys()]
	years.sort()
	for idx, year in enumerate(years):
		x = np.asarray(hist_data[str(year)])
		ax1 = fig.add_subplot(rows, cols, idx+1)
		y, binEdges = np.histogram(x, bins=100)
		bincenters = 0.5*(binEdges[1:]+binEdges[:-1])
		ax1.plot(bincenters,y,'ro')
		# ax1.hist(x, 25, normed=1, facecolor='g', alpha=0.75, histtype='barstacked')
		# ax1.set_xlabel('Paid Percentage')
		# ax1.set_title(str(year))
		# ax1.axis([40, 105, 0, 0.5])
		# ax1.grid(True)
	plt.show()

parse_csvs()
printJson()
