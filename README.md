Log Analysis Tool Kit 
---------------------
Joe McManus josephmc@alumni.cmu.edu
version 1.5 2011/11/06
Copyright (C) 2011 Joe McManus
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Introduction
---------------------
This is a collection of command line and web based tools for use in incident response and long term analysis use as part of ongoing situational awareness. Often when responding to a security incident the only files available are web server  and proxy server logs. The tools here will aid you in detecting odd traffic such as botnet beaconing and SQL Injection attempts. The large amount of data can be overwhelming and the tools in the Log Analysis Tool Kit can be used to parse these files and build a MySQL database for querying.

Currently the log formats supported are:

Proxy Logs:

    Squid
    Bluecoat

Web Server Logs:

    Apache
    IIS

The tools are currently beta release, so your feedback is greatly appreciated. Please report any issue to the author. 

The tools are written in Python3 and PHP. The tool kit has been tested on Mac OSX and Fedora.


Installation
-----------------
#tar -zxvf LogAnalysisToolKit-version.tar.gz  

If you want to use the web interface, move the PHP code in to your web root. Access it via the web. 

Prereqs
-----------------
Python 3.x: http://www.python.org/
MySQL Connector/Python: https://code.launchpad.net/myconnpy 
Numpy: http://numpy.scipy.org/

Setup Database
-----------------
The first step in using the Log Analysis Tool Kit (LATK) is to create a database. A script is included with LATK to do this. 

latk-createdb.py

Usage:
giskard:logs joe$ ./latk-createdb.py
OK: Created database LogAnalysisToolKit
OK: Created created tables

By default the tools use a local MySQL Server and the user root with no password, you will need to edit the file latk-mysql.conf to match your environment.

[mysql]
user = root
pass =
host = localhost
dbName = LogAnalysisToolKit

Add Data Sources and Collections
-----------------
The Log Analysis Tool Kit works using the concept of  collections and data sources. As an example you would create a collection for investigating an incident on WWW Server. Collections and Data Sources can be added through the script latk-setup.py or using the LATK Web Interface.

latk-setup.py 

First create a collection, the options are shortname and description in quotes.
giskard:logs joe$ ./latk-setup.py collection wwwattack "WWW Server Attack on 6/1/2011"
OK: collections table found
OK: datasources table found
Adding new collection wwwattack with id 1

Next add data sources to your collection, the options are shortname, description, log type and the ID of the collection created above.
giskard:logs joe$ ./latk-setup.py datasource wwwlogs "Logs from the www server" apache 1
OK: collections table found
OK: datasources table found
Adding new datasrouce wwwlogs with id 1
giskard:logs joe$

To display the collections and data sources the show option is passed to latk-setup.py.
giskard:logs joe$ ./latk-setup.py show
OK: collections table found
OK: datasources table found
collection_id, name, description
1 , wwwattack , WWW Server Attack on 6/1/2011
datasource name, datasource id, datasource type,  collection name, collection id
wwwlogs , 1 , apache , wwwattack , 1

Import Proxy Logs
-----------------
To import proxy logs the tool latk-proxyimport.py is used. 

The syntax: 
giskard:logs joe$ ./latk-proxyimport.py
ERROR: Must supply log file name and dataSourceID.
USAGE: ./latk-proxyimport.py LOG_FILE_NAME datasource_id

An example of loading a squid log file would be:
giskard:logs joe$ ./latk-proxyimport.py squid/access.log 4
Logfile: squid/access.log
OK: proxyData table found
Creating list of Connections.
20934 records.

Import Web Logs
-----------------
To import web logs the tool latk-wwwimport.py is used.

The syntax is:
giskard:logs joe$ ./latk-wwwimport.py
ERROR: Must supply log file name and data source id.
USAGE: ./latk-wwwimport.py LOG_FILE_NAME Data_Source_ID

An example of loading an apache log is below:
giskard:logs joe$ ./latk-wwwimport.py apache/combined.log 1
Logfile: apache/combined.log
OK: webData table found
Creating list of Connections.
Imported 917 records.
Import Complete

