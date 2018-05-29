from flask import (
	Blueprint, flash, jsonify, render_template
)

from tempSensor.auth import login_required
from tempSensor.db import get_db

from datetime import datetime

from bokeh.plotting import figure
from bokeh.models import AjaxDataSource, BoxAnnotation, HoverTool
from bokeh.embed import components
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
	
	
	
@bp.route('/')
@login_required
def index():
	source = AjaxDataSource(data_url="/monitor/data", max_size=5000,
							polling_interval=1000, mode='append')

	dates = []
	tempfs = []
	dates, tempfs = get_initial_data()
	# print(dates, tempfs)
	# source.data = dict(x=[], y=[])
	source.data = dict(x=dates, y=tempfs)

	TOOLS = "pan,wheel_zoom,box_zoom,reset,save"
	# TOOLS = [HoverTool(),"pan,wheel_zoom,box_zoom,reset,save"]
	fig = figure(title="DS18B20 Sensor", x_axis_type="datetime", tools=TOOLS)
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
	# fig.add_tools(HoverTool())
	fig.add_tools(hover)
	fig.xgrid.grid_line_color = None
	fig.ygrid.grid_line_alpha = 0.8
	fig.xaxis.axis_label = 'Time'
	fig.yaxis.axis_label = 'Temperature'
	
	r = fig.line('x', 'y', source=source, line_width=2)
	fig.add_layout(BoxAnnotation(top=70, fill_alpha=0.1, fill_color='blue'))
	fig.add_layout(BoxAnnotation(bottom=70, top=80, fill_alpha=0.1, line_color='olive', fill_color='olive'))
	fig.add_layout(BoxAnnotation(bottom=80, fill_alpha=0.1, fill_color='red'))
	
	glyph = r.glyph
	glyph.name = "( Y )"




	script, div = components(fig, CDN)
	return render_template("monitor/index.html", plot_div=div, plot_script=script)
