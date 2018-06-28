
from bokeh.embed import components
from bokeh.models import AjaxDataSource, BoxAnnotation, ColumnDataSource, HoverTool, Range1d
# from bokeh.models.widgets import Button, Slider, TextInput
from bokeh.plotting import figure
from bokeh.resources import CDN

from datetime import datetime, timedelta

from flask import (
	current_app, Blueprint, flash, g, jsonify, render_template, Response, request, send_from_directory, session
)

from temp_sensor.auth import login_required
from temp_sensor.db import (
	sensorisrunning, get_db, get_gallery, get_imagestats, get_sfreq, start_log, stop_log
)

from temp_sensor.camera import Camera
from temp_sensor.converter import Converter

import sqlite3
import time

bp = Blueprint('monitor', __name__, url_prefix='/monitor')

pollfreq = 10 # 10 seconds
range = 3600 # 10 minutes
source = ColumnDataSource()
no_reset = ["monitor.data", "auth.logout"]

@bp.before_app_request
def reset_timeout():
	if (request.endpoint not in no_reset):
		# print("Reset session timeout from:", request.endpoint)
		session.modified = True
		try:
			now = datetime.now()
			session['last_active'] = now
		except:
			pass

def get_initial_data(range):
	db = get_db()
	dates = []
	tempfs = []

	ldate, ltempf = data(j=0)
	ldatetime = datetime.strptime(ldate, "%Y-%m-%d %H:%M:%S")
	fdate = ldatetime - timedelta(seconds=int(range))
	fdate = datetime.strftime(fdate, "%Y-%m-%d %H:%M:%S")
	rangecount = db.execute('SELECT COUNT(*) FROM temperatures WHERE timestamp BETWEEN ? and ?', (fdate, ldate)).fetchone()[0]
	
	range = min(rangecount, 200)
	interval = rangecount//range
	
	i = 0
	for row in db.execute('SELECT timestamp, tempf FROM temperatures WHERE timestamp BETWEEN ? and ? ORDER BY timestamp DESC', (fdate, ldate)):
		if i % interval == 0:
			dates.append(date_to_millis(row[0]))
			tempfs.append(row[1])
		i += 1
	
	dates = list(reversed(dates))
	tempfs = list(reversed(tempfs))
	
	return dates, tempfs

def date_to_millis(s):
	epoch = datetime.utcfromtimestamp(0)
	s = datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
	return (s - epoch).total_seconds() * 1000.0


@login_required
@bp.route('/data', methods=['POST'])
def data(j=1):
	date = []
	tempf = []
	try:
		row = get_db().execute('SELECT timestamp, tempf FROM temperatures ORDER BY timestamp DESC LIMIT 1').fetchone()
		
	except sqlite3.Error as e:
		print("sqlite3.Error: ", e.args[0])
	else:
		pass
	
	if request.form.get('j') is not None:
		j = int(request.form.get('j'))
	
	if row is not None:
		date = row[0]
		tempf = row[1]
		
		delta = None
		keep_polling = True
		now = datetime.now()
		timeout = current_app.config['PERMANENT_SESSION_LIFETIME']
		timeout = timeout.total_seconds()
		try:
			last_active = session['last_active']
			delta = now - last_active
			if delta.seconds > int(timeout):
				# session['last_active'] = now
				print("Session expired\n\tdelta.seconds: %s" % delta.seconds)
				keep_polling = False
		except:
			print("Session has no last_active")
			session['last_active'] = now
			pass


		# If j > 0, return jsonified date, else return date string
		if j == 1:
			date = date_to_millis(date)
			return jsonify(x=[date], y=[tempf])
		elif j == 2:
			return jsonify(x=[date], y=[tempf], keep_polling=[keep_polling])
		else:
			return date, tempf
		

@login_required
@bp.route('/data/camera/image', methods=['POST'])
def cam_image():
	Camera.kill_thread()
	time.sleep(1)
	imgstats = Camera.take_image()
	
	# return jsonify(img="images/" + imgstats['filename'], timestamp=imgstats['ts'], imgstats=imgstats)
	return jsonify(imgstats=imgstats)

@login_required
@bp.route('/data/camera/video', methods=['POST'])
def cam_video():
	Camera.kill_thread()
	time.sleep(1)
	imgstats = Camera.take_video()
	imgstats = Converter.convert(imgstats['filename'])
	
	return jsonify(imgstats=imgstats)

