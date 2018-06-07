#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  logTempStatis.py
#
#  status of logTemp.py

import glob
import time
import os
import subprocess
import sys
import signal
import getopt


# grep for logTemp.py
def main():	
	fh = open('../instance/log_temp_pid.txt', 'r')
	pid = int(fh.read())
	fh.close()
	
	os.kill(pid, signal.SIGUSR1)


# ------------ Execute program 
if __name__ == "__main__":
	main()
	# main(sys.argv[1:])
