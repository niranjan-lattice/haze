import pandas as pd
import math
import numpy as np
import matplotlib.pyplot as plt

ailment = None
lastSeenCode = None
ailmentToCode = {}
codeToVal = {}
col_names = ['ALLOWED CHARGES', 'ALLOWED SERVICES', 'PAYMENT']

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
		if code != 'nan' and code.isalnum():
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
	try:
		modifier = str(row['MODIFIER'])
		if modifier == 'TOTAL' and lastSeenCode.isalnum():
			if not year in codeToVal:
				codeToVal[year] = {}
			if not lastSeenCode in codeToVal[year]:
				codeToVal[year][lastSeenCode] = {}
				for updateFor in col_names:
					codeToVal[year][lastSeenCode][updateFor] = 0.0
			for updateFor in col_names:
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

def safe_division(n, d, safe_val):
	if d <= 0:
		return safe_val
	else:
		return n / d

def safe_float(val, safe_val):
	if math.isnan(val):
		return safe_val
	return float(val)

def build_ailment_aggregate():
	aggregate = {}
	for year, ailment_codes in ailmentToCode.iteritems():
		for ailment, codes in ailment_codes.iteritems():
			if ailment not in aggregate:
				aggregate[ailment] = {}
			charges = payments = services = 0.0
			for code in codes:
				charges += safe_float(codeToVal[year][code][col_names[0]], 0.0)
				payments += safe_float(codeToVal[year][code][col_names[2]], 0.0)
				services += safe_float(codeToVal[year][code][col_names[1]], 0.0)
			aggregate[ailment][year] = {'charges_avg':safe_division(charges, services, charges),\
										'payment_avg':safe_division(payments, services, 0.0)}
	return aggregate


def generate_hist(hist_data):
	fig = plt.figure()
	cols = len(hist_data)
	rows = 1
	years = [int(y) for y in hist_data.keys()]
	years.sort()
	for idx, year in enumerate(years):
		x = np.asarray(hist_data[str(year)])
		ax1 = fig.add_subplot(rows, cols, idx+1)
		ax1.hist(x, 25, normed=1, facecolor='g', alpha=0.75, histtype='step')
		ax1.set_xlabel('Paid Percentage')
		ax1.set_title(str(year))
		ax1.axis([40, 105, 0, 0.5])
		ax1.grid(True)
	plt.show()

def generate_line(line_data):
	# print line_data
	fig = plt.figure()
	rows = 2
	cols = 1
	plot_num = 1
	for ailment, vals in line_data.iteritems():
		if plot_num > rows:
			plt.savefig('./graphs/'+ailment.replace(' ','')+'.png')
			plot_num = 1
		ax1 = fig.add_subplot(rows, cols, plot_num)
		years = [int(y) for y in vals.keys()]
		years.sort()
		percents = []
		for year in years:
			curr_vals = vals[str(year)]
			percents.append(safe_division(curr_vals['payment_avg'],curr_vals['charges_avg'],0.0))
		print years, percents
		ax1.plot(years, percents)
		# ax1.set_xlabel('Year')
		ax1.set_title(ailment)
		ax1.axis([2000, 2015, 0, 1])
		ax1.grid(True)
		plot_num += 1
	plt.savefig('./graphs/last.png')

def temp():
	fig = plt.figure()
	rows = 3
	cols = 1
	plot_num = 1
	for idx in range(20):
		if plot_num > rows:
			plot_num = 1
			plt.savefig('./'+str(idx))
		ax1 = fig.add_subplot(rows, cols, plot_num)
		plot_num += 1
		# years = [int(y) for y in vals.keys()]
		# years.sort()
		# percents = []
		# for year in years:
		# 	curr_vals = vals[str(year)]
		# 	percents.append(safe_division(curr_vals['payment_avg'],curr_vals['charges_avg'],0.0))
		# print years, percents
		ax1.plot([1,2,3], [1,2,3])
		ax1.set_xlabel('Year')
		# ax1.set_title(ailment)
		# ax1.axis([2000, 2015, 40, 100])
		ax1.grid(True)
	plt.savefig('./blahblah')

parse_csvs()
line_data = build_ailment_aggregate()
generate_line(line_data)
# temp()