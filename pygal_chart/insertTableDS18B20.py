import sqlite3 as lite
import sys
con = lite.connect('sensorsData.db')
with con:
	cur = con.cursor()
	cur.execute("INSERT INTO DS18B20_1_data VALUES(datetime('now'), 20.5)")
	cur.execute("INSERT INTO DS18B20_1_data VALUES(datetime('now'), 22.5)")
