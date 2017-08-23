import pandas as pd
import math
import numpy as np
import matplotlib.pyplot as plt
import json
import requests
import time
import sys
import nltk
from nltk.corpus import stopwords
from nltk import word_tokenize
from sklearn.naive_bayes import GaussianNB, BernoulliNB, MultinomialNB
from sklearn import datasets, metrics

# {'S': 'Non-covered by Medicare statute', 'I': 'Not payable by Medicare', 'C': 'Carrier judgment', 'M': 'Non-covered by Medicare', 'D': 'Special coverage instructions apply'}

ailment = None
lastSeenCode = None
ailmentToCode = {}
codeToVal = {}
col_names = ['ALLOWED CHARGES', 'ALLOWED SERVICES', 'PAYMENT']
prediction_words = ['lens', 'ambulance', 'x-ray']
coverage_codes = ['S', 'I', 'C', 'M', 'D']

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
	cols = 1
	rows = 2
	plot_num = 1
	years = [str(y) for y in hist_data.keys()]
	years.sort()
	for idx, year in enumerate(years):
		if plot_num > rows:
			plt.savefig('./hists/'+year+'.png')
			plot_num = 1
			fig = plt.figure()
		if hist_data[str(year)] and len(hist_data[str(year)]) > 0:
			x = np.asarray([coverage_codes.index(hd) for hd in hist_data[str(year)]])
			# print x
			ax1 = fig.add_subplot(rows, cols, plot_num)
			n, bins, patches = ax1.hist(x, 5, normed=1, facecolor='g', alpha=0.75)
			# ax1.set_xlabel('Paid Percentage')
			ax1.set_title(str(year))
			ax1.axis([0, 5, 0, 1])
			ax1.grid(True)
			plot_num += 1
	# plt.show()
	plt.savefig('./hists/last.png')

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

def download_hcspcs_deets():
	year = '2015'
	for ailment in ailmentToCode[year].keys():
		if ailment != 'CARDIOVASCULAR':
			print ailment
			codes = list(set([str(code) for code in ailmentToCode[year][ailment]]))
			deets = get_deets_for_codes(codes)
			ailment = ailment.replace('/', ' ')
			with open(ailment+'.json', 'w') as outfile:
				json.dump({'hcpcs':deets}, outfile)
			time.sleep(60)

def generate_ailment_occurances(codeToOccurances):
	ret_val = {}
	ailmentToCode = read_json('./ailmentToCode.json')
	for ailment, codes in ailmentToCode['2015'].iteritems():
		if ailment not in ret_val:
			ret_val[ailment] = []
		for code in codes:
			ailment_code = [0, 0, 0]
			if code not in codeToOccurances:
				continue
			fd = codeToOccurances[code]
			for idx, word in enumerate(prediction_words):
				if word in fd:
					ailment_code[idx] += fd[word]
			ret_val[ailment].append(ailment_code)
	return ret_val

def build_data_set(occurances_map):
	ailment_codes = []
	word_freq_counts = []
	for idx, ailment in enumerate(occurances_map.keys()):
		print ailment, idx
		for code_map in occurances_map[ailment]:
			# print ailment, idx, code_map
			ailment_codes.append(idx)
			word_freq_counts.append(code_map)
	return np.asarray(ailment_codes), np.asarray(word_freq_counts)

def fit(target, data):
	classifier = GaussianNB()
	classifier.fit(data, target)
	print classifier.predict([[0, 0, 1]])

def predict_payment_percent(codeToOccurances):
	occurances_map = generate_ailment_occurances(codeToOccurances)
	target, data = build_data_set(occurances_map)
	fit(target, data)

def save_json_files():
	parse_csvs()
	# get_hcpcs_deets()
	# hcpcsDeets = read_json('./hcpcs.json')
	with open('ailmentToCode.json', 'w') as outfile:
	    json.dump(ailmentToCode, outfile)
	with open('codeToVal.json', 'w') as outfile:
	    json.dump(codeToVal, outfile)

def save_graphs():
	ailmentToCode = read_json('./ailmentToCode.json')
	codeToVal = read_json('./codeToVal.json')
	line_data = build_ailment_aggregate()
	generate_line(line_data)

def parse_hcpcs():
	codeToOccurances = {}
	for file_name in getHCPCSFiles():
		try:
			currJson = read_json('./hcpcs/'+file_name)
			for code in currJson['hcpcs']:
				code_id = code['HCPC']
				if code_id not in codeToOccurances:
					codeToOccurances[code_id] = {}
				wordToOccurances = codeToOccurances[code_id]
				tokens = [t.lower() for t in word_tokenize(code['LongDescription']) if t.lower() in prediction_words]
				if len(tokens) > 0:
					for word, freq in nltk.FreqDist(tokens).most_common(5):
						if word not in wordToOccurances:
							wordToOccurances[word] = 0
						wordToOccurances[word] += freq
		except:
			print 'Error processing ', file_name, sys.exc_info()
			raise		
	return codeToOccurances

