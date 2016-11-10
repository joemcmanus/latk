#!/usr/bin/env python3

#latk-importwwwlogs.py a script for importing web server log data in to a database as part of the LATK
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
	print("USAGE: " + sys.argv[0] + " LOG_FILE_NAME Data_Source_ID")
	sys.exit()


if platform.python_version() < "3.0.0": 
	print("ERROR: Python 3.0 or greater is required for this to run. Sorry")
	sys.exit()
try:
	import mysql.connector
except: 
	print("ERROR: Python MySQL Connector not installed.")
	sys.ext()

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
		curs.execute("show tables like 'webData'")
		rows=curs.fetchall()
		for row in rows:
			print("OK: " + row[0] + " table found") 
	except mysql.connector.errors.Error as e: 
		print("ERROR: webData tables does not exist.")
		print(e)
		sys.exit()
	curs.close()	

def processRecords(db, result, dataSourceID):
	i=0
	curs=db.cursor()
	for row in result: 
		curs.execute("""INSERT INTO webData (id, clientip, time, bytesIn, bytesOut, page, datasource_id, query) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""", ('', row[0], row[1], row[2], row[3], row[4], dataSourceID, row[5]))
		i+=1
	print("Adding " + str(i) + " records to db")
	db.commit()     

def parseLogLine(line, logType):
	#Check to see if the line looks right.
	if line[:1].isdigit():
		try:
			logEntry=shlex.split(line)
			if logType == "apache":
				if len(logEntry) > 8:
					returnCode = logEntry[6]
					if returnCode != "404":
						clientIP=str(logEntry[0])
						timestamp=time.strptime(logEntry[3], "[%d/%b/%Y:%H:%M:%S")
						timestamp=str(time.mktime(timestamp))
						bytesOut=str(logEntry[7])
						bytesIn=''
						page=shlex.split(str(urlparse(logEntry[5]).path))
						page=str(page[1])
						query=str(urlparse(logEntry[5]).query)
						return(clientIP, timestamp, bytesIn , bytesOut, page, query)
			if logType == "iis":
				if len(logEntry) > 8:
					print(logEntry)
					returnCode = logEntry[14]
					if returnCode != "404":
						clientIP=logEntry[9]
						timestamp=time.strptime(logEntry[0] + " " + logEntry[1], "%Y-%m-%d %H:%M:%S")
						timestamp=time.mktime(timestamp)
						bytesOut=logEntry[17]
						bytesIn=logEntry[18]
						page=logEntry[5]
						query=logEntry[6]
						return(clientIP, timestamp, bytesIn, bytesOut, page, query)
			if logType == "iis-short":
				if len(logEntry) > 8:
					returnCode = logEntry[11]
					if returnCode != "404":
						clientIP=logEntry[8]
						timestamp=time.strptime(logEntry[0] + " " + logEntry[1], "%Y-%m-%d %H:%M:%S")
						timestamp=time.mktime(timestamp)
						page=logEntry[4]
						query=logEntry[6]
						bytesIn=''
						bytesOut=''
						return(str(clientIP), str(timestamp), bytesIn , bytesOut, str(page), query)
		except:
			#print('ERROR: Unable to parse line ' + str(i) + " skipping.")
			pass
				
def commandLineOptions():
	if len(sys.argv) < 3:
		printUsage("Must supply log file name and data source id.")
	logFile=sys.argv[1]
	if os.path.isfile(logFile):
		print("Logfile: " + logFile) 
	else:
		printUsage("Logfile " + logFile + " does not exist")
	if sys.argv[2].isdigit():
		dataSourceID=sys.argv[2]
	else:
		printUsage("Data Source ID must be specified, use latk-setup.py to list and add data sources")		
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
	chunkSize=1024*1024
	f = io.FileIO(file, "r")
	while 1:
		start = f.tell()
		f.seek(chunkSize, 1)
		s = f.readline()
		yield start, f.tell() - start
		if not s:
			break
                
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

