#!/usr/bin/env python3

#latk-setup.py a script for setting up collections and datasources in the LATK db
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
	print("USAGE: " + sys.argv[0] + " show ")
	print("USAGE: " + sys.argv[0] + " collection CollectionName description_in_quotes")
	print("USAGE: " + sys.argv[0] + " datasource DataSourceName description_in_quotes type collection_id_it_belongs_to")
	print("USAGE: " + sys.argv[0] + " datasource wwwlogs \"Logs from the www server\" apache 1")
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
		curs.execute("show tables like 'collections'")
		rows=curs.fetchall()
		for row in rows:
			print("OK: " + row[0] + " table found") 
	except mysql.connector.errors.Error as e: 
		print("ERROR: collections tables does not exist.")
		print(e)
		sys.exit()
	try:
		curs.execute("show tables like 'dataSources'")
		rows=curs.fetchall()
		for row in rows:
			print("OK: " + row[0] + " table found") 
	except mysql.connector.errors.Error as e: 
		print("ERROR: dataSources tables does not exist.")
		print(e)
		sys.exit()
	curs.close()	

def addCollection(db, collectionName, collectionDesc):
	curs=db.cursor()
	try: 
		curs.execute("""INSERT INTO collections (id, name, description) VALUES(%s,%s,%s)""", ('', collectionName, collectionDesc))
		db.commit()
	except mysql.connector.errors.Error as e:
		print("ERROR: While adding new collection")
		print(e)
		sys.exit()
	
	curs.execute("SELECT id, name, description from collections where name = '" +  collectionName + "'")
	print("Adding new collection " + collectionName + " with id " + "%d" % curs.fetchone()[0])

def addDatasource(db, datasourceName, datasourceDesc, type, collectionID):
	curs=db.cursor()
	try: 
		curs.execute("""INSERT INTO datasources (id, name, description, type, collection_id) VALUES(%s,%s,%s,%s,%s)""", ('', datasourceName, datasourceDesc, type, collectionID))
		db.commit()
	except mysql.connector.errors.Error as e:
		print("ERROR: While adding new collection")
		print(e)
		sys.exit()
	
	curs.execute("""SELECT id, name, description from datasources where name = %s and collection_id= %s""", (datasourceName, collectionID))
	print("Adding new datasrouce " + datasourceName + " with id %d" % curs.fetchone()[0])

def getInfo(db): 
	curs=db.cursor()
	curs.execute("SELECT id, name, description from collections")
	rows=curs.fetchall()
	if len(rows) == 0:
		print("No Collections Found")
	else:
		print("collection_id, name, description")
		for row in rows: 
			print(str(row[0]) + " , " + row[1] + " , " + row[2]) 

	curs.execute("select datasources.name, datasources.id, datasources.type, collections.name as collection_name, collections.id as collection_name from datasources,collections where collections.id = datasources.collection_id")
	rows=curs.fetchall()
	if len(rows) == 0:
		print("No Datasources Found")
	else:
		print("datasource name, datasource id, datasource type,  collection name, collection id")
		for row in rows: 
			print(str(row[0]) + " , " + str(row[1]) + " , " + row[2] + " , " + str(row[3]) + " , " + str(row[4])) 

		
	
def commandLineOptions(): 
	if len(sys.argv) == 2 and sys.argv[1] == "show":
		return("show")
	elif len(sys.argv) == 4:
		if sys.argv[1] == "collection":
			return("collection", sys.argv[2], sys.argv[3])
	elif len(sys.argv) == 6:
		if sys.argv[1] == "datasource": 
			if sys.argv[5].isdigit():
				return("datasource", sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
			else: 
				printUsage("collection id must be a digit")
		else: 
			printUsage("Invalid Options")
		
	else: 
		printUsage("Invalid Options")

cmdOpts=commandLineOptions()
db=setDB(dbUser, dbPass, dbName, dbHost)
checkDB(db)

if cmdOpts[0] == "collection": 
	addCollection(db, cmdOpts[1], cmdOpts[2])
if cmdOpts[0] == "datasource": 
	addDatasource(db, cmdOpts[1], cmdOpts[2], cmdOpts[3], cmdOpts[4])
if cmdOpts == "show":
	getInfo(db)
