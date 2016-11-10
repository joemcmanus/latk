<?php
////////////////////////////
//Log Analysis Tool Kit (LATK)
//version 1.5.2 2011.11.06
//Copyright (C) 2011 Joe McManus - josephmc@alumni.cmu.edu 
//This program is free software: you can redistribute it and/or modify
//it under the terms of the GNU General Public License as published by
//the Free Software Foundation, either version 3 of the License, or
//at your option) any later version.
//
//This program is distributed in the hope that it will be useful,
//but WITHOUT ANY WARRANTY; without even the implied warranty of
//MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//GNU General Public License for more details.
//
//You should have received a copy of the GNU General Public License
//along with this program.  If not, see <http://www.gnu.org/licenses/>.
////////////////////////////



isset ( $_REQUEST['i'] ) ? $i = $_REQUEST['i'] : $i = "";
isset ( $_REQUEST['s'] ) ? $s = $_REQUEST['s'] : $s = "";
isset ( $_REQUEST['ip'] ) ? $ip = $_REQUEST['ip'] : $ip = "";
isset ( $_REQUEST['word'] ) ? $word = $_REQUEST['word'] : $word = "";
isset ( $_REQUEST['t'] ) ? $t = $_REQUEST['t'] : $t = "";
isset ( $_REQUEST['h'] ) ? $h = $_REQUEST['h'] : $h = "";
isset ( $_REQUEST['f'] ) ? $f = $_REQUEST['f'] : $f = "";
isset ( $_REQUEST['d'] ) ? $d = $_REQUEST['d'] : $d = "";
isset ( $_REQUEST['c'] ) ? $c = $_REQUEST['c'] : $c = "";
isset ( $_FILES['userfile']['name'] ) ? $file = $_FILES['userfile']['name'] : $file = "";
isset ( $_FILES['userfile']['size'] ) ? $size = $_FILES['userfile']['size'] : $size = "";
isset ( $_FILES['userfile']['tmp_name'] ) ? $tempfile = $_FILES['userfile']['tmp_name'] : $tempfile = "";
isset ( $_REQUEST['ulf'] ) ? $ulf = $_REQUEST['ulf'] : $ulf = "";
isset ( $_REQUEST['collectionName'] ) ? $collectionName = $_REQUEST['collectionName'] : $collectionName = "";
isset ( $_REQUEST['collectionDesc'] ) ? $collectionDesc = $_REQUEST['collectionDesc'] : $collectionDesc = "";
isset ( $_REQUEST['dataSourceName'] ) ? $dataSourceName = $_REQUEST['dataSourceName'] : $dataSourceName = "";
isset ( $_REQUEST['dataSourceDesc'] ) ? $dataSourceDesc = $_REQUEST['dataSourceDesc'] : $dataSourceDesc = "";
isset ( $_REQUEST['dataSourceType'] ) ? $dataSourceType = $_REQUEST['dataSourceType'] : $dataSourceType = "";

function connect(&$db){
	$latkMysqlConf="/etc/latk-mysql.conf";
	if (!file_exists($latkMysqlConf)) { 
		echo "ERROR: DB Config file not found: $latkMysqlConf";
		exit;
	}	
	$mysql_ini_array=parse_ini_file($latkMysqlConf);
	$db_host=$mysql_ini_array[host];
	$db_user=$mysql_ini_array[user];
	$db_pass=$mysql_ini_array[pass];
	$db_name=$mysql_ini_array[dbName];
        $db = mysql_pconnect($db_host, $db_user, $db_pass); 
	if (!$db) { 
		print "<br> Houston we have a problem! There seems to be an error connecting to the MySQL Database. <br> The error we hit was: " . mysql_error();
		exit; 
	}
        mysql_select_db($db_name, $db);
}

