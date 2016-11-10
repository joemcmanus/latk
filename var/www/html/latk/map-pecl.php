<?php
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


include_once('latklib.php');
$geoip=initializeGeoDat();
connect($db);
$ip=mysql_real_escape_string($ip);
if ($d != '') { 
        $dataSourceType=getDataSourceType($db, $d) ;
} 


echo "
<html>
<head>
<title>DINO GEO IP $ip</title> 
<meta name=\"viewport\" content=\"initial-scale=1.0, user-scalable=no\" />
<style type=\"text/css\">
  html { height: 100% }
  body { height: 100%; margin: 0; padding: 0 }
  #map_canvas { height: 100% }
</style>
<script type=\"text/javascript\"
    src=\"http://maps.googleapis.com/maps/api/js?sensor=false\">
</script>
<script type=\"text/javascript\">
  function initialize() {\n";
		$i=0;
		$oldLat=0;
		if ($ip == Null ) {
			if ($dataSourceType == "squid" || $dataSourceType == "bluecoat") {
				$query="select distinct(destip), (bytesIn + bytesOut) as totalBytes from proxyData where (destip not like '192.168.1.%' and destip != '0.0.0.0' and destip not like '10.%' and destip not like '172.16.%') and datasource_id=$d group by destip order by totalBytes Desc limit 100"; 
			} else { 
				$query="select distinct(clientip), (bytesIn + bytesOut) as totalBytes from webData where (clientip not like '192.168.1.%' and clientip != '0.0.0.0' and clientip not like '10.%' and clientip not like '172.16.%') and datasource_id=$d group by clientip order by totalBytes Desc limit 500"; 
			}	
			$result=mysql_query($query, $db);
		        while($row=mysql_fetch_row($result)) {
				if (isIP($row[0])) { 
					$location=$geoip->lookupLocation($row[0]);
                                } else { 
					$location=$geoip->lookupLocation(gethostbyname($row[0]));
                                }
				
				$lat=$location->latitude;
				$long=$location->longitude;
				if ($lat != Null ) { 
					$kbytes[]=$row[1];
					$client[]=$row[0];
					$country[]=$location->countryName;
					$city[]=$location->city;
					$region[]=$location->region;
					echo "var ip$i = new google.maps.LatLng($lat, $long);\n";
					$i++;
				}
			}
			$zoom=2;
			$width="100%";
			$height="100%";
		} else {
			$location=$geoip->lookupLocation($ip);
			$lat=$location->latitude;
			$long=$location->longitude;
			$zoom=2;
			$width="400px";
			$height="320px";
			$client[]=$ip;
			$kbytes[]='';
			$country[]=$location->countryName;
			$city[]=$location->city;
			$region[]=$location->region;
		}

	if ($ip != Null ) {
		$ipX=("$lat, $long");
	} else { 
		$ipX='18,-34';
	}
    echo "
    var ipX= new google.maps.LatLng($ipX);

    var myOptions = {
      zoom: $zoom,
      center: ipX,
      mapTypeId: google.maps.MapTypeId.ROADMAP
    };

    var map = new google.maps.Map(document.getElementById(\"map_canvas\"), myOptions); \n";

  $j=0;
  while ($j < $i) {
	echo " 

	var marker$j = new google.maps.Marker({
     	position: ip$j,
	map: map, 
	title:\"IP: $client[$j]  Kb: $kbytes[$j]\"
	});   

	var contentString$j = '<div id=\"content\"> IP: $client[$j] <br> Kb: $kbytes[$j] <br> Country: $country[$j] <br> Region: $region[$j] <br> City: $city[$j] <br> <a href=index.php?i=40&d=$d&ip=$client[$j] target=\"_top\">More Info...</a> </div>' ;
	var infowindow$j = new google.maps.InfoWindow({ content: contentString$j });

	google.maps.event.addListener(marker$j, 'click', function() { infowindow$j.open(map, marker$j);});
	";
	$j++;
}

echo "
}
 

</script>
</head>
<body onload=\"initialize()\">
  <div id=\"map_canvas\" style=\"width:$width; height:$height\"></div>
</body>
</html>";

?>
