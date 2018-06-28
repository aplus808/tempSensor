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

def close_db(e=None):
	db = g.pop('db', None)

	if db is not None:
		db.close()

def get_db():
	if 'db' not in g:
		g.db = sqlite3.connect(
			current_app.config['DATABASE'],
			detect_types=sqlite3.PARSE_DECLTYPES
		)
		g.db.row_factory = sqlite3.Row

	return g.db

def get_gallery(format):
	gallery = [];
	try:
		for row in get_db().execute("SELECT * FROM camera WHERE content_type = (?) AND active = 1 ORDER BY timestamp DESC LIMIT 12", (format,)):
			image = [row['id'], row['filepath']]
			# gallery.append(row['filepath'])
			gallery.append(image)
	except sqlite3.Error as e:
		print("sqlite3.Error: ", e.args[0])
	return gallery

def get_imagestats(filename=None, content_type='JPEG', active=1):
	imgstats = {
				'id'				: None,
				'ts'				: None,
				'timestamp'			: None,
				'filename'			: None,
				'filepath'			: None,
				'content_type'		: None,
				'iso'				: None,
				'resolution'		: None,
				'framerate'			: None,
				'framerate_range'	: None,
				'sensor_mode'		: None,
				'active'			: None
			}
	try:
		if filename is not None:
			row = get_db().execute("SELECT * FROM camera WHERE filename = (?) AND content_type = (?) AND active = (?) ORDER BY timestamp DESC LIMIT 1", (filename, content_type, active)).fetchone()
		else:
			row = get_db().execute("SELECT * FROM camera WHERE content_type = (?) AND active = (?) ORDER BY timestamp DESC LIMIT 1", (content_type, active)).fetchone()
		if row is not None:
			for rkey in row.keys():
				for iskey in imgstats.keys():
					if iskey == rkey:
						imgstats[rkey] = row[rkey]
	except sqlite3.Error as e:
		print("sqlite3.Error: ", e.args[0])
	else:
		pass

	return imgstats


def get_pid(pidfile):
	fh = open(pidfile, 'r')
	pid = int(fh.read())
	fh.close()
	return pid

def get_sfreq():
	return sfreq

def init_app(app):
	app.teardown_appcontext(close_db)
	app.cli.add_command(init_db_command)
	app.cli.add_command(start_log_command)
	app.cli.add_command(stop_log_command)
	
def init_db():
	db = get_db()

	with current_app.open_resource('schema.sql') as f:
		db.executescript(f.read().decode('utf8'))
	
	pid = start_log(sfreq)

@click.command('init-db')
@with_appcontext
def init_db_command():
	"""Clear the existing data and create new tables."""
	init_db()
	click.echo("Initialized the database.")

def log_image(imgstats):
	try:
		get_db().execute("INSERT INTO camera (timestamp, content_type, filename, filepath, iso, resolution, framerate, framerate_range, sensor_mode, active) VALUES (datetime('now', 'localtime'), (?), (?), (?), (?), (?), (?), (?), (?), (?))", (imgstats['content_type'], imgstats['filename'], imgstats['filepath'], imgstats['iso'], imgstats['resolution'], imgstats['framerate'], imgstats['framerate_range'], imgstats['sensor_mode'], 1))
		get_db().commit()
	except sqlite3.Error as e:
		print("sqlite3.Error: ", e.args[0])
	else:
		pass	

	
def sensorisrunning():
	pid = get_pid(current_app.config['PIDFILE'])
	try:
		os.kill(pid, 0)
	except OSError:
		return False
	else:
		return True

def set_active(imgstats, active=0):
	try:
		get_db().execute("UPDATE camera SET active = (?) WHERE id = (?)", (active, imgstats['id']))
		get_db().commit()
	except sqlite3.Error as e:
		print("sqlite3.Error: ", e.args[0])

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

def stop_log():
	# os.kill(get_pid(), signal.SIGUSR1)
	# check if a file exists on disk ##
	## If exists, delete it else show message on screen ##
	pidfile = current_app.config['PIDFILE']
	if os.path.exists(pidfile):
		try:
			#read pid, delete pidfile, kill process
			pid = get_pid(pidfile)
			os.remove(pidfile)
			os.kill(pid, signal.SIGUSR1)
			# print("Sent kill signal to %s" % (pid))
		except OSError as e:
			print ("Read/Delete/Kill pid error: %s: %s" % (e.errno, e.strerror))
		
	else:
		print("Unable to find %s" % pidfile)

@click.command('stop-log')
@with_appcontext
def stop_log_command():
	stop_log()
	click.echo("Stopped log_temp.py")
