
from bokeh.embed import components
from bokeh.models import AjaxDataSource, BoxAnnotation, ColumnDataSource, HoverTool, Range1d
# from bokeh.models.widgets import Button, Slider, TextInput
from bokeh.plotting import figure
from bokeh.resources import CDN

from datetime import datetime, timedelta

from flask import (
	Blueprint, flash, g, jsonify, render_template, Response, request, send_from_directory, session
)

from temp_sensor.auth import login_required
from temp_sensor.db import isrunning, get_db, get_sfreq, start_log, stop_log
# import temp_sensor.camera as Camera
from temp_sensor.camera import Camera

import time

bp = Blueprint('monitor', __name__, url_prefix='/monitor')

pollfreq = 10 # 10 seconds
range = 3600 # 10 minutes
source = ColumnDataSource()

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
		# If j > 0, return jsonified date, else return date string
		if j == 1:
			date = date_to_millis(date)
			return jsonify(x=[date], y=[tempf])
		elif j == 2:
			return jsonify(x=[date], y=[tempf])
		else:
			return date, tempf
		

@login_required
@bp.route('/data/camera/image', methods=['POST'])
def cam_image():
	Camera.kill_thread()
	time.sleep(1)
	img = Camera.take_image()
	# img = "images/20180613_001546.jpg"
	timestamp = img[7:-4]
	# try:
		# timestamp = datetime.strptime(timestamp, "%Y%b%d_%H%M%S")
		# print("timestamp:", timestamp)
		# get_db().execute("INSERT INTO camera (timestamp, filename) VALUES ((?), (?))", (timestamp, img))
		
	# except sqlite3.Error as e:
		# print("sqlite3.Error: ", e.args[0])
	# else:
		# pass
	# Camera.close_camera()
	
	
	return jsonify(img=img, timestamp=timestamp)


def gen(camera):
	"""Video streaming generator function."""
	while True:
		frame = camera.get_frame()
		yield (b'--frame\r\n'
			b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@login_required
@bp.route('/data/camera/stream')
def stream():
	"""Video streaming route. Put this in the src attribute of an img tag."""
	return Response(gen(Camera()),
		mimetype='multipart/x-mixed-replace; boundary=frame')

@login_required
@bp.route('/data/camera/utils/<op>', methods=['POST'])
def cam_utils(op):
	"""Camera utilities."""
	print("op:", op)
	if op == 'kill':
		Camera.kill_thread()
	return jsonify("You rang?")

		
@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
	global pollfreq
	global range
	global source
	post = False
	
	# Set the request method
	if request.method == 'POST':
		range = request.form['range']
		post = True
	
	# Check log_temp.py
	if isrunning() == False:
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
		img = 'images/20180613_001546.jpg'
		return render_template(
			"monitor/index.html",
			plot_script=plot_script,
			plot_div=plot_div,
			pollfreq=pollfreq,
			img=img,
		)
