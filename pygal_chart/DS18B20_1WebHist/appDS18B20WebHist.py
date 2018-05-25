#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  appDS18B20WebHist.py
#  


'''
	RPi Web Server for DS18B20 captured data with Gauge and Graph plot  
'''

from datetime import datetime, timedelta
from dateutil import tz
import io

# from flask import Flask, jsonify, render_template, send_file, make_response, request
from flask import Flask, render_template, make_response, request
# from pygal import Config

import sqlite3
import pygal
import json
import cairosvg

app = Flask(__name__)

# Retrieve LAST data from database
def getLastData():
	conn = sqlite3.connect('../sensorsData.db')
	curs = conn.cursor()
	for row in curs.execute("SELECT * FROM DS18B20_1_data ORDER BY timestamp DESC LIMIT 1"):
		time = row[0]
		temp = row[1]
	conn.close()
	return time, temp

# Get 'x' samples of historical data
def getHistData (numSamples):
	global rangeTime
	global rangeUnit
	global fmt
	# print('0.0: ' + str(numSamples))
	lastTstamp = datetime.strptime(getLastData()[0], fmt)
	# print('0.5: ' + str(rangeTime * rangeUnit))
	firstTstamp = lastTstamp - timedelta(minutes = rangeTime * rangeUnit)
	# print('1.0: ' + str(lastTstamp) + ', ' + str(firstTstamp))
	firstTstamp = datetime.strftime(firstTstamp, fmt)
	# print('1.1: ' + firstTstamp)
	
	conn = sqlite3.connect('../sensorsData.db')
	curs = conn.cursor()
	for row in curs.execute("SELECT COUNT(*) FROM DS18B20_1_data WHERE timestamp > '" + firstTstamp + "'"):
		rowcount = row[0]
		# print('2.0: ' + str(rowcount))
	curs.execute("SELECT * FROM DS18B20_1_data WHERE timestamp > '" + firstTstamp + "' ORDER BY timestamp ASC")
	data = curs.fetchall()
	dates = []
	temps = []
	step = max(1, rowcount//20)
	count = 0
	for row in data:
		if count == 0 or count%step == 0:
			dates.append(datetime.strptime(row[0], fmt))
			temps.append(row[1])
			temps = testData(temps)
		count += 1
	conn.close()
	return dates, temps

# Test data for cleanning possible "out of range" values
def testData(temps):
	n = len(temps)
	for i in range(0, n-1):
		if (temps[i] < 32 or temps[i] > 120):
			temps[i] = temps[i-2]
	return temps


# Get Max number of rows (table size)
def maxRowsTable():
	conn = sqlite3.connect('../sensorsData.db')
	curs = conn.cursor()
	for row in curs.execute("select COUNT(temp) from  DS18B20_1_data"):
		maxNumberRows = row[0]
	conn.close()
	return maxNumberRows

# Get sample frequency in minutes
def freqSample():
	# global fmt
	times, temps = getHistData(2)
	# tstamp0 = datetime.strptime(times[0], fmt)
	# tstamp1 = datetime.strptime(times[1], fmt)
	# freq = tstamp1-tstamp0
	freq = times[1] - times[0]
	freq = int(round(freq.total_seconds()/60))
	return freq
	
# Convert timestamps to local timezone from UTC
def convertTz(time):
	global fmt
	from_zone = tz.gettz('UTC')
	to_zone = tz.tzlocal()

	if type(time) is list:
		tlocal = []
		for t in time:
			# Tell the datetime object that it's in UTC time zone since 
			# datetime objects are 'naive' by default
			t = t.replace(tzinfo=from_zone)
			# Convert timezone
			tlocal.append(t.astimezone(to_zone))
	else:
		if type(time) is datetime:
			time = time.replace(tzinfo=from_zone)
			tlocal = time.astimezone(to_zone)
		elif type(time) is str:
			time = datetime.strptime(time, fmt)
			time = time.replace(tzinfo=from_zone)
			tlocal = time.astimezone(to_zone)
	
	return tlocal

# define and initialize global variables
global numSamples
numSamples = 100

global rangeTime
rangeTime = 100

global rangeUnit
rangeUnit = 1

global timezone
timezone = datetime.now(tz.tzlocal()).tzname()

global fmt
fmt = '%Y-%m-%d %H:%M:%S'

global freqSamples
freqSamples = freqSample()		

# main route
@app.route("/")
def index():
	time, temp = getLastData()
	time = convertTz(time)
	time = time.strftime('%b %d %Y %H:%M:%S')
	templateData = {
	  'time'		: time,
	  'timezone'	: timezone,
	  'temp'		: temp,
	  'freq'		: freqSamples,
	  'rangeTime'	: rangeTime
	}
	# return render_template('index.html', **templateData)
	return render_template('main.html', **templateData)

@app.route('/', methods=['POST'])
def my_form_post():
	global numSamples 
	global freqSamples
	global rangeTime
	global rangeUnit
	rangeTime = int(request.form['rangeTime'])
	rangeUnit = int(request.form['rangeUnit'])
	# print([rangeTime, rangeUnit, rangeTime*rangeUnit])
	if (rangeTime * rangeUnit < 20):
		freqSamples = 1
	else:
		freqSamples = freqSample()
	if (rangeTime * rangeUnit < freqSamples):
		rangeTime = freqSamples + 1
	numSamples = rangeTime * rangeUnit
	numMaxSamples = maxRowsTable()
	if (numSamples > numMaxSamples):
		numSamples = (numMaxSamples-1)
	
	time, temp = getLastData()
	time = convertTz(time)
	time = time.strftime('%b %d %Y %H:%M:%S')
	
	templateData = {
	  'time'		: time,
	  'timezone'	: timezone,
	  'temp'		: temp,
	  'freq'		: freqSamples,
	  'rangeTime'	: rangeTime
	}
	# return render_template('index.html', **templateData)
	return render_template('main.html', **templateData)
	
	
@app.route('/plot/temp')
def plot_temp():
	global rangeUnit
	times, temps = getHistData(numSamples)
	times = convertTz(times)
	xs = list(map(lambda d: d.strftime('%b %d %H:%M'), times))
	# ys = temps
	
	line_chart = pygal.Line(title="Temperature [°F]", x_label_rotation=-20, show_x_guides=True, show_minor_x_labels=False)

	# Set the xaxis label (major) spacing
	line_chart.x_labels = xs
	# print('3.0: ' + str(numSamples))
	if numSamples < 20:
		spacing = 1
	else:
		spacing = 2
	line_chart.x_labels_major = xs[::spacing]
	# line_chart.x_labels_major_every = 2
	
	# Set the custom y labels (60-90 Farenheit, with TOO HOT = 80 and TOO COLD = 70)
	line_chart.y_labels = [{'label': '60', 'value': 60}, {'label': '62', 'value': 62}, {'label': '64', 'value': 64}, {'label': '66', 'value': 66}, {'label': '68', 'value': 68}, {'label': 'TOO COLD', 'value': 70}, {'label': '72', 'value': 72}, {'label': '74', 'value': 74}, {'label': '76', 'value': 76}, {'label': '78', 'value': 78}, {'label': 'TOO HOT', 'value': 80}, {'label': '82', 'value': 82}, {'label': '84', 'value': 84}, {'label': '86', 'value': 86}, {'label': '88', 'value': 88}, {'label': '90', 'value': 90}]
	
	line_chart.add('Temps in F', temps)

	output = io.BytesIO()
	line_chart.render_to_png(output)
	response = make_response(output.getvalue())
	response.mimetype = 'image/png'
	return response
	# return render_template('index.html', chart=line_chart)

if __name__ == "__main__":
   app.run(host='0.0.0.0', debug=True)
