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


include("latklib.php");

include 'open-flash/php-ofc-library/open-flash-chart.php';
connect($db);

switch($i) { 
        case "0": //Clients by bytes
                $query="select sum(bytesOut) + sum(bytesIn) as bytes, clientIP FROM webData WHERE datasource_id='$d' GROUP BY clientip ORDER BY bytes DESC LIMIT 20";
		$result=mysql_query($query, $db);

                $title="Top Clients by Total Bytes ";
                $xlabel ='IP Address';
                $ylabel ='Traffic in kB';
                $target=40;
		$type="trafficByClient";
		$steps="";
		barchart($result, $title, $xlabel, $ylabel, $target , $type, $steps, $ip, $d, $c);
        break;	
	case "1": //Clients by pages
		if (!$ip) { 
                	$query="select count(page) as totalPages, clientIP from webData where datasource_id='$d' group by clientip order by totalPages Desc limit 40";
                	$title="Top Clients by Pages ";
		} else { 
			$title="Top Pages access by $ip";
                	$query="select count(page) as totalPages, page from webData where datasource_id='$d' and clientip='$ip' group by page order by totalPages Desc limit 40";
		}
		$result=mysql_query($query, $db);

		$target=40;
                $xlabel ='IP Address';
                $ylabel ='Pages';
		$type="pagesByClient";
		$steps="";
		barchart($result, $title, $xlabel, $ylabel, $target , $type, $steps, $ip, $d, $c);
	break;
	case "2": //Pages by bytes
                $query="select sum(bytesOut) + sum(bytesIn) as totalBytes, page FROM webData WHERE datasource_id='$d' GROUP BY page ORDER BY totalBytes DESC LIMIT 20";
		$result=mysql_query($query, $db);

                $title="Top Pages by Bytes ";
                $xlabel ='IP Address';
                $ylabel ='Bytes';
                $target="";
		$type="trafficByPage";
		$steps="";
		barchart($result, $title, $xlabel, $ylabel, $target , $type, $steps, $ip, $d, $c);
	break;

	case "5": //Proxy Client by bytes
		$dataSourceType=getDataSourceType($db, $d);
		if ($dataSourceType == "bluecoat") {  
                	$query="select sum(bytesIn) as totalBytes, clientIP FROM proxyData WHERE datasource_id='$d' GROUP BY clientIP ORDER BY totalBytes DESC LIMIT 50";
		} elseif ($dataSourceType == "squid") {
                	$query="select sum(bytesOut) as totalBytes, clientIP FROM proxyData WHERE datasource_id='$d' GROUP BY clientIP ORDER BY totalBytes DESC LIMIT 50";
		}

		$result=mysql_query($query, $db);
                $title="Top Clients by Bytes In ";
                $xlabel ='IP Address';
                $ylabel ='Bytes';
                $target=40;
		$type="trafficByClient";
		$steps="";
		barchart($result, $title, $xlabel, $ylabel, $target , $type, $steps, $ip, $d, $c);
	break;

	case "6": //Proxy Client by bytes
		$dataSourceType=getDataSourceType($db, $d);
		if ($dataSourceType == "bluecoat") {  
                	$query="select sum(bytesOut) as totalBytes, clientIP FROM proxyData WHERE datasource_id='$d' GROUP BY clientIP ORDER BY totalBytes DESC LIMIT 50";
		} elseif ($dataSourceType == "squid") {
                	$query="select sum(bytesIn) as totalBytes, clientIP FROM proxyData WHERE datasource_id='$d' GROUP BY clientIP ORDER BY totalBytes DESC LIMIT 50";
		}

		$result=mysql_query($query, $db);
                $title="Top Clients by Bytes Out ";
                $xlabel ='IP Address';
                $ylabel ='Bytes';
                $target=40;
		$type="trafficByClient";
		$steps="";
		barchart($result, $title, $xlabel, $ylabel, $target , $type, $steps, $ip, $d, $c);
	break;

	case "7": //Proxy Client by bytesTotal
		$dataSourceType=getDataSourceType($db, $d);
		if ($dataSourceType == "bluecoat") {  
                	$query="select sum(bytesOut) + sum(BytesIn)  as totalBytes, clientIP FROM proxyData WHERE datasource_id='$d' GROUP BY clientIP ORDER BY totalBytes DESC LIMIT 50";
		} elseif ($dataSourceType == "squid") {
                	$query="select sum(bytesIn) as totalBytes, clientIP FROM proxyData WHERE datasource_id='$d' GROUP BY clientIP ORDER BY totalBytes DESC LIMIT 50";
		}

		$result=mysql_query($query, $db);
                $title="Top Clients by Bytes Total ";
                $xlabel ='IP Address';
                $ylabel ='Bytes';
                $target=40;
		$type="trafficByClient";
		$steps="";
		barchart($result, $title, $xlabel, $ylabel, $target , $type, $steps, $ip, $d, $c);
	break;

	case "8": //Pages by clients
                $query="select COUNT(DISTINCT(destIP)) AS hostCount, clientIP FROM proxyData WHERE datasource_id='$d' GROUP BY clientIP ORDER BY hostCount DESC LIMIT 40";
		$result=mysql_query($query, $db);

                $title="Top Pages by Bytes ";
                $xlabel ='IP Address';
                $ylabel ='Hosts';
                $target=40;
		$type="pagesByClient";
		$steps="";
		barchart($result, $title, $xlabel, $ylabel, $target , $type, $steps, $ip, $d, $c);
	break;
	case "9": //Pages by bytesIn
                $query="select sum(bytesIn) as totalBytes, page FROM webData WHERE datasource_id='$d' GROUP BY page ORDER BY totalBytes DESC LIMIT 20";
		$result=mysql_query($query, $db);

                $title="Top Pages by Bytes Uploaded ";
                $xlabel ='IP Address';
                $ylabel ='Bytes';
                $target="";
		$type="trafficByPage";
		$steps="";
		barchart($result, $title, $xlabel, $ylabel, $target , $type, $steps, $ip, $d, $c);
	break;
	case "10": //Pages by bytesIn
                $query="select sum(bytesOut) as totalBytes, page FROM webData WHERE datasource_id='$d' GROUP BY page ORDER BY totalBytes DESC LIMIT 20";
		$result=mysql_query($query, $db);

                $title="Top Pages by Bytes Downloaded ";
                $xlabel ='IP Address';
                $ylabel ='Bytes';
                $target="";
		$type="trafficByPage";
		$steps="";
		barchart($result, $title, $xlabel, $ylabel, $target , $type, $steps, $ip, $d, $c);
	break;
        case "11": //Clients by bytes Downloaded
                $query="select sum(bytesOut) as bytes, clientIP FROM webData WHERE datasource_id='$d' GROUP BY clientip ORDER BY bytes DESC LIMIT 20";
		$result=mysql_query($query, $db);

                $title="Top Clients by Bytes Downloaded";
                $xlabel ='IP Address';
                $ylabel ='Traffic in kB';
                $target=40;
		$type="trafficByClient";
		$steps="";
		barchart($result, $title, $xlabel, $ylabel, $target , $type, $steps, $ip, $d, $c);
        break;	
        case "12": //Clients by bytes uploaded
                $query="select sum(bytesIn) as bytes, clientIP FROM webData WHERE datasource_id='$d' GROUP BY clientip ORDER BY bytes DESC LIMIT 20";
		$result=mysql_query($query, $db);
                $title="Top Clients by Bytes Uploaded";
                $xlabel ='IP Address';
                $ylabel ='Traffic in kB';
                $target=40;
		$type="trafficByClient";
		$steps="";
		barchart($result, $title, $xlabel, $ylabel, $target , $type, $steps, $ip, $d, $c);
        break;	



}

