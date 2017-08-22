import pandas as pd
import math
import numpy as np
import matplotlib.pyplot as plt
import json
import requests
import time
import sys

ailment = None
lastSeenCode = None
ailmentToCode = {}
codeToVal = {}
col_names = ['ALLOWED CHARGES', 'ALLOWED SERVICES', 'PAYMENT']

def setAilment(row):
	global ailment
	try:
		print row['DESCRIPTION']
		if str(row['DESCRIPTION']) != 'nan':
			ailment = str(row['DESCRIPTION'])
			print ailment
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

def getHCPCSFiles():
	from os import listdir
	from os.path import isfile, join
	mypath = './hcpcs'
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
		'2010': 4,
		'2011': 4,
		'2012': 4,
		'2013': 3,
		'2014': 3,
		'2015': 3
	}
	for year in getYears():
		print year
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
			plt.savefig('./graphs/'+ailment.replace(' ','').replace('/','')+'.png')
			plot_num = 1
			fig = plt.figure()
		ax1 = fig.add_subplot(rows, cols, plot_num)
		years = [int(y) for y in vals.keys()]
		years.sort()
		percents = []
		for year in years:
			curr_vals = vals[str(year)]
			percents.append(safe_division(curr_vals['payment_avg'],curr_vals['charges_avg'],0.0))
		ax1.plot(years, percents)
		# ax1.set_xlabel('Year')
		ax1.set_title(ailment)
		ax1.axis([2000, 2015, min(percents)-0.01, max(percents)+0.01])
		ax1.grid(True)
		plot_num += 1
	plt.savefig('./graphs/last.png')

def read_json(file_name):
	with open(file_name) as data_file:
	    return json.load(data_file)

def get_deets_for_codes(codes):
	print len(codes)
	deets = []
	count = 0
	for x in range((len(codes)/100)+1):
		try:
			selected = codes[(count*100):((count+1)*100)]
			selectedCodes = ''
			for sc in selected:
				selectedCodes+=(sc+',')
			hipaaspaceToken='182191EA884C497893E9A574312C08D7559DC87E7F4E48EEA1A8CC0E649292AC'
			payload = {'q': selectedCodes, 'rt': 'json', 'token': hipaaspaceToken}
			# print payload
			r = requests.get('https://www.hipaaspace.com/api/hcpcs/getcodes', params=payload)
			# print r.json()
			deets += r.json()['HCPCS']
			count+=1
			if count%10 == 0:
				time.sleep(60)
		except:
			print 'EXCEPTION! on request ', count+1
			print deets
			time.sleep(60)
	print 'Request: ',count
	print len(deets)
	print 'Coverage', float(len(deets))/float(len(codes))*100
	return deets

def get_hcpcs_deets():
	codes = []
	for key in ailmentToCode['2010'].keys():
		codes += [str(code) for code in ailmentToCode['2010'][key]]
	sortedCodes = list(set(codes))
	total = len(sortedCodes)
	selected = []
	selected+=sortedCodes[(total/3):(total/3)+10]
	selected+=sortedCodes[(2*total/3):(2*total/3)+10]
	print selected
	get_deets_for_codes(selected)

# parse_csvs()
# with open('ailmentToCode.json', 'w') as outfile:
#     json.dump(ailmentToCode, outfile)
# with open('codeToVal.json', 'w') as outfile:
#     json.dump(codeToVal, outfile)
# ailmentToCode = read_json('./ailmentToCode.json')
# codeToVal = read_json('./codeToVal.json')
# line_data = build_ailment_aggregate()
# print sorted([str(key) for key in ailmentToCode['2010'].keys()])
# print sorted([str(key) for key in ailmentToCode['2009'].keys()])
# get_hcpcs_deets()
# hcpcsDeets = read_json('./hcpcs.json')

# for ailment in ailmentToCode['2015'].keys():
# 	print ailment, len(set([str(code) for code in ailmentToCode['2015'][ailment]]))

# year = '2015'
# for ailment in ailmentToCode[year].keys():
# 	if ailment != 'CARDIOVASCULAR':
# 		print ailment
# 		codes = list(set([str(code) for code in ailmentToCode[year][ailment]]))
# 		deets = get_deets_for_codes(codes)
# 		ailment = ailment.replace('/', ' ')
# 		with open(ailment+'.json', 'w') as outfile:
# 			json.dump({'hcpcs':deets}, outfile)
# 		time.sleep(60)

# generate_line(line_data)

wordMap = {}

sentence = 'I have to buy contact lens and I need to call an ambulance to fix my fractured bone and get family planning'

for file_name in getHCPCSFiles():
	# print file_name
	try:
		currJson = read_json('./hcpcs/'+file_name)
		for code in currJson['hcpcs']:
			for word in sentence.split(' '):
				if not word in wordMap:
					wordMap[word] = {'ailments':{}}
				if word in code['LongDescription'].split(' ') or word in code['ShortDescription'].split(' '):
					# print word
					# print code['HCPC'], code['LongDescription'], code['ShortDescription']
					if not file_name in wordMap[word]['ailments']:
						wordMap[word]['ailments'][file_name] = {'codes':set()}
					if not code['HCPC'] in wordMap[word]['ailments'][file_name]['codes']:
						# print 'Adding ',code['HCPC']
						wordMap[word]['ailments'][file_name]['codes'].add(code['HCPC'])
	except:
		print 'Error processing ', file_name, sys.exc_info()
		raise

# print wordMap
for word in wordMap:
	for ailment in wordMap[word]['ailments']:
		print word, ailment, len(wordMap[word]['ailments'][ailment]['codes'])




