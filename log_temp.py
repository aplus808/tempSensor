#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  log_temp.py
#
#  Capture data from a DS18B20 sensor and save it on a database

import glob
import time
import sqlite3
import os
import subprocess
import click
import signal


# from temp_sensor.db import get_db

# Initialize sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

received = False

# Set sensor variables
device_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(device_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

# Flask instance path from current working directory
instancepath = os.getcwd() + '/instance/'

# Set db variables
dbname = instancepath + 'temp_sensor.sqlite3'
sfreq = 30 # time in seconds

# Record the pid
pidfile = instancepath + 'log_temp_pid.txt'
fh = open(pidfile, 'w')
fh.write(str(os.getpid()))
fh.close()

# Get data from DS18B20 sensor
def getDS18B20data():	
	catdata = subprocess.Popen(['cat',device_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out,err = catdata.communicate()
	out_decode = out.decode('utf-8')
	lines = out_decode.split('\n')
	return lines

# Read data into Celcius and Farenheit
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

# Log sensor data on database
def logData (temp):
	
	conn=sqlite3.connect(dbname)
	curs=conn.cursor()
	
	curs.execute("INSERT INTO temperatures (timestamp, tempc, tempf) VALUES (datetime('now', 'localtime'), (?), (?))", (temp[0], temp[1]))
	conn.commit()
	conn.close()

def handUSR1(signum,frame):
	# Callback invoked whan a USR1 signal is received
	global received
	# print("SIGUSR1 received")
	received = True

@click.command()
@click.option('--freq', default=30, help="Sample frequency in seconds")
def main(freq):
	global sfreq
	global received
	
	if freq is not None and freq > 0:
		sfreq = freq
	print("Sample frequency is " + str(sfreq) + " seconds")
	
	i = 1
	# Waitait for a kill signal
	while received == False:
		signal.signal(signal.SIGUSR1, handUSR1)
		time.sleep(1)
		# Logog and read data at the sampling frequency
		if i%sfreq == 0:
			temp = read_temp()
			logData(temp)
		i += 1

		
# ------------ Execute program 
if __name__ == "__main__":
	main()
