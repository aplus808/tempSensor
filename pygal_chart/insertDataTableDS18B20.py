import sqlite3
import sys
conn=sqlite3.connect('sensorsData.db')
curs=conn.cursor()
# function to insert data on a table
#def add_data (temp, hum):
def add_data (temp):
#	curs.execute("INSERT INTO DHT_data values(datetime('now'), (?), (?))", (temp, hum))
	curs.execute("INSERT INTO DS18B20_1_data values(datetime('now'), (?))", (temp,))
	conn.commit()
# call the function to insert data
# add_data (20.5, 30)
# add_data (25.8, 40)
# add_data (30.3, 50)
add_data (20.5)
add_data (25.8)
add_data (30.3)
# print database content
print ("\nEntire database contents:\n")
for row in curs.execute("SELECT * FROM DS18B20_1_data"):
	print (row)
# close the database after use
conn.close()