function initializeGeoDat() {
	$GeoDat="GeoLiteCity.dat"; //Location of MaxMind GeoLiteCity DB
	if (!class_exists('Net_GeoIP')) { 
		require_once "Net/GeoIP.php";
	} 
       	//echo "ERROR: Library Net::GeoIP not found, maps will not work.";
	if (file_exists($GeoDat)) { 
       		$geoip = Net_GeoIP::getInstance($GeoDat);
	} else {
        	echo "ERROR: GeoIP Data file not found. File: $GeoDat";
        	exit;
	}
	return $geoip;
}

// If you are not running this on your server root, add your directory to the end of the baseurl argument below. 
// i.e. http://127.0.0.1/ then leave it alone, but if you are using http://127.0.0.1/latk/ then add the directory to the end. 
// The reason we have to set this is because of open-flash-charts click function

if (isset($_SERVER['SERVER_PORT']))  {
	if ($_SERVER['SERVER_PORT'] != "80" ) {
       		$baseurl = "http://" . $_SERVER['SERVER_NAME'] . ":" . $_SERVER['SERVER_PORT'] . "/latk";      
	} else {
       		$baseurl = "http://" . $_SERVER['SERVER_NAME'] . "/latk";
	}
}

function getPage() { //Get the current php script name
	$currentFile = $_SERVER["PHP_SELF"];
	$parts = Explode('/', $currentFile);
	return $parts[count($parts) - 1];
}

function getRef() {  //Get the referer
	$currentFile = $_SERVER["HTTP_REFERER"];
	$parts = Explode('/', $currentFile);
	return $parts[count($parts) - 1];
}

function getMapPage() { //Find out OS, if it's Linux. then use PHPGeoIP, if its other try PECL
	if (PHP_OS == 'Linux') { 
		return 'map-phpgeo.php';
	} else { 
		return 'map-pecl.php';
	}
}


function addCollection($db, $collectionName, $collectionDesc) { 
	$query="INSERT INTO collections (id, name, description) VALUES('', '$collectionName', '$collectionDesc')"; 
	mysql_query($query, $db);
	return mysql_insert_id();
}

function addDataSource($db, $dataSourceName, $dataSourceDesc, $dataSourceType, $collection_id) { 
	$query="INSERT INTO datasources (id, name, description, type, collection_id) VALUES('', '$dataSourceName', '$dataSourceDesc', '$dataSourceType', '$collection_id')"; 
	mysql_query($query, $db);
	return mysql_insert_id();
}


function checkSubmitJobs() { //determine if we can upload from the web page. 
	if(PHP_OS == 'Linux') { 
		$submitJobs='y';
	} else { 
		$submitJobs='n'; 
	}
	return $submitJobs;
}

function getDataSourceType($db, $d) { //Get The data source type. 
	$query="SELECT type from datasources where id=$d";
	$result=mysql_query($query, $db);
	while($row=mysql_fetch_row($result)) {	
		$dataSourceType=$row[0];
	}
	return $dataSourceType; 	
}


function getCollections($db) { //get a list of Collections 
	$collections=array();
	$query="SELECT id, name, description from collections";
	$result=mysql_query($query, $db);
	while($row=mysql_fetch_row($result)) {	
		$collections[]=(array($row[0], $row[1], $row[2]));
	}
	return $collections;
}
	
function getDataSources($db, $c) { //get a list of Collections 
	$dataSources=array();
	$query="select id, name, description, type from datasources where collection_id=$c";
	$result=mysql_query($query, $db);
	while($row=mysql_fetch_row($result)) {	
		$dataSources[]=(array($row[0], $row[1], $row[2], $row[3]));
	}
	return $dataSources;
}
	
function icheck($i) { //Check that a field is numeric
        if ($i != null) {
        	if(!is_numeric($i)) {
                	print "<b> ERROR: </b> does not compute.  ";
                	exit;
		}
        }
}


