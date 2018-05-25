import sqlite3

def connection():
	conn = sqlite3.connect('../sensorsData.db')
	curs = conn.cursor()
	
	return conn, curs