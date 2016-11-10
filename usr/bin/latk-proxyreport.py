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
import os
import re
import sys
import time
from urllib.parse import urlparse
from time import mktime, gmtime, strftime
import shlex
import pdb 
import configparser

def printUsage(error):
	print("ERROR: " + error)
	print("USAGE: " + sys.argv[0] + " reportType  datasource_id")
	print("USAGE: " + sys.argv[0] + " (summary|detail) X ")
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

def ipCheck(ip_str):
	pattern = r"\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
	if re.match(pattern, ip_str):
		return True
	else:
		return False

def commandLineOptions():
	if len(sys.argv) < 3:
		printUsage("Must supply report type dataSourceID.")

	if sys.argv[1] == "summary":
		reportType = "summary"
	elif sys.argv[1] == "detail": 
		reportType = "detail"
	else: 
		printUsage("Invalid report type  specified.")

	if sys.argv[2].isdigit:
		dataSourceID=sys.argv[2]
	else: 
		printUsage("Invalid dataSourceID specified.")

	return dataSourceID, reportType
	
def getType(db, dataSourceID):
	curs=db.cursor()
	curs.execute("SELECT type from datasources where id=" + dataSourceID) 
	dataSourceType=curs.fetchone()[0]
	print("Data Source Type is:"  + dataSourceType)
	return dataSourceType

def bluecoatDetail(db, dataSourceID):
	curs=db.cursor()
	print("Client IP |".rjust(18) \
                + "Dest IP |".rjust(44) \
                + "Direction |".rjust(14) \
		+ "# of Recs. |".rjust(12) \
                + "Bytes In |".rjust(12) \
                + "Bytes Out |".rjust(12) \
                + "Total Bytes |".rjust(12) )

	print("-" * 130)

	curs.execute("SELECT clientIP, destIP, SUM(bytesIn), SUM(bytesOut), (SUM(bytesIn)+ SUM(bytesOut)) as byteTotal,  COUNT(id) AS count FROM proxyData WHERE datasource_id=" + dataSourceID + " GROUP BY clientIP, destIP  order by byteTotal DESC")
	for row in curs:
		bytesIn=int(row[2])
		bytesOut=int(row[3])
		if bytesIn > bytesOut:
			direction="in"
		elif bytesOut > bytesIn:
			direction="out"
		else:
       			direction="=="		
		print(row[0].rjust(16) + " |" \
			+ row[1].rjust(42) + " |" \
			+ direction.rjust(12) + " |" \
			+ str(row[5]).rjust(10) + " |" \
			+ str(row[2]).rjust(10) + " |" \
			+ str(row[3]).rjust(10) + " |"\
			+ str(row[4]).rjust(12) )
	
def bluecoatSummary(db, dataSourceID):
	curs=db.cursor()
	print("Client IP |".rjust(18) \
                + "Bytes In |".rjust(12) \
                + "Bytes Out |".rjust(12) \
                + "Total Bytes |".rjust(12) 
		+ "# of Hosts".rjust(12) )

	print("-" * 70)

	curs.execute("SELECT clientIP, SUM(bytesIn), SUM(bytesOut), (SUM(bytesIn)+ SUM(bytesOut)) as byteTotal, COUNT(DISTINCT(destIP)) AS count FROM proxyData WHERE datasource_id=" + dataSourceID + " GROUP BY clientIP order by byteTotal DESC")
	for row in curs:
		bytesIn=int(row[1])
		bytesOut=int(row[2])
		print(row[0].rjust(16) + " |" \
			+ str(row[1]).rjust(12) + " |" \
			+ str(row[2]).rjust(10) + " |" \
			+ str(row[3]).rjust(10) + " |" \
			+ str(row[4]).rjust(10) )


def squidDetail(db, dataSourceID):
	curs=db.cursor()
	print("Client IP |".rjust(18) \
                + "Dest IP |".rjust(54) \
                + "Direction |".rjust(14) \
		+ "# of Recs. |".rjust(12) \
                + "Total Bytes |".rjust(12) )

	print("-" * 114)

	curs.execute("SELECT clientIP, destIP, SUM(bytesIn) AS bytes, direction, COUNT(id) AS count FROM proxyData WHERE datasource_id=" + dataSourceID + " GROUP BY clientIP, destIP order by bytes DESC")
	for row in curs:
		print(row[0].rjust(16) + " |" \
			+ row[1].rjust(52) + " |" \
			+ row[3].rjust(12) + " |" \
			+ str(row[4]).rjust(10) + " |" \
			+ str(row[2]).rjust(12) )

def squidSummary(db, dataSourceID):
	curs=db.cursor()
	print("Client IP |".rjust(18) \
                + "Bytes |".rjust(12) \
		+ "# of Hosts".rjust(12) )

	print("-" * 42)

	curs.execute("SELECT clientIP, SUM(bytesIn) AS bytes, COUNT(DISTINCT(destIP)) AS count FROM proxyData WHERE datasource_id=" + dataSourceID + " GROUP BY clientIP order by bytes DESC")
	for row in curs:
		print(row[0].rjust(16) + " |" \
			+ str(row[1]).rjust(12) + " |" \
			+ str(row[2]).rjust(10) )


cmdOpts=commandLineOptions()
dataSourceID=cmdOpts[0]
reportType=cmdOpts[1]

db=setDB(dbUser, dbPass, dbName, dbHost)
checkDB(db)

dataSourceType=getType(db, dataSourceID)

if dataSourceType == "bluecoat" and reportType == "detail":
	bluecoatDetail(db, dataSourceID)

if dataSourceType == "bluecoat" and reportType == "summary":
	bluecoatSummary(db, dataSourceID)

if dataSourceType == "squid" and reportType == "detail":
	squidDetail(db, dataSourceID)

if dataSourceType == "squid" and reportType == "summary":
	squidSummary(db, dataSourceID)

