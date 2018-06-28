#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  converter.py
#
#  Convert h264 to mp4

import datetime
import os
import shlex
import subprocess
import sys

from temp_sensor.db import (
	get_db, get_imagestats, log_image, set_active
)

class Converter(object):
    # Flask video path from current working directory
    viddir = os.getcwd() + '/temp_sensor/static/videos/'
    # print("viddir:", viddir)

    # Set db variables
    # dbpath = os.getcwd() + '/instance/temp_sensor.sqlite3'

    # try:
    #     for (dirpath, dirnames, filenames) in os.walk(viddir):
    #         break
    # except OSError as e:
    #     print("OSError:", e)
    # else:
    #     pass
    
    @staticmethod
    def convert(filename):
        print("Converting:", filename)
        filepath = Converter.viddir + filename
        imgstats = get_imagestats(filename, 'H264')
        # print(filepath)

        # FFMPEG command
        args = shlex.split("ffmpeg -y -framerate 30 -i " + filepath + " -c copy " + filepath.split('.')[0] + ".mp4")
        try:
            ffmpegdata = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output, error = ffmpegdata.communicate()
            if output and ffmpegdata.returncode == 0:
                print("ffmpeg ret>", ffmpegdata.returncode)
                # print("OK> output:", output)
                set_active(imgstats, 0)
                imgstats['id'] = None
                imgstats['filename'] = filename.split('.')[0] + ".mp4"
                imgstats['filepath'] = "videos/" + imgstats['filename']
                imgstats['content_type'] = 'MP4'
                # print("imgstats:", imgstats)
                log_image(imgstats)
            if ffmpegdata.returncode !=0:
                print("ffmpeg ret> ", ffmpegdata.returncode)
                print("ffmpeg STDOUT>", output.strip())
                print("ffmpeg STDERR>", error.strip())
        except OSError as e:
            print("OSError > ", e.errno)
            print("OSError > ", e.strerror)
            print("OSError > ", e.filename)
        except:
            print("Error > ", sys.exc_info())
        
        
        return imgstats
        
            

def main():
    c = Converter()
    c.convert(Converter.filepaths[0])

# ------------ Execute program 
if __name__ == "__main__":
	main()