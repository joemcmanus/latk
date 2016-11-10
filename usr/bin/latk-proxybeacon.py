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

import platform
import configparser
import os
import re
import sys
import time
from urllib.parse import urlparse
from time import mktime, gmtime, strftime
import shlex
import pdb 
import threading
import queue
from multiprocessing import Pool, cpu_count

def printUsage(error):
	print("ERROR: " + error)
	print("USAGE: " + sys.argv[0] + " reportType  datasource_id")
	print("USAGE: " + sys.argv[0] + " (beacongen|beaconshow) X ")
	sys.exit()


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
	print("ERROR: Python 3.0 or greater is required for this to run. Sorry")
	sys.exit()

try: 
	import numpy
except: 
	printUsage("Numpy is not installed, please install and retry.")

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

def checkDB(db, tableName): 
	try:
		curs=db.cursor()
		curs.execute("show tables like '" +  tableName + "'")
		rows=curs.fetchall()
		for row in rows:
			print("OK: " + row[0] + " table found") 
	except mysql.connector.errors.Error as e: 
		print("ERROR: " + tableName + " table does not exist.")
		print(e)
		sys.exit()
	curs.close()	



def processRecords(db, result, dataSourceID):
	i=0
	curs=db.cursor()
	for row in result: 
		try:
			curs.execute("""INSERT INTO beaconData (id, clientip, destip, mean, stdDev, count, beaconScore, datasource_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", (None, row[0], row[1], row[2], row[3], row[4], row[5], dataSourceID))
		except mysql.connector.errors.Error as e:
			print(e)
			sys.exit()
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
		printUsage("Must supply report type dataSourceID.")

	if sys.argv[1] == "beacongen": 
		reportType = "beacongen"
	elif sys.argv[1] == "beaconshow": 
		reportType = "beaconshow"
	else: 
		printUsage("Invalid report type  specified.")

	if sys.argv[2].isdigit:
		dataSourceID=sys.argv[2]
	else: 
		printUsage("Invalid dataSourceID specified.")

	return dataSourceID, reportType
	
def createMemoryTable(db, dataSourceID):
	print("Creaiting Memory Table")
	curs=db.cursor()
	try: 
		curs.execute("create table memoryTable ENGINE=MEMORY select id, clientip, destip, time, bytesDiff, contentType from proxyData where dataSource_id=" + dataSourceID)
	except mysql.connector.errors.Error as e: 
		print("ERROR: Unable to create memory table")
		print(e)
		sys.exit()
	print("Creating index")
	curs.execute("create index srcdst on memoryTable (clientIP, destIP)")

		
def dropMemoryTable(db):
	curs=db.cursor()
	try: 
		curs.execute("drop table if exists memoryTable")
	except mysql.connector.errors.Error as e: 
		print("ERROR: Unable to drop memory table")
		print(e)
		sys.exit()

def cleanupData(db, dataSourceID):
	curs=db.cursor()
	curs.execute("delete from beaconData where datasource_id=" + dataSourceID)

def createPairs(db):
	curs=db.cursor()
	#Create a list of unique src and dests
	print("Creating list of Unique Source and Dest IPs.",)
	ipSets=[]
	curs.execute("SELECT DISTINCT clientip, destip FROM memoryTable ORDER BY clientip")
	for row in curs:
		x=row[0]
		y=row[1]
		ipSets.append([x, y]) 
	print(str(len(ipSets)) + " records. ") 

	#Create a dictionary of destip addresses and a count of occurance 
	curs.execute("SELECT destip, COUNT(*) FROM proxyData where datasource_id=" + dataSourceID + " GROUP BY destip")
	destipCount={}
	for row in curs:
		destipCount[row[0]] = row[1]
	return destipCount , ipSets

def processChunk(ipSet, db, dataSourceType, destipCount): 
	x=[]
	tmp=createDeltas(db, ipSet, destipCount, dataSourceType)
	if tmp != None:
		x.append(tmp)
	return x

def createDeltas(db, ipSet, destipCount, dataSourceType):
	curs=db.cursor()
	#Select a list of times
	i=0
	timeDiffs=[]
	try: 
		query="SELECT time, bytesDiff, contentType FROM memoryTable WHERE clientip='" + ipSet[0] + "' and destip='" + ipSet[1] + "' order by time";
		curs.execute(query)
		threading.enumerate()
		for row in curs:
			if i == 0:
				lastTime=row[0]
				contentSum = row[2]
				bytesSum = row[1]
			else:
				currentTime=row[0]
				diff=currentTime - lastTime
				timeDiffs.append(diff)
				lastTime=currentTime
				contentSum=contentSum + row[2]
				bytesSum=bytesSum + row[1]
			i += 1
	
		#Generate time information
		timeDiffs=numpy.array(timeDiffs)
		timeDiffStdDev=round(timeDiffs.std(),3)
		timeDiffMean=round(timeDiffs.mean(),2)

		#This check throws away records with a mean time of 0 
		if timeDiffMean > 0:
			beaconScore=calcBeaconScore(timeDiffStdDev, timeDiffMean, i, contentSum, ipSet[1], destipCount.get(ipSet[1]), bytesSum, dataSourceType)
			return(ipSet[0], ipSet[1], str(timeDiffMean), str(timeDiffStdDev), i, beaconScore)

	except mysql.connector.errors.Error as e: 
		return None	

def calcBeaconScore(stdDev, mean, count, contentSum, url, roa, bytesSum, dataSourceType): 

	#Generate stdDev Factor
	if stdDev < 0.5:
		timeStdDevFactor=2
	elif stdDev < 1:
		timeStdDevFactor=1
	else:
		timeStdDevFactor=0

	#Generate meanFactor
	if mean > 900:
		timeMeanFactor=1
	else:
		timeMeanFactor=0

	#Generate count factor
	if count <= 3: 
		countFactor=-3
	else:
		countFactor=0

	#Generate fileType factor
	contentAvg=contentSum/ count * 100
	if contentAvg > 50:
		fileTypeFactor=1
	else:
		fileTypeFactor=0

	#Generate URL Factor
	if ipCheck(url) == True:
		ipURL=2
	else:
		ipURL=0	

	#Generate rateOfOccurance factor
	if roa >= 5:
		rateOfOccuranceFactor=0
	else:
		rateOfOccuranceFactor=1
	
	#Generate bytesFactor
	bytesAvg=bytesSum/count*100
	if dataSourceType == 'bluecoat':
		if bytesAvg > 500:
			bytesFactor=1
		else:
			bytesFactor=0
	else:
		if bytesAvg > 5000:
			bytesFactor=1
		else:
			bytesFactor=0

	#Generate a beacon Probability
	beaconScore= rateOfOccuranceFactor + fileTypeFactor + bytesFactor + timeMeanFactor + timeStdDevFactor + ipURL + countFactor
	return beaconScore

def printBeaconResults(db, dataSourceID): 
	curs=db.cursor()
	print("Client IP |".rjust(18) \
                + "Dest IP |".rjust(54) \
                + "Count |".rjust(7) \
                + "Mean Time |".rjust(12) \
                + "Std Dev |".rjust(12) \
		+ "Score".rjust(7))
	print("-" * 111)

	curs.execute("SELECT clientip, destip, count, mean, stdDev, beaconScore FROM beaconData where beaconScore >= 3 and datasource_id=" + dataSourceID + " ORDER BY beaconScore DESC, stdDev ASC")
	for row in curs:
		if row[5] >= 6:
			beaconProbability="High"
		elif row[5] >= 3:
			beaconProbability="Medium"
		else:
			beaconProbability="Low"

		print(row[0].rjust(16) + " |" \
			+ row[1].rjust(52) + " |" \
			+ str(row[2]).rjust(5) + " |" \
			+ str(row[3]).rjust(10) + " |" \
			+ str(row[4]).rjust(10) + " |" \
			+ beaconProbability.rjust(7) )


def getType(db, dataSourceID):
	curs=db.cursor()
	curs.execute("SELECT type from datasources where id=" + dataSourceID) 
	dataSourceType=curs.fetchone()[0]
	print("Data Source Type is:"  + dataSourceType)
	return dataSourceType




cmdOpts=commandLineOptions()
dataSourceID=cmdOpts[0]
reportType=cmdOpts[1]

db=setDB(dbUser, dbPass, dbName, dbHost)
checkDB(db, 'proxyData')

dataSourceType=getType(db, dataSourceID)
cleanupData(db, dataSourceID)
dropMemoryTable(db)

createMemoryTable(db, dataSourceID)

# result queue
result = []

# job queue
queue = queue.Queue()


ipPairs=createPairs(db)
destipCount=ipPairs[0]
ipSets=ipPairs[1]


#Here is where we do all of the real work.
i=0
j=0
for ipSet in ipSets:
	i+=1
	if j == 99:
		print("Processing " + str(i) + " of " + str(len(ipSets)))
		j=0
	else: 
		j+=1
	
	result.extend(processChunk(ipSet, db, dataSourceType, destipCount))

#Insert the records in to the db. 
processRecords(db, result, dataSourceID) 
dropMemoryTable(db)
