#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# test.py
#  


'''
	Flask test app
'''

# from datetime import datetime, timedelta
# from dateutil import tz
# import io

# from flask import Flask, jsonify, render_template, send_file, make_response, request
from flask import Flask, render_template, make_response, request, flash, url_for, redirect, session
from dbconnect import connection
from wtforms import Form, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import gc

# from pygal import Config

# import sqlite3
# import pygal
# import json
# import cairosvg

app = Flask(__name__)
app.secret_key = '7yuhjvnmghlutio2'

# import test.views

# local classes and functions
class LoginForm(Form):
	username = TextField('Username')
	password = PasswordField('Password', [validators.Required()])

def login_required(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash("You need to login first")
			return redirect(url_for('login_page'))
			
	return wrap


	
# main route
@app.route("/")
@login_required
def index():
	
	flash("Bawk bawk!")
	return render_template('simple.html')
	

@app.route("/logout")
@login_required
def lougout():
	session.clear()
	flash("Logout successful")
	gc.collect()
	return redirect(url_for('login_page'))

			
@app.route("/login", methods = ['GET', 'POST'])
def login_page():
	error = ''
	try:
		form = LoginForm(request.form)
		
		if request.method == 'POST' and form.validate():
			username = form.username.data
			# password = sha256_crypt.encrypt(str(form.password.data))
			# password = form.password.data
			# attempted_username = request.form['username']
			# attempted_password = request.form['password']
			
			# flash(attempted_username)
			# flash(attempted_password)
			
			conn, curs = connection()
			# x = curs.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username,password))
			
			# for row in curs.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username,password)):
				# session['logged_in'] = True
				# session['username'] = username
				# conn.close()
				# gc.collect()
				# return redirect(url_for('index'))
		
			for row in curs.execute("SELECT * FROM users WHERE username = ?", (username,)):
				if sha256_crypt.verify(form.password.data, row[2]):
					session['logged_in'] = True
					session['username'] = username
					conn.close()
					gc.collect()
					flash("Login successful")
					return redirect(url_for('index'))
			
			error = "Invalid credentials.  Try again."
			# flash(error)
			conn.close()
			gc.collect()
		return render_template("login.html", error=error, form=form)
		
	except Exception as e:
		# flash(e)
		return render_template("login.html", error=error, form=form)
	
	return render_template("login.html", form=form)

if __name__ == "__main__":
   app.run(host='0.0.0.0', debug=True)
