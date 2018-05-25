#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  appDS18B20.py
#  

import os
import glob
import time
import sqlite3
import subprocess

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'
dbname='sensorsData.db'
sampleFreq = 1

# get data from DS18B20 sensor
def getDS18B20data():	
	catdata = subprocess.Popen(['cat',device_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out,err = catdata.communicate()
	out_decode = out.decode('utf-8')
	lines = out_decode.split('\n')
	return lines

# read data into Celcius and Farenheit
def read_temp():
	lines = getDS18B20data()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = getDS18B20data()
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
		temp_f = temp_c * 9.0 / 5.0 + 32.0
		return temp_c, temp_f

# log sensor data on database
def logData (temp):
	
	conn = sqlite3.connect(dbname)
	curs = conn.cursor()
	
	curs.execute("INSERT INTO DS18B20_1_data values(datetime('now'), (?))", (temp,))
	conn.commit()
	conn.close()

# display database data
def displayData():
	conn = sqlite3.connect(dbname)
	curs = conn.cursor()
	print ("\nEntire database contents:\n")
	for row in curs.execute("SELECT * FROM DS18B20_1_data"):
		print (row)
	conn.close()

# main function
def main():
	for i in range (0,3):
		temp = read_temp()
		logData(temp[1])
		time.sleep(sampleFreq)
	displayData()

# Execute program 
main()