function ipcheck($ip) { //check for an IP address
	if ($ip != null) { 
		  $ip=trim($ip);
 		  if(!preg_match("/^([1-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])" .  "(\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])){3}$/", $ip)) {
			print "<b> ERROR: </b> does not compute.  ";
                        exit;
		} else { 
			return $ip;
		}
		
	}
}
function isIP($ip) { //just return 0 or 1 
	$ip=trim($ip);
        if (preg_match(':(\.\.|^/|\:|\;|\"|\'):', $ip)) {
            exit;
        };
	if(!preg_match("/^([1-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])" .  "(\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])){3}$/", $ip)) {
		return 0;
	} else { 
		return 1;
	}
}	

function printBeaconResult($d, $c, $ip, $db) { 
	if($ip == null) { 
		$query="SELECT clientip, destip, count, mean, stdDev, beaconScore FROM beaconData where beaconScore >= 2 and datasource_id=$d ORDER BY beaconScore DESC, stdDev ASC";
	} else { 
		$query="SELECT clientip, destip, count, mean, stdDev, beaconScore FROM beaconData where datasource_id=$d and (clientIP='$ip'  or destIP='$ip' ) ORDER BY beaconScore DESC, stdDev ASC";
	}
	echo "<center>
		<b> <u> Beacon Behaviour Analysis </b</u> </br>  
		<table>
		<tr>
		<td> Client IP </td>
		<td> Destination </td>
		<td> Hits </td>
		<td> Avg Interval </td>
		<td> Std Dev </td>
		<td> Score </td>
		<td> Probability </td>
		</tr>";

	$result=mysql_query($query, $db);
	while($row=mysql_fetch_row($result)) {	
                if ( $row[5] >= 6 ) { 
                        $beaconProbability="High";
                } else if ($row[5] >= 3) {       
                        $beaconProbability="Medium";
                } else { 
                        $beaconProbability="Low";
		}

		print "<tr> <td> <a href=index.php?i=40&d=$d&c=$c&ip=$row[0]> $row[0] </a></td> 
			 <td> <a href=index.php?i=40&d=$d&c=$c&ip=$row[1]>$row[1] </a></td> 
			 <td> $row[2] </td> 
			 <td> $row[3] </td> 
			 <td> $row[4] </td> 
			 <td> $row[5] </td> 
			 <td> $beaconProbability </td>  </tr> \n";

	}
	print "</table>";
}

function pageSearchResults($d, $c, $dataSourceType, $db, $word) {
	$uword=htmlspecialchars($word); //display safe
	$myword=mysql_real_escape_string($word); //query safe
	if ($dataSourceType == "squid" || $dataSourceType == "bluecoat") {
		$query="select distinct(clientip), count(time) as pageCount, from_unixtime(min(time), '%Y-%m-%d %H:%i'), from_unixtime(max(time), '%Y-%m-%d %H:%i'), sum(bytesIn + bytesOut) from proxyData where datasource_id=$d and (page like '%$myword%' or destip like '%$myword%') group by clientip  order by pageCount desc";
	} else {
		$query="select distinct(clientip), count(page) as pageCount, from_unixtime(min(time), '%Y-%m-%d %H:%i'), from_unixtime(max(time), '%Y-%m-%d %H:%i'), sum(bytesIn + bytesOut) from webData where datasource_id=$d and page like '%$myword%' group by clientip  order by pageCount desc";
	}
	$title="Custom Page Search Results for $uword";
	echo "<center> <b><u> $title </b</u>
                <table width=50%>
                 <tr> 
                        <td id=\"main\" bgcolor=#4682B4> Client IP </td>
                        <td id=\"main\" bgcolor=#4682B4> Hit Count </td>
                        <td id=\"main\" bgcolor=#4682B4> First Accessed </td>
                        <td id=\"main\" bgcolor=#4682B4> Last Accessed </td>
			<td id=\"main\" bgcolor=#4682B4> Bytes </td>";
		
	$pageCount=0;
	$result=mysql_query($query, $db);
	while($row=mysql_fetch_row($result)) {	
		print "<tr> <td id=\"main\"> <a href=index.php?i=40&d=$d&c=$c&ip=$row[0]>$row[0]</a> </td>
			<td id=\"main\" > $row[1] </td> 
			<td id=\"main\" > $row[2] </td>
			<td id=\"main\" > $row[3] </td> 
			<td id=\"main\" > $row[4] </td>
			</tr>";
		}
		$sqliCount++;
	if ( $sqliCount == 0 )  { 
		print "<tr> <td colspan=6> No Matches Found </td> </tr> "; 
	}
}
	
