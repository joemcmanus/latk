#!/usr/bin/env python3

#latk-reportwwwlogs.py a script for creating network traffic information out of web server logs
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
	print("USAGE: " + sys.argv[0] + " (sqli|pagediff|traffic) Data_Source_ID")
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

def processRecords(db, dataSourceID, result):
	i=0
	curs=db.cursor()
	try:
		curs.execute("DELETE FROM xssData where datasource_id=" + dataSourceID)
	except mysql.connector.errors.Error as e:
		print(e)
		sys.exit()
	for row in result: 
		try:
			curs.execute("""INSERT INTO xssData (id, clientip, query, xsstype, datasource_id) VALUES (%s,%s,%s,%s,%s)""", (None, row[0], row[1], row[2], dataSourceID))
		except mysql.connector.errors.Error as e:
			print(e)
			sys.exit()
		i+=1
	db.commit()   

def pageDiffs(db, dataSourceID):
	curs=db.cursor()
	#Get the last day in the database
	curs.execute("select distinct(time) from webData where datasource_id=" + dataSourceID + " order by time desc limit 1")
	for row in curs:
		rawDate=row[0]
	lastDate=str(rawDate)
	oneWeekPrior=str(rawDate-(7*60*60*24))
	twoWeeksPrior=str(rawDate-(2*7*60*60*24))
	#Get the files present in the last week
	currentUrl=[]
	previousUrl=[]
	curs.execute("select distinct(time), page from webData where datasource_id=" + dataSourceID + " and time < " + lastDate + " and time > " + oneWeekPrior )
	for row in curs:
		currentUrl.append(row[1])
	currentTotal=len(currentUrl)
	print("Current Week Total: " + str(currentTotal))
	
	curs.execute("""select  distinct(time),  page from webData where datasource_id=" + dataSourceID + " and time > %s and time < %s""", (oneWeekPrior, twoWeeksPrior))
	i=0
	for row in curs:
		previousUrl.append(row[1])
	previousTotal=len(previousUrl)
	print("Previous Week Total: " + str(previousTotal))
	
	print("-"* 70)
	print("New files in the current week")
	print("-"* 70)
	currentDiffs=list(set(currentUrl).difference(set(previousUrl)))	
	for url in currentDiffs:
		print(url)
	
	print("-"* 70)
	print("Files in the previous week not present in the most current week")
	print("-"* 70)
	previousDiffs=list(set(previousUrl).difference(set(currentUrl)))	
	for url in previousDiffs:
		print(url)
	
def sqlInjectionCheck(db, dataSourceID):
	records=[]
	curs=db.cursor()
	print("-" * 42)
	curs.execute("select clientIP, query from webData where query != '' and datasource_id=" + dataSourceID)
	for row in curs:
		query=row[1]
		clientIP=row[0]
		#Clear Text SQL injection test, will create false positives. 
		regex=re.compile('drop|delete|truncate|update|insert|select|declare|union|create|concat', re.IGNORECASE)
		if regex.search(query):
			print ("Clear SQL |".rjust(15) +  clientIP.rjust(16) + " | " + query)
			records.append([clientIP, query, "sqli"])

		#look for single quote, = and --
		regex=re.compile('((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))|\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))', re.IGNORECASE)
		if regex.search(query):
			print ("SQLi |".rjust(15) +  clientIP.rjust(16) + " | " + query)
			records.append([clientIP, query, "sqli"])
        
		#look for MSExec
		regex=re.compile('exec(\s|\+)+(s|x)p\w+', re.IGNORECASE)
		if regex.search(query):
			print ("MSSQL Exec |".rjust(15) +  clientIP.rjust(16) + " | " + query)
			records.append([clientIP, query, "sqli"])

		#look for XSS
		regex=re.compile('((\%3C)|<)((\%2F)|\/)*[a-z0-9\%]+((\%3E)|>)|((\%3C)|<)((\%69)|i|(\%49))((\%6D)|m|(\%4D))((\%67)|g|(\%47))[^\n]+((\%3E)|>)', re.IGNORECASE)
		if regex.search(query):
			print ("XSS |".rjust(15) +  clientIP.rjust(16) + " | " + query)
			records.append([clientIP, query, "xss"])
	
	if len(records) > 0:
		print("Adding " + str(len(records)) + " records to db.") 
		processRecords(db, dataSourceID, records)	
	else: 
		print("No XSS/SQLi Indicators Found.")

def trafficSummary(db, dataSourceID):
	curs=db.cursor()
	print("Client IP |".rjust(18) + "Bytes |".rjust(12) )
	print("-" * 42)
	
	curs.execute("select sum(bytesOut) as bytes, clientIP from webData where datasource_id=" + dataSourceID + " group by clientip order by bytes Desc limit 20")
	for row in curs:
		print(str(row[1]).rjust(16) + " |" + str(row[0]).rjust(12) )


	print("Client IP |".rjust(18)  + "# of Pages".rjust(12) )
	print("-" * 42)
	curs.execute(" select count(page) as totalPages, clientIP from webData where datasource_id=" + dataSourceID + " group by clientip order by totalPages Desc limit 20 ")
	for row in curs:
		print(str(row[1]).rjust(16) + " |" + str(row[0]).rjust(10) )


	print("Page |".rjust(58)  + "# of Bytes".rjust(12) )
	print("-" * 72)
	curs.execute(" select sum(bytesOut) as totalBytes, page from webData where datasource_id=" + dataSourceID + " group by page order by totalBytes Desc limit 20")
	for row in curs:
		print(str(row[1]).rjust(56) + " |" + str(row[0]).rjust(10) )

# I need to figure this out, maybe selec the first 100 recs and if bytesIn != null iin any of them, run the test? 
#	if logType == "iis":
#		print("Page |".rjust(58)  + "# of Bytes In".rjust(12) )
#		print("-" * 72)
#		curs.execute(" select sum(bytesIn) as totalBytes, page from webData group by page order by totalBytes Desc limit 20")
#		for row in curs:
#			print(str(row[1]).rjust(56) + " |"  + str(row[0]).rjust(10) )

def commandLineOptions():
	if len(sys.argv) < 3:
		printUsage("Must supply report type and data source id.")
	if sys.argv[1] == "traffic":
		reportType = "traffic"
	elif sys.argv[1] == "pagediff": 
		reportType = "pagediff"
	elif sys.argv[1] == "sqli": 
		reportType = "sqli"
	else: 
		printUsage("Invalid report format specified.")
	if sys.argv[2].isdigit():
		dataSourceID=sys.argv[2]
	else:
		printUsage("Data Source ID must be specified, use latk-setup.py to list and add data sources")		
	return reportType, dataSourceID

cmdOpts=commandLineOptions()
reportType=cmdOpts[0]
dataSourceID=cmdOpts[1]

db=setDB(dbUser, dbPass, dbName, dbHost)

checkDB(db)

if reportType == "pagediff":
	pageDiffs(db, dataSourceID)
if reportType == "traffic":
	trafficSummary(db, dataSourceID)
if reportType == "sqli":
	sqlInjectionCheck(db, dataSourceID)
