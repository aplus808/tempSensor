from flask import (
	Blueprint, flash, jsonify, render_template, request
)

from temp_sensor.auth import login_required
from temp_sensor.db import get_db, get_sfreq, start_log, stop_log

from datetime import datetime

from bokeh.io import curdoc
from bokeh.embed import components
from bokeh.models import AjaxDataSource, BoxAnnotation, CustomJS, HoverTool
# from bokeh.models.widgets import Button, Slider, TextInput
from bokeh.plotting import figure
from bokeh.resources import CDN

bp = Blueprint('monitor', __name__, url_prefix='/monitor')


def get_initial_data():
	db = get_db()
	dates = []
	tempfs = []
	for row in db.execute('SELECT timestamp, tempf FROM temperatures ORDER BY timestamp DESC LIMIT 100'):
		dates.append(date_to_millis(row[0]))
		tempfs.append(row[1])
	
	dates = list(reversed(dates))
	tempfs = list(reversed(tempfs))

	return dates, tempfs

def date_to_millis(s):
	epoch = datetime.utcfromtimestamp(0)
	s = datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
	return (s - epoch).total_seconds() * 1000.0
	

def polling_slider_handler():
	# callback = CustomJS(args=dict(source=source), code="""
		# var data = source.data;
		# var f = cb_obj.value
		# var x = data['x']
		# var y = data['y']
		# for (var i = 0; i < x.length; i++) {
			# y[i] = Math.pow(x[i], f)
		# }
		# source.change.emit();
	# """)
	return CustomJS(code="""
		console.log('Slider changed value:' + cb_obj.value)
	""")


@login_required
@bp.route('/data', methods=['POST'])
def data():
	db = get_db()
	date = []
	tempf = []
	for row in db.execute('SELECT timestamp, tempf FROM temperatures ORDER BY timestamp DESC LIMIT 1'):
		date = date_to_millis(row[0])
		tempf = row[1]
	
	return jsonify(x=[date], y=[tempf])

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
	if request.method == 'POST':
		# Set polling interval
		pfreq = int(request.form['pollfreq'])
		sfreq = get_sfreq()
		
		if sfreq > pfreq:
			flash("Sample frequency changed to " + str(pfreq))
			start_log(pfreq)
		elif pfreq > 600 and sfreq != 600:
			start_log(600)
			flash("Sample frequency changed to its max, 600")

		pollfreq = pfreq
		flash("Polling frequency changed to " + str(pfreq))
		
		# Set time range
		if request.form['timerange'] is not None:
			timerange = int(request.form['timerange'])
	else:
		pollfreq = 30
		if pollfreq != get_sfreq():
			start_log(30)
	
	# Initialize figure data and data source
	source = AjaxDataSource(data_url="/monitor/data", max_size=5000,
							polling_interval=pollfreq * 1000, mode='append')

	dates = []
	tempfs = []
	dates, tempfs = get_initial_data()
	source.data = dict(x=dates, y=tempfs)
	
	# Determine current timerange
	# rmilli = dates[-1] - dates[0]
	# print("rmilli: " + str(rmilli))
	# if rmilli/604800000 < 1:
		# r = 604800				# 7d
	# if rmilli/86400000 < 1:
		# r = 86400				# 1d
	# if rmilli/43200000 < 1:
		# r = 43200				# 12h
	# if rmilli/3600000 < 1:
		# r = 3600				# 1h
	# if rmilli/1800000 < 1:
		# r = 1800				# 30m
	# if rmilli/60000 < 1:
		# r = 60					# 1m
	# if rmilli/30000 < 1:
		# r = 30					# 30s
	# if rmilli/10000 < 1:
		# r = 10					# 10s
	# if rmilli/1000 < 1:
		# r = 1					# 1s
	
	# print(r)

	# Create the plot
	TOOLS = "pan,wheel_zoom,box_zoom,reset,save"
	fig = figure(title='DS18B20 Sensor', x_axis_type='datetime', tools=TOOLS, sizing_mode='scale_width')
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
	
	fig.line('x', 'y', source=source, line_width=2)
	fig.add_layout(BoxAnnotation(top=70, fill_alpha=0.1, fill_color='blue'))
	fig.add_layout(BoxAnnotation(bottom=70, top=80, fill_alpha=0.1, line_color='olive', fill_color='olive'))
	fig.add_layout(BoxAnnotation(bottom=80, fill_alpha=0.1, fill_color='red'))
	
	plot_script, plot_div = components(fig)
	
	# Create widgets
	# polling = Slider(title="Polling Frequency (seconds)", value=30, start=1, end=60, step=1)
	# polling.js_on_change('value', polling_slider_handler())
	# freqbtn = Button(label="Submit")
	# freqbtn.js_on_click(freqbtn_handler())
	
	# poll_script, poll_div = components(polling)
	# freqbtn_script, freqbtn_div = components(freqbtn)
	
	return render_template("monitor/index.html", plot_script=plot_script, plot_div=plot_div, pollfreq=pollfreq)