function sqliTable($d, $c, $ip, $db) {           
	$title="SQLi Indicators";
	echo "<center> <b><u> $title </b</u>
                <table>
                 <tr>
                        <td id=\"main\" bgcolor=#4682B4> Client IP </td>
                        <td id=\"main\" bgcolor=#4682B4> Query </td>
                        <td id=\"main\" bgcolor=#4682B4> Type </td>
	</tr>";
	if (!$ip) {
		$query="select clientIP, query, xsstype from xssData where datasource_id='$d'";
	} else { 
		$query="select clientIP, query, xsstype from xssData where clientIP='$ip' and datasource_id='$d'";
	}
		
	$sqliCount=0;
	$result=mysql_query($query, $db);
	while($row=mysql_fetch_row($result)) {	
		$xss=htmlspecialchars($row[1]); 
		$xss=wordwrap($xss, 80, "<br> \n", true);
		print "<tr> <td id=\"main\"> <a href=index.php?i=40&d=$d&c=$c&ip=$row[0]>$row[0]</a> </td> <td id=\"main\" > $xss </td> <td id=\"main\" > $row[2] </td> </tr>"; 
		$sqliCount++;
	}
	if ( $sqliCount == 0 )  { 
		print "<tr> <td colspan=3> No Indiciators Found </td> </tr> "; 
	}
         echo "</table>";
}

