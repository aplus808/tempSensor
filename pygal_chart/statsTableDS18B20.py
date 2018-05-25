#!/usr/bin/env python3

import sqlite3
import sys

# Get count of rows in table
def getCount(curs):
	for row in curs.execute("SELECT COUNT(*) FROM DS18B20_1_data"):
		rowCount = row[0]
	return rowCount
	
# Get x number of latest rows
def getLatestRows(curs, numSamples):
	if int(numSamples) > rowCount:
		numSamples = rowCount
	for row in curs.execute("SELECT * FROM DS18B20_1_data ORDER BY timestamp DESC LIMIT " + str(numSamples)):
		print(row)
	
# print database content
# print ("\nEntire database contents:\n")
# for row in curs.execute("SELECT * FROM DS18B20_1_data"):
	# print (row)

# Globals
dbPath = '/home/pi/Sensors_Database/sensorsData.db'

global conn
conn = sqlite3.connect(dbPath)

global curs
curs = conn.cursor()

global rowCount
rowCount = getCount(curs)

def main(args):
	if len(args) > 1:
		getLatestRows(curs, args[1])
	else:
		print('Row Count: ' + str(rowCount))
	# close the database after use
	conn.close()
	
if __name__ == '__main__':
	main(sys.argv)