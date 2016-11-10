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

include_once("latklib.php");
icheck($i);
icheck($s);
icheck($h);
icheck($d);

$ip=mysql_real_escape_string($ip);
isIP($ip);

connect($db);
if ($d != '') { 
	$dataSourceType=getDataSourceType($db, $d) ;
} 

echo "<html>
 <head>
  <title>
   Log Analysis Tool Kit - LATK
  </title>
 <link rel=\"stylesheet\" type=\"text/css\" href=\"latk.css\" />
	 <script type=\"text/javascript\"><!--//--><![CDATA[//><!--
	 sfHover = function() {
		var sfEls = document.getElementById(\"nav\").getElementsByTagName(\"LI\");
		for (var i=0; i<sfEls.length; i++) {
			sfEls[i].onmouseover=function() {
				this.className+=\" sfhover\";
			}
			sfEls[i].onmouseout=function() {
				this.className=this.className.replace(new RegExp(\" sfhover\\b\"), \"\");
			}
		}
	}
	if (window.attachEvent) window.attachEvent(\"onload\", sfHover);

	//--><!]]></script>
	";

	//Check to see if we are running the ip report and create multiple swf items
	if ($i == 40 ) { 
		//Override default data file
		$datafilebytesIn=urlencode("open-flash.php?i=$i&ip=$ip&s=1&d=$d");
		$datafilebytesOut=urlencode("open-flash.php?i=$i&ip=$ip&s=2&d=$d");
		$datafilebytesTotal=urlencode("open-flash.php?i=$i&ip=$ip&s=3&t=2&d=$d");
		$datafilepages=urlencode("open-flash.php?i=$i&ip=$ip&s=4&d=$d");
		
		echo "
		<script type=\"text/javascript\" src=\"open-flash/js/swfobject.js\"></script>
		<script type=\"text/javascript\">
	 
		swfobject.embedSWF(
		  \"open-flash/open-flash-chart.swf\", \"bytesIn_chart\",
		  \"400\", \"320\", \"9.0.0\", \"open-flash/expressInstall.swf\",
		  {\"data-file\":\"$datafilebytesIn\"} );
	 
		swfobject.embedSWF(
		  \"open-flash/open-flash-chart.swf\", \"bytesOut_chart\",
		  \"400\", \"320\", \"9.0.0\", \"open-flash/expressInstall.swf\",
		  {\"data-file\":\"$datafilebytesOut\"} );
	 
		swfobject.embedSWF(
		  \"open-flash/open-flash-chart.swf\", \"bytesTotal_chart\",
		  \"400\", \"320\", \"9.0.0\", \"open-flash/expressInstall.swf\",
		  {\"data-file\":\"$datafilebytesTotal\"} );
	 
		swfobject.embedSWF(
		  \"open-flash/open-flash-chart.swf\", \"pages_chart\",
		  \"400\", \"320\", \"9.0.0\", \"open-flash/expressInstall.swf\",
		  {\"data-file\":\"$datafilepages\"} );

		function barclick(txt){ 
			window.open(\"$baseurl/index.php?\"+txt, '_self')
		} 

		</script> ";
	} else { 
		$datafile=urlencode("open-flash.php?i=$i&ip=$ip&h=$h&d=$d&c=$c");
		echo "
		<script type=\"text/javascript\" src=\"open-flash/js/swfobject.js\"></script>
		<script type=\"text/javascript\">
		swfobject.embedSWF(
			\"open-flash/open-flash-chart.swf\", 
			\"my_chart\",
			\"800\", \"640\", \"9.0.0\", 
			\"open-flash/expressInstall.swf\", 
			{\"data-file\":\"$datafile\"} );

			function barclick(txt){ 
			    window.open(\"$baseurl/index.php?\"+txt, '_self')
			} 
		</script>";
	}

	echo "
	 </head>
	<body>
	

	<table width=100%>
	 <tr>
	  <td id=\"banner\"> <a href=index.php><img src=latk-banner.png></a></td>
	  <td id=\"menu\"> 
		<ul id=\"nav\">
		<li> Collections 
			<ul>\n";
		$collections=getCollections($db);
		foreach ($collections as $x) { 
			print "<li><a href=index.php?i=0&c=$x[0]> $x[2] </a> 
				<ul>\n ";
			$dataSources=getDataSources($db, $x[0]); 
			foreach ($dataSources as $y) { 
				if ($y[3] == "squid" || $y[3] == "bluecoat") {
					$action="7";
				} else { 
					$action="0";
				}	
				print "<li><a href=index.php?i=$action&c=$x[0]&d=$y[0]>-$y[2]</a> </li>\n ";
			}
			print "</ul></li>\n";
		}
	echo "<li><a href=index.php?i=50> Add Collections </a> </li>
	      <li><a href=index.php?i=52> Add Data Sources </a> <li>
	    </ul>
            </li>"; 

	// Check to see if we display the web logs menu
	if ($d == Null || $dataSourceType == "squid" || $dataSourceType == "bluecoat" ) { 
		echo "  <li><strike>Web Logs</strike> </li>";
	} elseif  ( $dataSourceType == "apache" || $dataSourceType == "iis" || $dataSourceType == "iis-short") { 
		echo " 
		<li>Web Logs
		<ul>
			<li> <a href=index.php?i=0&d=$d&c=$c>Top Clients by Bytes(total)</a></li>
			<li> <a href=index.php?i=1&d=$d&c=$c>Top Clients by Pages</a></li>
			<li> <a href=index.php?i=2&d=$d&c=$c>Top Pages by Bytes</a></li>
			<li> <a href=index.php?i=9&d=$d&c=$c>Top Pages by Bytes Inbound</a></li>
			<li> <a href=index.php?i=10&d=$d&c=$c>Top Pages by Bytes Outbound</a></li>
			<li> <a href=index.php?i=11&d=$d&c=$c>Top Clients by Bytes Downloaded</a></li>
			<li> <a href=index.php?i=12&d=$d&c=$c>Top Clients by Bytes Uploaded</a></li>
			<li> <a href=index.php?i=3&d=$d&c=$c>SQLi Report</a></li>
			<li> <a href=index.php?i=4&d=$d&c=$c>Custom Search</a></li>
			<li> <a href=index.php?i=16&d=$d&c=$c>IP Map</a></li>
			<li> <a href=index.php?i=49&d=$d&c=$c>Generate Index of Suspicion</a></li>
		</ul> </li>";
	} 

	//Check to see if we display the proxy logs menu
	if ($d == Null ||  $dataSourceType == "apache" || $dataSourceType == "iis" || $dataSourceType == "iis-short") {
		echo "  <li><strike>Proxy Logs</strike> </li>";
	} elseif ($dataSourceType == "squid" || $dataSourceType == "bluecoat") { 
		echo " 
		<li> Proxy Logs
		<ul>
			<li> <a href=index.php?i=5&d=$d&c=$c>Top Clients by Bytes In </a></li>
			<li> <a href=index.php?i=6&d=$d&c=$c>Top Clients by Bytes Out </a></li>
			<li> <a href=index.php?i=7&d=$d&c=$c>Top Clients by Bytes Total </a></li>
			<li> <a href=index.php?i=8&d=$d&c=$c>Top Clients by Unique Hosts </a></li>
			<li> <a href=index.php?i=15&d=$d&c=$c>Beacon Analysis </a></li>
			<li> <a href=index.php?i=4&d=$d&c=$c>Custom Search</a></li>
			<li> <a href=index.php?i=16&d=$d&c=$c>IP Map</a></li>
			<li> <a href=index.php?i=49&d=$d&c=$c>Generate Index of Suspicion</a></li>
		</ul></li>
		";
	}
	echo " 
		</ul>
		
	  </td>
  	 </tr>
	 <tr>
	  <td id=\"main\" colspan=2>

	";
	
	if ($d != null || $i >= 50) { 	
		switch($i) { 
			default: 
				echo "<p> Please Select a Collection from the menu. </p>";
			break;
			case "0": 
				if( $dataSourceType == "apache" || $dataSourceType == "iis" || $dataSourceType == "iis-short") {
					echo " <div id=\"my_chart\"></div>";
				} else { 
					echo " <p> Sorry, $dataSourceType logs are not web server logs. </p> ";
				}
			break;
			case "1": 
				if( $dataSourceType == "apache" || $dataSourceType == "iis" || $dataSourceType == "iis-short") {
					echo " <div id=\"my_chart\"></div>";
				} else { 
					echo " <p> Sorry, $dataSourceType logs are not web server logs. </p> ";
				}
			break;
	
			case "2": 
				if( $dataSourceType == "apache" || $dataSourceType == "iis" || $dataSourceType == "iis-short") {
					echo " <div id=\"my_chart\"></div>";
				} else { 
					echo " <p> Sorry, $dataSourceType logs are not web server logs. </p> ";
				}
			break;
			
			case "3": 
				sqliTable($d, $c, $ip, $db);
			break;
			
			case "4" ;
				echo "<center>
				<form method=post action=index.php?i=40>
				<fieldset>
				<legend>Custom Report | IP Address </legend> 
				<p><label for \"ip\"> IP Address </label> <input type=\"text\" id=\"ip\" name=\"ip\"></p>
				 <input type=hidden name=c value=\"$c\"></input> 
				 <input type=hidden name=d value=\"$d\"></input>
				<p class=\"submit\"><input type=\"submit\" value=\"Submit\" /></p>
				</fieldset>
				</form>

				<form method=post action=index.php?i=41>
				<fieldset>
				<legend>Custom Report | Query</legend> 
				<p><label for \"word\"> String in URL </label> <input type=\"text\" id=\"word\" name=\"word\"></p>
				 <input type=hidden name=c value=\"$c\"></input> 
				 <input type=hidden name=d value=\"$d\"></input>
				<p class=\"submit\"><input type=\"submit\" value=\"Submit\" /></p>
				</fieldset>
				</form> ";
			break;
	
			case "5": 
				if ($dataSourceType == "bluecoat") { 
					echo " <div id=\"my_chart\"></div>";
				} else if( $dataSourceType == "squid" ) { 
					echo " <p> Sorry, $dataSourceType logs do not split out incoming and outgoing traffic.<br> ";
				} else { 
					echo " <p> Sorry, $dataSourceType logs are not proxy logs. </p> ";
				}
			break;

			case "6": 
				if ($dataSourceType == "bluecoat") { 
					echo " <div id=\"my_chart\"></div>";
				} else if( $dataSourceType == "squid" ) { 
					echo " <p> Sorry, $dataSourceType logs do not split out incoming and outgoing traffic.<br> ";
				} else { 
					echo " <p> Sorry, $dataSourceType logs are not proxy logs. </p> ";
				}
			break;

			case "7": 
				if( $dataSourceType == "squid" || $dataSourceType == "bluecoat") {
					echo " <div id=\"my_chart\"></div>";
				} else { 
					echo " <p> Sorry, $dataSourceType logs are not proxy logs. </p> ";
				}
			break;

			case "8":
				if( $dataSourceType == "squid" || $dataSourceType == "bluecoat") {
					echo " <div id=\"my_chart\"></div>";
				} else { 
					echo " <p> Sorry, $dataSourceType logs are not proxy logs. </p> ";
				}
			break;

			case "9":
				if($dataSourceType == "iis") {
					echo " <div id=\"my_chart\"></div>";
				} else { 
					echo " <p> Sorry, $dataSourceType logs will not work with this report</p> ";
				}
			break;

			case "10" ;
				if($dataSourceType == "iis") {
					echo " <div id=\"my_chart\"></div>";
				} else { 
					echo " <p> Sorry, $dataSourceType logs will not work with this report</p> ";
				}
			break;

			case "11" ;
				if( $dataSourceType == "apache" || $dataSourceType == "iis" || $dataSourceType == "iis-short") {
					echo " <div id=\"my_chart\"></div>";
				} else { 
					echo " <p> Sorry, $dataSourceType logs are not web server logs. </p> ";
				}
			break;

			case "12" ;
				if($dataSourceType == "iis") {
					echo " <div id=\"my_chart\"></div>";
				} else { 
					echo " <p> Sorry, $dataSourceType logs will not work with this report</p> ";
				}
			break;

			case "13" ;
				if($dataSourceType == "iis") {
					echo " <div id=\"my_chart\"></div>";
				} else { 
					echo " <p> Sorry, $dataSourceType logs will not work with this report</p> ";
				}
			break;

			case "14": 
				echo " <div id=\"my_chart\"></div>";
			break;
			case "15": 
				if($dataSourceType == "bluecoat" || $dataSourceType == "squid") {
					printBeaconResult($d, $c, $ip, $db);
				} else { 
					echo " <p> Sorry, $dataSourceType logs will not work with this report</p> ";
				}
			break;
			case "16":
				$map=getMapPage();
				echo "<iframe src=\"$map?d=$d\" width=\"800\" height=\"800\"></iframe>";
			break;
			case "40" ;
				if (isIP($ip)) { 
					$hostname=gethostbyaddr($ip);
				} else { 
					$hostname=$ip;
				}
				echo "<center><b><u> Report for IP: $ip</b></u> hostname: $hostname </center><br>"; 
				if ($dataSourceType == "iis" || $dataSourceType == "bluecoat") { 
					print " <div id=\"bytesIn_chart\"></div> 
	                        	<div id=\"bytesOut_chart\"></div> <br> ";
				}
				print " 
	                        <div id=\"bytesTotal_chart\"></div>
	                        <div id=\"pages_chart\"></div><br>";
				if ($dataSourceType == "iis" || $dataSourceType == "iis-short" || $dataSourceType == "apache")  {
					sqliTable($d, $c, $ip, $db);
				} else { 
					printBeaconResult($d, $c, $ip, $db);
				}
		 	break;
			case "41" : 
				pageSearchResults($d, $c, $dataSourceType, $db, $word);
			break;
				
			case "49": 
				suspicionIndex($d, $c, $dataSourceType, $db);
			break;
			case "50":
				echo "<center> <b><u> Create a Collection </b></u> <br>
				 <br>  *IMPORTANT* LATK requires you to create a collection, then add data sources to the collection for analysis. <br>
				 As an example, you'd create a collection called \"Web Server Hack 2011/02/01\" And then add data sources like Apache logs <br>
				and proxy logs after the collection has been added. <br>
				 <form method=post action=index.php?i=51>
				<fieldset>
				<legend>Add Collection</legend> 
				<p><label for \"collectionName\"> Collection Name </label> <input type=\"text\" id=\"collectionName\" name=\"collectionName\"></p>
				<p><label for \"collectionDesc\"> Collection Description </label> <input type=\"text\" id=\"collectionDesc\" name=\"collectionDesc\"></p>
				<p class=\"submit\"><input type=\"submit\" value=\"Submit\" /></p>
				</fieldset>
				</form> 
				";
			break; 
			case "51":
				$c=addCollection($db, $collectionName, $collectionDesc);
				print "<center> Added new collection $collectionName. Why not add some <a href=index.php?i=52&c=$c> Data Sources</a> now. ";
			break; 
			case "52":
				echo "<center> <b><u> Add A Data Source to a Collection </b></u> <br>
				 <br>  *IMPORTANT* LATK requires you to create a collection, then add data sources to the collection for analysis. <br>
				 As an example, you'd create a collection called \"Web Server Hack 2011/02/01\" And then add data sources like Apache logs <br>
				and proxy logs after the collection has been added. <br>

				<br> Select a Collection, then add a data source. <br>
				 <form method=post action=index.php?i=53>
				<fieldset>
				<legend>Add Data Source</legend> ";

				if ($c != null) { 
					print "<p><label for \"collectionName\"> Collection</label> <input type=\"text\" id=\"collectionName\" name=\"c\" value=\"$c\"></p>";
				} else { 
					print "<label for \"c\"> Collection </label> 
					<select name=\"c\">
					 <option value=''> Choose...</option>";
					$collections=getCollections($db);
					foreach ($collections as $x) { 
						print "<option value='$x[0]'> $x[2] </option>\n";
					}
					print "</select>";
				}
				print "
				<p><label for \"dataSourceName\"> Data Source Name </label> <input type=\"text\" id=\"dataSourceName\" name=\"dataSourceName\"></p>
				<p><label for \"dataSourceDesc\"> Data Source Description </label> <input type=\"text\" id=\"dataSourceDesc\" name=\"dataSourceDesc\"></p>
				<p><label for \"dataSourceType\"> Data Source Type </label> 
                                        <select name=\"dataSourceType\">
                                         <option value=''> Choose...</option>
                                         <option value='apache'> Apache</option>
                                         <option value='iis'> IIS</option>
                                         <option value='squid'>Squid</option>
                                         <option value='bluecoat'>Bluecoat</option>
				</select>
				<p class=\"submit\"><input type=\"submit\" value=\"Submit\" /></p>
				</fieldset>
				</form> 
				";
			break; 
			case "53":
				if ($c == null) { 
					print "Error: You have to select a Collection, please select one and try again."; 
				} else { 
					$d=addDataSource($db, $dataSourceName, $dataSourceDesc, $dataSourceType, $c);
					print "<center> Added new data source $dataSourceName with ID = $d. ";
				}
				break;

		}
	} else { 
		echo "<p> Please Select a data source from the menu </p>"; 
	}
	echo " 
	    </td>
	   </tr>
	  </table>
	 </body>
	</html>";
	?>
