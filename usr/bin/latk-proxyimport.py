#!/usr/bin/env python3

#latk-importproxy.py a script for detecting beaconing in proxy logs
#Joe McManus josephmc@alumni.cmu.edu
#version 1.5.2 2011.11.06
#Copyright (C) 2011 Joe McManus
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

from sqlite3 import * 
import platform
import configparser
import os
import io
import re
import sys
import time
from urllib.parse import urlparse
from time import mktime, gmtime, strftime
import shlex
import pdb 
from multiprocessing import Pool, cpu_count
import threading
import queue

def printUsage(error):
	print("ERROR: " + error)
	print("USAGE: " + sys.argv[0] + " LOG_FILE_NAME datasource_id")
	sys.exit()

try: 
	import numpy
except: 
	printUsage("Numpy is not installed, please install and retry.")

#Set Database info
config=configparser.RawConfigParser()
try: 
	config.read('/etc/latk-mysql.conf')
	dbUser=config.get("mysql", "user")
	dbPass=config.get("mysql", "pass")
	dbName=config.get("mysql", "dbName")
	dbHost=config.get("mysql", "host")
	dbSock=config.get("mysql", "sock")
except: 
	printUsage("MySQL Configurations options not set in /etc/latk-mysql.conf")


if platform.python_version() < "3.0.0": 
	printUsage("Python 3.0 or greater is required for this to run. Sorry")

try:
	import mysql.connector
except: 
	print("ERROR: Python MySQL Connector not installed.")
	sys.ext()

def setDB(dbUser, dbPass, dbName, dbHost):
	try:
		db = mysql.connector.Connect(host=dbHost, unix_socket=dbSock, user=dbUser, passwd=dbPass, db=dbName, buffered=True)
		return db
	except mysql.connector.errors.Error as e: 
		print("ERROR: Unable to connect to MySQL Server")
		print(e)
		sys.exit()

def checkDB(db): 
	try:
		curs=db.cursor()
		curs.execute("show tables like 'proxyData'")
		rows=curs.fetchall()
		for row in rows:
			print("OK: " + row[0] + " table found") 
	except mysql.connector.errors.Error as e: 
		print("ERROR: proxyData tables does not exist.")
		print(e)
		sys.exit()
	curs.close()



def processRecords(db, result, dataSourceID):
	i=0
	curs=db.cursor()
	for row in result: 
		curs.execute("""INSERT INTO proxyData (id, clientip, destip, time, bytesDiff, bytesIn, bytesOut, direction, contentType, page, datasource_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (None, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], dataSourceID ))

		i+=1
	print("Adding " + str(i) + " records to db")
	db.commit()	

def ipCheck(ip_str):
	pattern = r"\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
	if re.match(pattern, ip_str):
		return True
	else:
		return False

def commandLineOptions():
	if len(sys.argv) < 3:
		printUsage("Must supply log file name, dataSourceID.")

	#Check to see if the logfile exists
	logFile=sys.argv[1]
	if os.path.isfile(logFile):
		print("Logfile: " + logFile) 
	else:
		printUsage("Logfile " + logFile + " does not exist")
	if sys.argv[2].isdigit:
		dataSourceID=sys.argv[2]
	else: 
		printUsage("Invalid dataSourceID specified.")
	return logFile, dataSourceID

def processChunk(chunk, logFile, logType, db, datasource_id): 
	i=0
	x=[]
	fh=open(logFile, 'r', encoding='iso-8859-1')
	fh.seek(chunk[0])
	for line in fh.read(chunk[1]).splitlines():
		tmp=(parseLogLine(line, logType))
		if tmp != None:
			x.append(tmp)
		i+=1
	print("Parsed " + str(i) + " lines.")
	return (x) 

def getchunks(file):
	#chunkSize=round(os.path.getsize(file)/4)
	chunkSize=1024*1024
	f = io.FileIO(file, "r")
	while 1:
		start = f.tell()
		f.seek(chunkSize, 1)
		s = f.readline()
		yield start, f.tell() - start
		if not s:
			break
		
def parseLogLine(line, logType):
	#Check to see if the line looks right.
	if line[:1].isdigit():
		try:
			logEntry=shlex.split(line, posix=True)
			if logType == "bluecoat":
				if len(logEntry) > 12:
					if ipCheck(logEntry[3]): 
						clientIP=logEntry[3]
						destIP=logEntry[15]
						page=logEntry[17]
						timestamp=logEntry[0] + " " + logEntry[1]
						timestamp=time.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
						timestamp=time.mktime(timestamp)
			
						#Calculate the diffence in uploaded/downloaded bytes
						bytesDiff=abs(int(logEntry[22]) - int(logEntry[23]))

						#Get the content type
						if logEntry[13] == "text/html":
							content="1"
						else:
							content="0"
	
						bytesIn=int(logEntry[22])
						bytesOut=int(logEntry[23])
						if bytesIn > bytesOut:
							direction="in"
						elif bytesIn < bytesOut:
							direction="out"
						else:
                                                	direction="unknown"


					elif ipCheck(logEntry[2]):
						clientIP=logEntry[2]
						destIP=logEntry[12]
						page=str(shlex.split(str(urlparse(logEntry[7]).path)))
						timestamp=time.localtime(float(logEntry[0]))
						timestamp=time.mktime(timestamp)

						#Calculate the diffence in uploaded/downloaded bytes
						bytesIn=int(logEntry[5])
						bytesOut=''
						bytesDiff=''
						direction=''

						#Get the content type
						if logEntry[13] == "text/html":
							content="1"
						else:
							content="0"

					return(clientIP, destIP, timestamp, bytesDiff, bytesIn, bytesOut, direction, content, page)

	
			if logType == "squid":
				if len(logEntry) > 8:
					clientIP=logEntry[2]
					peerinfo=urlparse(logEntry[6])
					destIP=peerinfo.hostname
					page=peerinfo.path
					if destIP == None:
						destIP = "Unknown"
					timestamp=time.localtime(float(logEntry[0]))
					timestamp=time.mktime(timestamp)
					bytesDiff=abs(int(logEntry[4]))
					bytesIn=logEntry[4]
					bytesOut=''
					direction=''
		
					#Get the content type
					if logEntry[9] == "text/html":
						content="1"
					else:
						content="0"
					
					return ( clientIP, destIP, timestamp, bytesDiff, bytesIn, bytesOut, direction, content, page )
		except: 
			#print("Unable to read line, skipping")
			pass

def getType(db, dataSourceID):
	curs=db.cursor()
	curs.execute("SELECT type from datasources where id=" + dataSourceID) 
	dataSourceType=curs.fetchone()[0]
	print("Data Source Type is:"  + dataSourceType)
	return dataSourceType

# job queue
queue = queue.Queue()

# result queu, pagee
result = []

class Worker(threading.Thread):
	def run(self):
		while 1:
			args = queue.get()
			if args is None:
				break
			result.extend(processChunk(*args))
			queue.task_done()

cmdOpts=commandLineOptions()
logFile=cmdOpts[0]
dataSourceID=cmdOpts[1]

db=setDB(dbUser, dbPass, dbName, dbHost)
checkDB(db)
logType=getType(db, dataSourceID)

if cpu_count() >= 8: 
	workerCount = 8
else: 
	workerCount=(cpu_count() * 2 )


print("Starting " + str(workerCount) + " workers.")
for i in range(workerCount):
	w = Worker()
	w.setDaemon(1)
	w.start()


for chunk in getchunks(logFile):
	queue.put((chunk, logFile, logType, db, dataSourceID))

queue.join()

processRecords(db, result, dataSourceID) 
#print("Processed: " + str(sum(result)) + " records")