function suspicionIndex($d, $c, $type, $db) { 
	$title="Index of Suspicion ";
	$records=array();
	echo "<center> <b><u> $title </b</u>";
	if ($type == "squid" || $type == "bluecoat") { 
               echo" <table width=75%>
                 <tr>
                        <td id=\"main\" bgcolor=#4682B4> Client IP </td>
                        <td id=\"main\" bgcolor=#4682B4> % of Total IPs </td>
                        <td id=\"main\" bgcolor=#4682B4> % of Total Bytes </td>
                        <td id=\"main\" bgcolor=#4682B4> % of Total Beacon </td>
                        <td id=\"main\" bgcolor=#4682B4> Suspicion Score </td>
		</tr>";
		$query="select count(distinct(destip)) as ipCount , sum(bytesIn + bytesOut) as bytesTotal, (select sum(beaconScore) from beaconData where datasource_id=$d) as beaconTotal from proxyData where datasource_id=$d";
		$result=mysql_query($query, $db);
		while($row=mysql_fetch_row($result)) {	
                        $totalDests=$row[0];
                        $totalBytes=$row[1];
                        $totalBeacons=$row[2];
		}

		$query="select clientip, count(distinct(destip)) as ipCount , sum(bytesIn + bytesOut) as bytesTotal, (select sum(beaconScore) from beaconData where beaconData.clientip=proxyData.clientip) as beaconTotal from proxyData where datasource_id=$d group by clientIP limit 200";
		$result=mysql_query($query, $db);
		while($row=mysql_fetch_row($result)) {	
                        $clientIP=$row[0];
                        $ipScore=round(($row[1]/$totalDests*100),2);
                        $bytesScore=round(($row[2]/$totalBytes*100),2);
                        if ($row[3] == "") {
                                $beaconScore=0;
                        } else { 
                                $beaconScore=round(($row[3]/$totalBeacons*100),2);
			}
	                $suspicionScore=round(($ipScore + $bytesScore + $beaconScore),2);
			$records[]=array($suspicionScore, $ipScore, $bytesScore, $beaconScore, $clientIP);
		}
	
		array_multisort($records, SORT_DESC);
	
		foreach ($records as $row) {
			print "<tr>
			 <td id=\"main\"> <a href=index.php?i=40&d=$d&c=$c&ip=$row[4]>$row[4]</a></td>
			 <td id=\"main\"> $row[1] </td>
			 <td id=\"main\"> $row[2] </td>
			 <td id=\"main\"> $row[3] </td>
			 <td id=\"main\"> $row[0] </td> </tr>"; 
		}

	} else { 
                echo" <table width=80%>
                 <tr>
                        <td id=\"main\" bgcolor=#4682B4> Client IP </td>
                        <td id=\"main\" bgcolor=#4682B4> %TTL Hits </td>
                        <td id=\"main\" bgcolor=#4682B4> %TTL Bytes </td>
                        <td id=\"main\" bgcolor=#4682B4> %TTL Pages </td>
                        <td id=\"main\" bgcolor=#4682B4> %TTL XSS/SQLi </td>
                        <td id=\"main\" bgcolor=#4682B4> Suspicion Score </td>
			</tr>";
		$query="select count(page), count(distinct(page)), sum(bytesIn + bytesOut), (select count(query) from xssData where datasource_id=$d)  from webData where datasource_id=$d limit 200";
		$result=mysql_query($query, $db);
		while($row=mysql_fetch_row($result)) {	
                        $totalHits=$row[0];
                        $totalPages=$row[1];
                        $totalBytes=$row[2];
                        $totalXss=$row[3];
		}
		$query="select clientip, count(page), count(distinct(page)), sum(bytesIn + bytesOut), (select count(query) from xssData where xssData.clientip=webData.clientip and datasource_id=$d)  from webData where datasource_id=$d group by clientIP";
		$result=mysql_query($query, $db);
		while($row=mysql_fetch_row($result)) {	
                        $clientIP=$row[0];
			$hitsScore=round(($row[1]/$totalHits*100),2);
                        $pageScore=round(($row[2]/$totalPages*100),2);
                        if ($row[3] == 0) {
                                $bytesScore=0;
                        } else {
                                $bytesScore=round(($row[3]/$totalBytes*100),2);
			}
                        if ( $row[4] == 0) { 
                                $xssScore=0;
                        } else { 
                                $xssScore=round(($row[4]/$totalXss*100),2);
			}
                        $suspicionScore=round(($hitsScore + $pageScore + $bytesScore + $xssScore),2);
			$records[]=array($suspicionScore, $hitsScore, $pageScore, $bytesScore, $xssScore, $clientIP);
		}
		array_multisort($records, SORT_DESC);

		foreach ($records as $row) {
			print "<tr>
			 <td id=\"main\"> <a href=index.php?i=40&d=$d&c=$c&ip=$row[5]>$row[5]</a> </td>
			 <td id=\"main\"> $row[1] </td>
			 <td id=\"main\"> $row[2] </td>
			 <td id=\"main\"> $row[3] </td>
			 <td id=\"main\"> $row[4]</td>
			 <td id=\"main\"> $row[0] </td> </tr>"; 
		}

	}

	echo "</table>";
}
	  

