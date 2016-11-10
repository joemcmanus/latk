#!/usr/bin/env python3

#A script for setting up database connectivity in the LogAnalysisToolKit
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
import sys
import pdb 
import configparser

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
	print("MySQL Configurations options not set in /etc/latk-mysql.conf")

def createDB(dbUser, dbPass, dbName, dbHost):
	try:
		db = mysql.connector.Connect(host=dbHost, unix_socket=dbSock, user=dbUser, passwd=dbPass, db='mysql')
		curs = db.cursor()
		stmt_create="""CREATE DATABASE %s""" % (dbName)
		curs.execute(stmt_create)
		print("OK: Created database " + dbName)
		curs.close()
	except mysql.connector.errors.Error as e: 
		print("ERROR: Unable to connect to MySQL Server.")
		print(e)
		sys.exit()

def createTables(dbUser, dbPass, dbName, dbHost):
	try:
		db = mysql.connector.Connect(host=dbHost, unix_socket=dbSock, user=dbUser, passwd=dbPass, db=dbName)
		curs = db.cursor()
		curs.execute("CREATE TABLE IF NOT EXISTS `beaconData` ( \
			`id` INT NOT NULL AUTO_INCREMENT ,\
			`clientip` VARCHAR(45) NULL ,\
			`destip` VARCHAR(45) NULL ,\
			`mean` VARCHAR(45)  NULL ,\
			`stdDev` VARCHAR(45)  NULL ,\
			`count` INT UNSIGNED NULL ,\
			`beaconScore` INT UNSIGNED  NULL ,\
			`datasource_id` INT UNSIGNED NULL , \
			PRIMARY KEY (`id`) )\
			ENGINE = InnoDB")

		curs.execute("CREATE TABLE IF NOT EXISTS `collections` ( \
			`id` INT NOT NULL AUTO_INCREMENT , \
			`name` VARCHAR(60) NULL , \
			`description` TEXT NULL , \
			PRIMARY KEY (`id`) ) \
			ENGINE = InnoDB")

		curs.execute("CREATE TABLE IF NOT EXISTS `datasources` ( \
			`id` INT NOT NULL AUTO_INCREMENT , \
			`collection_id` INT NULL , \
			`name` VARCHAR(60) NULL , \
			`type` VARCHAR(60) NULL , \
			`description` TEXT NULL , \
			PRIMARY KEY (`id`) ) \
			ENGINE = InnoDB")

		curs.execute("CREATE  TABLE IF NOT EXISTS `proxyData` ( \
			`id` INT NOT NULL AUTO_INCREMENT , \
			`clientip` VARCHAR(45) NULL , \
			`destip` VARCHAR(120) NULL , \
			`time` INT UNSIGNED NULL , \
			`duration` INT UNSIGNED NULL , \
			`bytesIn` INT UNSIGNED NULL , \
			`bytesOut` INT UNSIGNED NULL , \
			`direction` VARCHAR(45) NULL , \
			`bytesDiff` INT UNSIGNED NULL , \
			`contentType` INT UNSIGNED NULL , \
			`page` VARCHAR(120) NULL , \
			`datasource_id` INT UNSIGNED NULL , \
			PRIMARY KEY (`id`) ) \
			ENGINE = InnoDB")

		curs.execute("CREATE  TABLE IF NOT EXISTS `webData` ( \
			`id` INT NOT NULL AUTO_INCREMENT , \
			`clientip` VARCHAR(45) NULL , \
			`time` INT UNSIGNED NULL , \
			`bytesIn` INT UNSIGNED NULL , \
			`bytesOut` INT UNSIGNED NULL , \
			`page` TEXT NULL , \
			`query` TEXT NULL , \
			`datasource_id` VARCHAR(45) NULL , \
			PRIMARY KEY (`id`) ) \
			ENGINE = InnoDB")

		curs.execute("CREATE  TABLE IF NOT EXISTS `xssData` ( \
			`id` INT NOT NULL AUTO_INCREMENT , \
			`clientip` VARCHAR(45) NULL , \
			`query` TEXT NULL , \
			`xsstype` VARCHAR(45) NULL , \
			`datasource_id` VARCHAR(45) NULL , \
			PRIMARY KEY (`id`) ) \
			ENGINE = InnoDB")


	except mysql.connector.errors.Error as e: 
		print("ERROR: Unable to create logData table in  " + dbName + " on " + dbHost + " , check mysql connection info.")
		print(e)
		sys.exit()

	print("OK: Created created tables")


createDB(dbUser, dbPass, dbName, dbHost)
createTables(dbUser, dbPass, dbName, dbHost)
sys.exit()
