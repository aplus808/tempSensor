import datetime
import io
import os
import subprocess
import signal
import sqlite3
import time

import click
from flask import current_app, g
from flask.cli import with_appcontext
from picamera import PiCamera
from temp_sensor.base_camera import BaseCamera
from temp_sensor.db import get_db, log_image


class Camera(BaseCamera):
	iso = 0
	image_resolution = (2592, 1944)
	stream_resolution = (1280, 720)
	video_resolution = (1920, 1080)
	# resolution = [image_resolution, stream_resolution, video_resolution]

	@staticmethod
	def frames():
		# with picamera.PiCamera(
		with PiCamera(
			resolution = Camera.stream_resolution,
			# framerate = Fraction(1, 6),
			# sensor_mode = 3,
		) as camera:
			camera.iso = Camera.iso
			# Let camera warm up
			time.sleep(3)

			stream = io.BytesIO()
			for _ in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
				# return current frame
				stream.seek(0)
				yield stream.read()

				# reset stream for next frame
				stream.seek(0)
				stream.truncate()
	
	@staticmethod
	def take_image():
		with PiCamera(
			resolution = Camera.image_resolution,
			# sensor_mode = 2,
		) as camera:
			camera.iso = Camera.iso
			time.sleep(3)
			now = datetime.datetime.now()
			ts = datetime.datetime.strftime(now, "%Y%m%d_%H%M%S")
			imgpath = current_app.config['CAMERA_IMAGES'] +  ts + ".jpg"
			imgstats = {
				'ts'				: ts,
				'timestamp'			: now,
				'filename'			: ts + '.jpg',
				'filepath'			: 'images/' + ts + '.jpg',
				'content_type'		: 'JPEG',
				'iso'				: int(camera.iso),
				'resolution'		: str(camera.resolution),
				'framerate'			: int(camera.framerate),
				'framerate_range'	: str(camera.framerate_range),
				'sensor_mode'		: int(camera.sensor_mode),
			}
			camera.capture(imgpath)
			camera.stop_preview()
			log_image(imgstats)
			return imgstats

	@staticmethod
	def take_video():
		with PiCamera(
			resolution = Camera.video_resolution,
			# sensor_mode = 2,
		) as camera:
			camera.iso = Camera.iso
			time.sleep(5)
			now = datetime.datetime.now()
			ts = datetime.datetime.strftime(now, "%Y%m%d_%H%M%S")
			vidpath = current_app.config['CAMERA_VIDEOS'] +  ts + ".h264"
			imgstats = {
				'ts'				: ts,
				'timestamp'			: now,
				'filename'			: ts + ".h264",
				'filepath'			: 'videos/' + ts + '.h264',
				'content_type'		: 'H264',
				'iso'				: int(camera.iso),
				'resolution'		: str(camera.resolution),
				'framerate'			: int(camera.framerate),
				'framerate_range'	: str(camera.framerate_range),
				'sensor_mode'		: int(camera.sensor_mode),
			}
			camera.start_recording(vidpath, format='h264')
			camera.wait_recording(10)
			camera.stop_recording()
			camera.stop_preview()
			log_image(imgstats)
			return imgstats


	@staticmethod
	def set_iso(iso):
		Camera.iso = int(iso)
		print("ISO set to", Camera.iso)

	@staticmethod
	def set_resolution(resolution):
		Camera.image_resolution = resolution
		print("Image resolution set to", Camera.image_resolution)


class Converter():
	# thread = None  # background thread that reads frames from camera
	# frame = None  # current frame is stored here by background thread
	# last_access = 0  # time of last client access to the camera
	# killthread = False
	# event = CameraEvent()
	viddir = None

	def __init__(self):
		"""Initialize Converter"""
		Converter.viddir = current_app.config["CAMERA_VIDEOS"]
		
		
	# @staticmethod
	# def kill_thread():
		# """"Set killthread to True"""
		# BaseCamera.killthread = True
		# print("! killthread:", BaseCamera.killthread)

	# @classmethod
	# def _thread(cls):
		# """Camera background thread."""
		# print('Starting camera thread.')
		# frames_iterator = cls.frames()
		# for frame in frames_iterator:
			# BaseCamera.frame = frame
			# BaseCamera.event.set()  # send signal to clients
			# time.sleep(0)

			# If there hasn't been any clients asking for frames in the last 10 seconds then stop the thread
			# if time.time() - BaseCamera.last_access > 10 or BaseCamera.killthread == True:
				# frames_iterator.close()
				# print('Stopping camera thread.')
				# break
		# BaseCamera.thread = None


def get_camera_images_path():
	return current_app.config['CAMERA_IMAGES']

def get_camera_videos_path():
	return current_app.config['CAMERA_VIDEOS']

def init_app(app):
	app.cli.add_command(init_camera_command)
	app.cli.add_command(image_camera_command)

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
	p = Camera.take_image()
	click.echo("Click!  images/" + p['filename'])

@click.command('video-camera')
@with_appcontext
def image_camera_command():
	"""Take a 10 second video"""
	p = Camera.take_video()
	click.echo("Click!  videos/" + p['filename'])