@login_required
@bp.route('/data/camera/video/latest', methods=['POST'])
def cam_video_latest():
	Camera.kill_thread()
	# time.sleep(1)
	imgstats = get_imagestats(content_type='MP4')
	
	return jsonify(imgstats=imgstats)


def gen(camera):
	"""Video streaming generator function."""
	while True:
		frame = camera.get_frame()
		yield (b'--frame\r\n'
			b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@login_required
@bp.route('/data/camera/stream')
def cam_stream():
	"""Video streaming route. Put this in the src attribute of an img tag."""
	return Response(gen(Camera()),
		mimetype='multipart/x-mixed-replace; boundary=frame')

@login_required
@bp.route('/data/camera/utils/<op>', methods=['POST'])
def cam_utils(op):
	"""Camera utilities."""
	
	if op == "kill":
		Camera.kill_thread()
		return jsonify("Camera killed")
	elif op == "iso":
		Camera.set_iso(request.form['iso'])
		return jsonify("ISO: " + str(Camera.iso))
	elif op == "resolution":
		Camera.set_resolution((int(request.form['resolution[w]']), int(request.form['resolution[h]'])))
		return jsonify("Resolution: " + str(Camera.resolution))
	elif op == "convert":
		Converter.convert(request.form['filename'])
		return jsonify("Converted file")


		
@bp.route('/gallery')
@login_required
def show_gallery(format='JPEG'):
	gallery = get_gallery(format)
	return render_template("monitor/gallery.html", gallery=gallery) 

@bp.route('/gallery_modal')
@login_required
def show_gallery_modal():
	gallery = get_gallery()
	return render_template("monitor/gallery_bs_modal.html", gallery=gallery)

@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
	global pollfreq
	global range
	global source
	post = False
	now = datetime.now()
	session['last_active'] = now
	
	# Set the request method
	if request.method == 'POST':
		range = request.form['range']
		post = True
	
	# Check log_temp.py
	if sensorisrunning() == False:
		start_log(pollfreq)
		time.sleep(1)

	# Initialize figure data and data source
	source = AjaxDataSource(
		data_url="/monitor/data",
		max_size=5000,
		polling_interval=pollfreq * 1000,
		mode='append'
	)
							
	dates = []
	tempfs = []
	dates, tempfs = get_initial_data(range)
	source.data = dict(x=dates, y=tempfs)
		
	# Create the plot
	TOOLS = "pan,wheel_zoom,box_zoom,reset,save"
	fig = figure(
		title='DS18B20 Sensor',
		x_axis_type='datetime',
		tools=TOOLS,
		height=200,
		# width=300,
		sizing_mode='scale_width',
	)
	hover = HoverTool(
		tooltips=[
			('temp', '@y{0.00}'),
			('time', '@x{%F %T}'),
		],
		formatters={
			'x'	:	'datetime', # use 'datetime' formatter for 'x' field
		},
		mode='vline'
	)
	fig.add_tools(hover)
	fig.xgrid.grid_line_color = None
	fig.ygrid.grid_line_alpha = 0.8
	fig.xaxis.axis_label = 'Time'
	fig.yaxis.axis_label = 'Temperature'

	fig.y_range=Range1d(60, 90)
	
	fig.line('x', 'y', source=source, line_width=2)
	fig.add_layout(BoxAnnotation(top=70, fill_alpha=0.1, fill_color='blue'))
	fig.add_layout(BoxAnnotation(bottom=70, top=80, fill_alpha=0.1, line_color='green', fill_color='green'))
	fig.add_layout(BoxAnnotation(bottom=80, fill_alpha=0.1, fill_color='red'))
	
	plot_script, plot_div = components(fig)
	
	
	if post:
		return (jsonify(plotscript=plot_script, plotdiv=plot_div))
	else:
		# img = cam_image().get_json()['img']
		imgstats = cam_image().get_json()['imgstats']
		return render_template(
			"monitor/index.html",
			plot_script=plot_script,
			plot_div=plot_div,
			pollfreq=pollfreq,
			imgstats=imgstats,
		)


@bp.route('/test')
def test():
	print("HEY!")
	print(get_imagestats())
	return render_template("monitor/index2.html")