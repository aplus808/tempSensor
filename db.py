import os
import subprocess
import signal
import sqlite3
import time

import click
from flask import current_app, g
from flask.cli import with_appcontext

global sfreq
sfreq = 5

def init_app(app):
	app.teardown_appcontext(close_db)
	app.cli.add_command(init_db_command)
	app.cli.add_command(start_log_command)
	app.cli.add_command(stop_log_command)
	
def get_db():
	if 'db' not in g:
		g.db = sqlite3.connect(
			current_app.config['DATABASE'],
			detect_types=sqlite3.PARSE_DECLTYPES
		)
		g.db.row_factory = sqlite3.Row

	return g.db

def init_db():
	db = get_db()

	with current_app.open_resource('schema.sql') as f:
		db.executescript(f.read().decode('utf8'))
	
	pid = start_log(sfreq)

def get_sfreq():
	return sfreq
	
def start_log(sfreq):
	# stop the script if it is already running
	stop_log()
	time.sleep(1)
	
	# check for the db
	from pathlib import Path
	dbfile = Path(current_app.config['DATABASE'])
	try:
		dbpath = dbfile.resolve()
	except FileNotFoundError:
		print("DB file not found, aborting start of log_temp.py")
	else:
		# db exists, start the process
		proc = subprocess.Popen(
			['python3', current_app.config['LOGTEMP'], '--freq', str(sfreq)]
		)
		print("DB file found, starting log_temp.py (pid = %s)" % (str(proc.pid)))
		return proc.pid

def stop_log():
	# os.kill(getpid(), signal.SIGUSR1)
	# check if a file exists on disk ##
	## If exists, delete it else show message on screen ##
	pidfile = current_app.config['PIDFILE']
	if os.path.exists(pidfile):
		try:
			#read pid, delete pidfile, kill process
			pid = getpid(pidfile)
			os.remove(pidfile)
			os.kill(pid, signal.SIGUSR1)
			# print("Sent kill signal to %s" % (pid))
		except OSError as e:
			print ("Read/Delete/Kill pid error: %s: %s" % (e.errno, e.strerror))
		
	else:
		print("Unable to find %s" % pidfile)
	
	
def getpid(pidfile):
	fh = open(pidfile, 'r')
	pid = int(fh.read())
	fh.close()
	return pid
	
def isrunning():
	pid = getpid(current_app.config['PIDFILE'])
	try:
		os.kill(pid, 0)
	except OSError:
		return False
	else:
		return True
	

@click.command('stop-log')
@with_appcontext
def stop_log_command():
	stop_log()
	click.echo("Stopped log_temp.py")

@click.command('start-log')
@click.option('--freq', help="Sample frequency in seconds")
@with_appcontext
def start_log_command(freq):
	global sfreq
	if freq is not None and freq > 0:
		sfreq = freq
		print("New freq arg, %s.  Updating sfreq" % (str(sfreq)))
	else:
		print("Using default freq, " + str(sfreq))
	pid = start_log(sfreq)
	if pid is not None:
		click.echo("Started log_temp.py (pid = " + str(pid) + ")")

@click.command('init-db')
@with_appcontext
def init_db_command():
	"""Clear the existing data and create new tables."""
	init_db()
	click.echo("Initialized the database.")

def close_db(e=None):
	db = g.pop('db', None)

	if db is not None:
		db.close()