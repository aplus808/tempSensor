import datetime
import os
import subprocess
import signal
import time

import click
from flask import current_app, g
from flask.cli import with_appcontext
from picamera import PiCamera

global sfreq
sfreq = 5

def init_app(app):
	app.cli.add_command(init_camera_command)
	app.cli.add_command(image_camera_command)
	
def get_camera():
	if current_app.config['CAMERA'] is None:
		# print("CAMERA does not exist")
		camera = PiCamera(
			resolution = (1280, 720),
			# framerate = Fraction(1, 6),
			# sensor_mode = 3,
		)
		# camera.rotation = 180
		# camera.shutter_speed = 500000
		camera.iso = 800
		# print(camera)
		current_app.config['CAMERA'] = camera
	# print("current_app.config['CAMERA']:", current_app.config['CAMERA'])
	return current_app.config['CAMERA']

def close_camera():
	if current_app.config['CAMERA'] is not None:
		current_app.config['CAMERA'].close()
		current_app.config['CAMERA'] = None

def get_camera_images_path():
	return current_app.config['CAMERA_IMAGES']

def get_camera_videos_path():
	return current_app.config['CAMERA_VIDEOS']

def init_camera():
	# check for the camera directories
	from pathlib import Path
	import shutil
	imgdir = current_app.config['CAMERA_IMAGES']
	viddir = current_app.config['CAMERA_VIDEOS']
	
	for dir in [imgdir, viddir]:
		try:
			dirpath = Path(dir).resolve()
		except FileNotFoundError:
			print(dir, "not found.")
			os.makedirs(dir)
		else:
			print("Removing", dir)
			shutil.rmtree(dir)
			print("Creating", dir)
			os.makedirs(dir)
	
def take_image():
	camera = get_camera()
	camera.start_preview()
	time.sleep(10)
	ts = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d_%H%M%S")
	imgpath = current_app.config['CAMERA_IMAGES'] +  ts + ".jpg"
	imgstr = "images/" + ts + ".jpg"
	# print("imgpath:", imgpath)
	camera.capture(imgpath)
	camera.stop_preview()
	close_camera()
	return imgstr
	
def take_video():
	camera = get_camera()
	camera.start_preview()
	time.sleep(5)
	ts = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d_%H%M%S")
	vidpath = current_app.config['CAMERA_VIDEOS'] +  ts + ".h264"
	vidstr = "videos/" + ts + ".h264"
	# print("vidpath:", vidpath)
	camera.start_recording(vidpath, format='h264')
	camera.wait_recording(10)
	camera.stop_recording()
	camera.stop_preview()
	close_camera()
	return vidstr
	
@click.command('init-camera')
@with_appcontext
def init_camera_command():
	"""Clear the existing image/video directories."""
	init_camera()
	click.echo("Initialized the camera.")

@click.command('image-camera')
@with_appcontext
def image_camera_command():
	"""Take a single image"""
	p = take_image()
	click.echo("Click! " + p)

@click.command('video-camera')
@with_appcontext
def image_camera_command():
	"""Take a 10 second video"""
	p = take_video()
	click.echo("Click! " + p)
