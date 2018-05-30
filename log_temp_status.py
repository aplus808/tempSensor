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
import getopt


# grep for logTemp.py
def main():	
	# catdata = subprocess.run('ps', '-eaf', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	catdata = subprocess.Popen(['ps', '-eaf'], stdout=subprocess.PIPE)
	grepdata = subprocess.Popen(['grep', 'python3 logTemp.py'], stdin=catdata.stdout, stdout=subprocess.PIPE)
	# out,err = catdata.communicate()
	out = grepdata.stdout
	# out_decode = out.decode('utf-8')
	# lines = out_decode.split('\n')
	
	for line in out:
		print(line.decode('utf-8').strip())



# ------------ Execute program 
if __name__ == "__main__":
	main()
	# main(sys.argv[1:])
