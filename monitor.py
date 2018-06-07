from flask import (
	Blueprint, flash, jsonify, render_template, request, session
)

from temp_sensor.auth import login_required
from temp_sensor.db import get_db, get_sfreq, start_log, stop_log

from datetime import datetime, timedelta

from bokeh.io import curdoc
from bokeh.embed import components
from bokeh.models import AjaxDataSource, BoxAnnotation, ColumnDataSource, CustomJS, HoverTool, Range1d
# from bokeh.models.widgets import Button, Slider, TextInput
from bokeh.plotting import figure
from bokeh.resources import CDN

bp = Blueprint('monitor', __name__, url_prefix='/monitor')

pollfreq = 10
range = 3600

def get_initial_data(range):
	db = get_db()
	dates = []
	tempfs = []

	ldate, ltempf = data(j=False)
	ldatetime = datetime.strptime(ldate, "%Y-%m-%d %H:%M:%S")
	fdate = ldatetime - timedelta(seconds=int(range))
	fdate = datetime.strftime(fdate, "%Y-%m-%d %H:%M:%S")
	# print("ldate:", ldate)
	# print("fdate:", fdate)
	rangecount = db.execute('SELECT COUNT(*) FROM temperatures WHERE timestamp BETWEEN ? and ?', (fdate, ldate)).fetchone()[0]
	
	range = min(rangecount, 200)
	interval = rangecount//range
	# print("range:", range)
	# print("rangecount:", rangecount)
	# print("interval:", interval)
	
	
	# for row in db.execute('SELECT timestamp, tempf FROM temperatures ORDER BY timestamp DESC LIMIT ' + str(range)):
	i = 0
	for row in db.execute('SELECT timestamp, tempf FROM temperatures WHERE timestamp BETWEEN ? and ? ORDER BY timestamp DESC', (fdate, ldate)):
		if i % interval == 0:
			dates.append(date_to_millis(row[0]))
			tempfs.append(row[1])
		i += 1
	
	dates = list(reversed(dates))
	tempfs = list(reversed(tempfs))
	# print(len(dates))
	
	return dates, tempfs

def date_to_millis(s):
	epoch = datetime.utcfromtimestamp(0)
	s = datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
	return (s - epoch).total_seconds() * 1000.0



@login_required
@bp.route('/data', methods=['POST'])
def data(j=True):
	date = []
	tempf = []
	try:
		row = get_db().execute('SELECT timestamp, tempf FROM temperatures ORDER BY timestamp DESC LIMIT 1').fetchone()
		
	except sqlite3.Error as e:
		print("sqlite3.Error: ", e.args[0])
	else:
		pass
	
	if row is not None:
		date = row[0]
		tempf = row[1]
		if j:
			return jsonify(x=[date], y=[tempf])
		else:
			return date, tempf
		


@login_required
@bp.route('/test', methods=['POST', 'GET'])
def test():
	if request.method == 'GET':
		args = request.args
		if args is not None and len(args) > 0:
			for arg, val in args.items():
				print(str(arg), str(val))
				

	return jsonify(title=["Bawkbawk"], html=["<p>Jeebus</p>"])
	
	
@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
	global pollfreq
	global range
	post = False
	
	if request.method == 'POST':
		range = request.form['range']
		post = True
	# print("range:", range)

	# Initialize figure data and data source
	source = AjaxDataSource(data_url="/monitor/data", max_size=5000,
							polling_interval=pollfreq * 1000, mode='append')
							
	dates = []
	tempfs = []
	dates, tempfs = get_initial_data(range)
	
	source.data = dict(x=dates, y=tempfs)
	
	# Create the plot
	TOOLS = "pan,wheel_zoom,box_zoom,reset,save"
	fig = figure(title='DS18B20 Sensor', x_axis_type='datetime', tools=TOOLS, plot_height=280, sizing_mode='scale_width')
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
		return render_template(
			"monitor/index.html",
			plot_script=plot_script,
			plot_div=plot_div,
			pollfreq=pollfreq,
		)
