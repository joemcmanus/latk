#!/usr/bin/env python3

#latk-ios.py a script for creating an index of suspicious IPs
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

def printUsage(error):
	print("ERROR: " + error)
	print("USAGE: " + sys.argv[0] + " Data_Source_ID")
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

def getBaseLine(db, dataSourceID, dataSourceType): 
	print("Creating Baseline")
	curs=db.cursor()
	records=[]
	if dataSourceType == "apache" or dataSourceType == "iis" or dataSourceType == "iis-short": 
		query="select count(page), count(distinct(page)), sum(bytesIn + bytesOut), (select count(query) from xssData where datasource_id=" + dataSourceID + ")  from webData where datasource_id=" + dataSourceID
		curs.execute(query)
		for row in curs:
			totalHits=row[0]
			totalPages=row[1]
			totalBytes=row[2]
			totalXss=row[3]
		return int(totalHits), int(totalPages), int(totalBytes), int(totalXss)
	else: 
		query="select count(distinct(destip)) as ipCount , sum(bytesIn + bytesOut) as bytesTotal, (select sum(beaconScore) from beaconData where datasource_id=" + dataSourceID + ") as beaconTotal from proxyData where datasource_id=" + dataSourceID
		curs.execute(query)
		for row in curs:
			totalDests=row[0]
			totalBytes=row[1]
			totalBeacons=row[2]
		return int(totalDests), int(totalBytes), int(totalBeacons)
	
def getScores(db, dataSourceID, dataSourceType, baseline):
	print("Generating Suspicious IP Index")
	curs=db.cursor()
	records=[]
	if dataSourceType == "apache" or dataSourceType == "iis" or dataSourceType == "iis-short": 
		curs.execute("select clientip, count(page), count(distinct(page)), sum(bytesIn + bytesOut), (select count(query) from xssData where xssData.clientip=webData.clientip and datasource_id=" + dataSourceID + ")  from webData where datasource_id=" + dataSourceID + " group by clientIP")
		for row in curs:
			clientIP=row[0]
			hitsScore=round((int(row[1])/baseline[0]*100),2)
			pageScore=round((int(row[2])/baseline[1]*100),2)
			if row[3] == 0: 
				bytesScore=0
			else: 
				bytesScore=round((int(row[3])/baseline[2]*100),2)
			if row[4] == 0: 
				xssScore=0
			else: 
				xssScore=round((int(row[4])/baseline[3]*100),2)
			suspicionScore=round((hitsScore + pageScore + bytesScore + xssScore),2)
			records.append([clientIP, hitsScore, pageScore, bytesScore, xssScore, suspicionScore])

	else: 
		curs.execute("select clientip, count(distinct(destip)) as ipCount , sum(bytesIn + bytesOut) as bytesTotal, (select sum(beaconScore) from beaconData where beaconData.clientip=proxyData.clientip) as beaconTotal from proxyData where datasource_id=" + dataSourceID + " group by clientIP")
		for row in curs:
			clientIP=row[0]
			ipScore=round((int(row[1])/baseline[0]*100),2)
			bytesScore=round((int(row[2])/baseline[1]*100),2)
			if row[3] == None: 
				beaconScore=0
			else: 
				beaconScore=round((int(row[3])/baseline[2]*100),2)
			suspicionScore=round((ipScore + bytesScore + beaconScore),2)
			records.append([clientIP, ipScore, bytesScore, beaconScore, suspicionScore])

	return records

def printResults(records,  dataSourceType):
	if dataSourceType == "apache" or dataSourceType == "iis" or dataSourceType == "iis-short": 
		records.sort(key=lambda x: x[5], reverse=True)
		print("Client IP |".rjust(18) \
			+ "% TTL Hits |".rjust(16) \
			+ "% TTL Pages |".rjust(16) \
			+ "% TTL Bytes |".rjust(16) \
			+ "% TTL XSS/SQLi |".rjust(16) \
			+ "Suspicion Index |".rjust(16) )
		print("-" * 100)
		for row in records:
			print(str(row[0]).rjust(18) \
				+ str(row[1]).rjust(14) + " |" \
				+ str(row[2]).rjust(14) + " |" \
				+ str(row[3]).rjust(14) + " |"\
				+ str(row[4]).rjust(14) + " |"\
				+ str(row[5]).rjust(14) )
	else: 
		records.sort(key=lambda x: x[4], reverse=True)
		print("Client IP |".rjust(18) \
			+ "% TTL IPS |".rjust(16) \
			+ "% TTL Bytes |".rjust(16) \
			+ "% TTL Beacon |".rjust(16) \
			+ "Suspicion Index |".rjust(16) )
		print("-" * 100)
		for row in records:
			print(str(row[0]).rjust(18) \
				+ str(row[1]).rjust(14) + " |" \
				+ str(row[2]).rjust(14) + " |" \
				+ str(row[3]).rjust(14) + " |"\
				+ str(row[4]).rjust(14) )
		
def commandLineOptions():
	if len(sys.argv) < 2:
		printUsage("Must supply data source id.")
	if sys.argv[1].isdigit():
		dataSourceID=sys.argv[1]
	else:
		printUsage("Data Source ID must be specified, use latk-setup.py to list and add data sources")		
	return dataSourceID

def getType(db, dataSourceID):
	curs=db.cursor()
	curs.execute("SELECT type from datasources where id=" + dataSourceID) 
	dataSourceType=curs.fetchone()[0]
	print("Data Source Type is:"  + dataSourceType)
	return dataSourceType


dataSourceID=commandLineOptions()

db=setDB(dbUser, dbPass, dbName, dbHost)

checkDB(db)
dataSourceType=getType(db, dataSourceID)
baseline=getBaseLine(db, dataSourceID, dataSourceType)
records=getScores(db, dataSourceID, dataSourceType, baseline)
printResults(records, dataSourceType)
