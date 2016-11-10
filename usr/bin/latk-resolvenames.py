#!/usr/bin/env python3

#latk-resolvename.py a script for resolving names from sqlite databses created by the log analysis toolkit
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
import socket
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
	print("USAGE: " + sys.argv[0] + " query")
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



logFile="query-output.csv"


def openLogFile(logFile):
	fh = open(logFile, 'w') 
	return fh

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
		curs.execute("show tables like 'collections'")
		rows=curs.fetchall()
		for row in rows:
			print("OK: " + row[0] + " table found") 
	except mysql.connector.errors.Error as e: 
		print("ERROR: collections tables does not exist.")
		print(e)
		sys.exit()
	curs.close()

def resolveNames(db, query, fh):
	curs=db.cursor()
	curs.execute(query)
	for row in curs:
		try: 
			nameTuple = socket.gethostbyaddr(row[0])
			name=nameTuple[0]
		except:
			name = "unresolvable"

		print(row[0] + "," + name)
		fh.write(row[0] + "," + name + "\n")
def commandLineOptions():
	if len(sys.argv) < 2:
		printUsage("Must supply query.")
	query=sys.argv[1]
	return query
	

query=commandLineOptions()
fh=openLogFile(logFile)
db=setDB(dbUser, dbPass, dbName, dbHost)
checkDB(db)

#This will work on all Log Analysis ToolKit databases, so you can use destIP too.
#Go Crazy

#This query will resolve all names that went to your phpmyadmin page
#query="select DISTINCT(clientIP) FROM logData WHERE page LIKE '%phpmyadmin%'"

#This query will resolve all client nmes that went to sites like google.com
#query="select DISTINCT(clientip) FROM proxyData WHERE destip LIKE '%google.com%'"
resolveNames(db, query, fh)

fh.close()

