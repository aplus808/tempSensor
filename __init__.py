
import os

from datetime import datetime, timedelta
from flask import Flask, request, session


def create_app(test_config=None):
	# Create and configure the app
	app = Flask(__name__, instance_relative_config=True)
	app.config.from_mapping(
		CAMERA_IMAGES = os.path.join(app.static_folder, 'images/'),
		CAMERA_VIDEOS = os.path.join(app.static_folder, 'videos/'),
		DATABASE = os.path.join(app.instance_path, 'temp_sensor.sqlite3'),
		PIDFILE = os.path.join(app.instance_path, 'log_temp_pid.txt'),
		LOGTEMP = os.path.join(app.root_path, 'log_temp.py'),
		PERMANENT_SESSION_LIFETIME = timedelta(minutes = 15),
		# PERMANENT_SESSION_LIFETIME = timedelta(seconds = 20),
		SECRET_KEY = 'dev'
	)

	if test_config is None:
		# Load the instance config, if it exists, when not testing
		app.config.from_pyfile('config.py', silent=True)
	else:
		# Load the test config if passed in
		app.config.from_mapping(test_config)

	# Ensure the instance folder exists
	try:
		os.makedirs(app.instance_path)
	except OSError:
		pass

	
	# Main route
	@app.route('/')
	def index():
		return 'LASERCHICKEN'
	
	# Register db functions with the app
	from . import db
	db.init_app(app)
	
	# Register camera functions with the app
	from . import camera
	camera.init_app(app)
	# app.register_blueprint(camera.bp)
	
	from . import auth
	app.register_blueprint(auth.bp)
	
	from . import monitor
	app.register_blueprint(monitor.bp)
	# app.add_url_rule('/', endpoint='index')

	from . import converter
	
	return app