//Check sub charts for ip report
if ($s != null) { 
	$dataSourceType=getDataSourceType($db, $d);
	if ($dataSourceType == "squid" || $dataSourceType == "bluecoat") { 
		$tableName="proxyData"; 
	} else { 
		$tableName="webData"; 
	}
}

if ($s != null) {
	$dataSourceType=getDataSourceType($db, $d);
	if ($dataSourceType == "bluecoat" || $dataSourceType == "squid") {  
               	$target=7;
	} else { 
		$target=0;
	} 
}
switch($s) {
        case "1": // Bytes In
		if ($dataSourceType == "squid" || $dataSourceType == "bluecoat") {
                	$query="select sum(bytesIn), from_unixtime(time, '%Y-%m-%d %H') as hour from $tableName where datasource_id='$d' and (clientIP='$ip' or destIP='$ip') group by hour limit 25";
		} else { 
                	$query="select sum(bytesIn), from_unixtime(time, '%Y-%m-%d %H') as hour from $tableName where datasource_id='$d' and clientIP='$ip' group by hour limit 25";
		}
		$result=mysql_query($query, $db);
                $title="Bytes Inbound from $ip";
                $xlabel ='Date';
                $ylabel ='Traffic in kB';
		$type="trafficByTime";
		$steps="1";
		barchart($result, $title, $xlabel, $ylabel, $target , $type, $steps, $ip, $d, $c);
		break;
        case "2": // Bytes Hour
		if ($dataSourceType == "squid" || $dataSourceType == "bluecoat") {
                	$query="select sum(bytesOut), from_unixtime(time, '%Y-%m-%d %H') as hour from $tableName where datasource_id='$d' and (clientIP='$ip' or destIP='$ip') group by hour limit 25";
		} else { 
                	$query="select sum(bytesOut), from_unixtime(time, '%Y-%m-%d %H') as hour from $tableName where datasource_id='$d' and clientIP='$ip' group by hour limit 25";
		}
		$result=mysql_query($query, $db);
                $title="Bytes Outbound to $ip";
                $xlabel ='Date';
                $ylabel ='Traffic in kB';
		$type="trafficByTime";
		$steps="1";
		barchart($result, $title, $xlabel, $ylabel, $target , $type, $steps, $ip, $d, $c);
		break;
        case "3": // Total Bytes 
		if ($dataSourceType == "squid" || $dataSourceType == "bluecoat") {
                	$query="select sum(bytesOut) + sum(bytesIn) as bytes, from_unixtime(time, '%Y-%m-%d %H') as hour FROM $tableName WHERE datasource_id='$d' and (clientIP='$ip' or destIP='$ip') GROUP BY hour LIMIT 25";
		} else {
                	$query="select sum(bytesOut) + sum(bytesIn) as bytes, from_unixtime(time, '%Y-%m-%d %H') as hour FROM $tableName WHERE datasource_id='$d' and clientIP='$ip' GROUP BY hour LIMIT 25";
		}
		$result=mysql_query($query, $db);
                $title="Total Bytes from $ip";
                $xlabel ='Date';
                $ylabel ='Traffic in kB';
		$type="trafficByTime";
		$steps="2";
		barchart($result, $title, $xlabel, $ylabel, $target , $type, $steps, $ip, $d, $c);
		break;
	case "4": //Pages 
		if ($dataSourceType == "squid" || $dataSourceType == "bluecoat") {
			$query= "select sum(bytesOut) + sum(bytesIn) as totalBytes, destip FROM $tableName WHERE datasource_id='$d' and (clientip='$ip' or destIP='$ip') GROUP BY destip ORDER BY totalBytes DESC LIMIT 25";
		} else { 
                	$query="select sum(bytesOut) + sum(bytesIn) as totalBytes, page FROM $tableName WHERE datasource_id='$d' and clientip='$ip' GROUP BY page ORDER BY totalBytes DESC LIMIT 25";
		}
		$result=mysql_query($query, $db);

                $title="Top Sites Visited by Bytes with $ip ";
                $xlabel ='IP Address';
                $ylabel ='Bytes';
		$type="trafficByPageByIP";
		$steps="";
		barchart($result, $title, $xlabel, $ylabel, $target , $type, $steps, $ip, $d, $c);
	break;
}

?>