def parse_hcpcs_coverage():
	coverages = {}
	ailmentToCoverages = {}
	for file_name in getHCPCSFiles():
		try:
			ailmentToCoverages[file_name] = []
			currJson = read_json('./hcpcs/'+file_name)
			for code in currJson['hcpcs']:
				coverage = str(code['Coverage'])
				coverageDesc = str(code['CoverageDescription'])
				if coverage not in coverages:
					coverages[coverage] = coverageDesc
				ailmentToCoverages[file_name].append(coverage)
		except:
			print 'Error processing ', file_name, sys.exc_info()
			raise
	print coverages
	return ailmentToCoverages

def parse_hcpcs_code_coverage():
	codeToCoverage = {}
	for file_name in getHCPCSFiles():
		try:
			currJson = read_json('./hcpcs/'+file_name)
			for code in currJson['hcpcs']:
				coverage = str(code['Coverage'])
				codeToCoverage[code['HCPC']] = coverage
		except:
			print 'Error processing ', file_name, sys.exc_info()
			raise
	return codeToCoverage

def parse_hcpcs_desc():
	codeToWords = {}
	for file_name in getHCPCSFiles():
		try:
			currJson = read_json('./hcpcs/'+file_name)
			for code in currJson['hcpcs']:
				code_id = code['HCPC']
				if code_id not in codeToWords:
					codeToWords[code_id] = set()
				tokens = set([t.lower() for t in word_tokenize(code['LongDescription'])]) - set(stopwords.words('english'))
				codeToWords[code_id] = codeToWords[code_id].union(tokens)
		except:
			print 'Error processing ', file_name, sys.exc_info()
			raise		
	return codeToWords

def findMatchedCodes():
	sentence = 'Cars ambulances and lens'
	codeToWords = parse_hcpcs_desc()
	userTokens = set([t.lower() for t in word_tokenize(sentence)]) - set(stopwords.words('english'))
	matchedCodes = set()
	for code, codeTokens in codeToWords.iteritems():
		if len(userTokens & codeTokens) > 0:
			matchedCodes.add(code)
	with open('matchedCodes.json', 'w') as outfile:
		json.dump({'codes':list(matchedCodes)}, outfile)

def plotCodePercentages(percentages):
	fig = plt.figure()
	rows = 1
	cols = 1
	x = np.asarray(percentages)
	print x
	ax1 = fig.add_subplot(rows, cols, 1)
	n, bins, patches = ax1.hist(x, 10, normed=1, facecolor='g', alpha=0.75)
	ax1.set_xlabel('Paid Percentage')
	ax1.set_title('Matched Codes Percentages')
	ax1.axis([0, 100, 0, 1])
	ax1.grid(True)
	plt.show()

def plotCodeCoverages(coverages):
	fig = plt.figure()
	rows = 1
	cols = 1
	x = np.asarray(coverages)
	print x
	ax1 = fig.add_subplot(rows, cols, 1)
	n, bins, patches = ax1.hist(x, 5, normed=1, facecolor='g', alpha=0.75)
	ax1.set_xlabel('Coverage[S, I, C, M, D]')
	ax1.set_title('Matched Codes Coverages')
	ax1.axis([0, 5, 0, 1])
	ax1.grid(True)
	plt.show()

def graphMatchedCodes():
	codeToVal = read_json('./codeToVal.json')["2015"]
	codeToCoverage = parse_hcpcs_code_coverage()
	matchedCodes = read_json('./matchedCodes.json')
	print matchedCodes['codes']
	percentages = []
	coverages = []
	for code in matchedCodes['codes']:
		charges = safe_float(codeToVal[code][col_names[0]], 0.0)
		payments = safe_float(codeToVal[code][col_names[2]], 0.0)
		services = safe_float(codeToVal[code][col_names[1]], 0.0)
		charges_avg = safe_division(charges, services, charges)
		payment_avg = safe_division(payments, services, 0.0)
		percentage = safe_division(payment_avg, charges_avg, 0.0)*100
		percentages.append(percentage)
		coverages.append(coverage_codes.index(codeToCoverage[code]))
	plotCodePercentages(percentages)
	plotCodeCoverages(coverages)

graphMatchedCodes()

# codeToOccurances = parse_hcpcs()
# predict_payment_percent(codeToOccurances)

# ailmentToCoverages = parse_hcpcs_coverage()
# generate_hist(ailmentToCoverages)