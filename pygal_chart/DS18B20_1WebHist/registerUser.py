#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# registerUser.py
#  

import sqlite3
import gc
import sys
from passlib.hash import sha256_crypt
from dbconnect import connection


def main(args):
	conn, curs = connection()
	if len(args) == 3:
		password = sha256_crypt.encrypt(args[2])
		curs.execute("INSERT INTO users (username, password) VALUES (?,?)", (args[1],password))
		conn.commit()
	else:
		print('Wrong number of args: ' + str(len(args)))
	# close the database after use
	conn.close()
	gc.collect()
	
if __name__ == '__main__':
	main(sys.argv)