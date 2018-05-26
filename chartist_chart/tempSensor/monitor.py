from flask import (
	Blueprint, flash, g, jsonify, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from tempSensor.auth import login_required
from tempSensor.db import get_db

from datetime import datetime, timedelta
# from dateutil import tz

bp = Blueprint('monitor', __name__, url_prefix='/monitor')

@bp.route('/')
@login_required
def index():
	# db = get_db()
	# posts = db.execute(
		# 'SELECT p.id, title, body, created, author_id, username'
		# ' FROM post p JOIN user u ON p.author_id = u.id'
		# ' ORDER BY created DESC'
	# ).fetchall()
	
	
	# return render_template('blog/index.html', posts=posts)
	return render_template('/monitor/index.html')
	
@bp.route('/data')
@login_required
def data():
	db = get_db()
	sampleSize = 10
	dates = []
	tempfs = []
	for row in db.execute('SELECT timestamp, tempf FROM temperatures ORDER BY timestamp DESC LIMIT ?', (sampleSize,)):
		dates.append(str(row[0])[11:])
		tempfs.append(row[1])
	
	# return jsonify({'sample' : sample(range(1,10), 5)})
	# dates = list(map(lambda d: datetime.strptime(d, '%Y-%m-%d %H:%M:%S'), dates))
	dates = list(reversed(dates))
	tempfs = list(reversed(tempfs))
	# print(dates)
	
	return jsonify({
		'tempfs' : tempfs,
		'dates' : dates})