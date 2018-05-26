#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  logTemp.py
#
#  Capture data from a DS18B20 sensor and save it on a database

import glob
import time
import sqlite3
import os
import subprocess

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'
dbname='instance/tempSensor.sqlite3'
sampleFreq = 30 # time in seconds

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
	
	conn=sqlite3.connect(dbname)
	curs=conn.cursor()
	
	curs.execute("INSERT INTO temperatures (timestamp, tempc, tempf) VALUES (datetime('now', 'localtime'), (?), (?))", (temp[0], temp[1]))
	conn.commit()
	conn.close()

# main function
def main():
	while True:
		temp = read_temp()
		logData (temp)
		time.sleep(sampleFreq)

# ------------ Execute program 
main()