//Begin Chart Functions
function barchart($result, $title, $xlabel, $ylabel, $target, $type, $steps, $ip, $d, $c) { 
 
                $bytes=array();
                $connections=array();
                $vals=array();
	        $bar = new bar();
       		$bar->set_tooltip("$title");

		if ($ip == null || $target != null)  {  //Check to see if we need an onclick
             		$bar->{'on-click'} = "barclick";
                	$bar->{'on-click-window'} = "_self";
		} 

		if ($type == "trafficByClient") {
			while($row=mysql_fetch_row($result)) {	
       	                 	$client[]=$row[1];
       	                 	$bytes[]=round($row[0]/1024,2);
       	                 	$byte=round($row[0]/1024,2);
       	                 	$tmp= new bar_value("$byte");
       	                 	$tmp->set_tooltip("kB:$byte<br>ip:$row[1]");
       	                	$tmp->{'on-click'} = "barclick('i=$target&ip=$row[1]&d=$d&c=$c')";
       	                	$vals[]=$tmp;
			}
		}
		if ($type == "trafficByTime") {
			while($row=mysql_fetch_row($result)) {	
       	                 	$client[]=$row[1];
       	                 	$bytes[]=round($row[0]/1024,2);
       	                 	$byte=round($row[0]/1024,2);
       	                 	$tmp= new bar_value("$byte");
       	                 	$tmp->set_tooltip("kB:$byte<br>Time:$row[1]");
       	                	$tmp->{'on-click'} = "barclick('i=$target&&d=$d&c=$c')";
       	                	$vals[]=$tmp;
			}
		}
		if ($type == "pagesByClient") {
			while($row=mysql_fetch_row($result)) {	
       	                 	$client[]=$row[1];
       	                 	$bytes[]=$row[0];
       	                 	$pages=$row[0];
       	                 	$tmp= new bar_value("$pages");
       	                 	$tmp->set_tooltip("Pages:$pages<br>ip:$row[1]");
       	                	$tmp->{'on-click'} = "barclick('i=$target&ip=$row[1]&d=$d&c=$c')";
       	                	$vals[]=$tmp;
			}
		}
		if ($type == "trafficByPage") {
			while($row=mysql_fetch_row($result)) {	
				if (strlen($row[1]) >= 10) { 
					$page=substr($row[1], 0, 10) . "...";
       	                 		$client[]=$page;
				} else { 
					$client[]=$row[1]; 
					$page=$row[1];
				}	
				$bytes[]=round($row[0]/1024,2);
				$byte=round($row[0]/1024,2);
				$tmp= new bar_value("$byte");
       	                 	$tmp->set_tooltip("kB:$byte<br>Page:$row[1]");
       	                	$tmp->{'on-click'} = "barclick('i=$target&ip=$page&d=$d&c=$c')";
       	                	$vals[]=$tmp;
			}
		}
		if ($type == "trafficByPageByIP") {
			while($row=mysql_fetch_row($result)) {	
				if (strlen($row[1]) >= 10) { 
					$page=substr($row[1], 0, 10) . "...";
       	                 		$client[]=$page;
				} else { 
					$client[]=$row[1]; 
					$page=$row[1];
				}	
				$bytes[]=round($row[0]/1024,2);
				$byte=round($row[0]/1024,2);
				$tmp= new bar_value("$byte");
       	                 	$tmp->set_tooltip("kB:$byte<br>Page:$row[1]");
       	                	$tmp->{'on-click'} = "barclick('i=$target&d=$d&c=$c')";
       	                	$vals[]=$tmp;
			}
		}



                $max=max($bytes);
                $bar->set_values($vals);

                $chart = new open_flash_chart();
                $chart->set_title( new title("$title") );
                $chart->add_element( $bar );
                $chart->set_bg_colour( '#FFFFFF' );
                $bar->set_on_show(new bar_on_show('grow-up',1,0));

                $x = new x_axis();
                $x->grid_colour('#FFFFFF');
                $x_labels = new x_axis_labels();
                $x_labels->rotate(-45);
                $x_labels->set_colour( 'black' );
                $x_labels->set_size( 12 );
                // set the label text
                $x_labels->set_labels($client);
                $x->set_labels( $x_labels );
                $chart->set_x_axis( $x );
		if ($steps != null) {
			$x_labels->set_steps($steps);
                	$x_labels->visible_steps($steps);
		}


                $y = new y_axis();
                $y->set_grid_colour('#FFFFFF');
                $x_labels = new x_axis_labels();
                $y->set_range( 0, $max, round(($max/10),0));
                $chart->set_y_axis($y);

                $x_legend = new x_legend( "$xlabel" );
                $x_legend->set_style( '{font-size: 14px; color: #778877}' );
                $chart->set_x_legend( $x_legend );

                $y_legend = new y_legend( "$ylabel" );
                $y_legend->set_style( '{font-size: 14px; color: #778877}' );
                $chart->set_y_legend( $y_legend );

                echo $chart->toPrettyString();
}


?>
