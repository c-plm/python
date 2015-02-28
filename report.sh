#!/bin/sh
awk -F "##" '/2015/{a[$1]++}END{for (i in a) print i,a[i]}' /home/tomcat/visitation.txt >/home/tomcat/count
sed 's/   /##/g' count >count.bak
rm count
awk -F"##"  'NR==FNR{a[$1]=$2;}NR!=FNR && a[$1]{print $1,$2,a[$1]}' count.bak report_list>reports_count.bak
sed 's/ /##/g' reports_count.bak >reports_count
rm reports_count.bak
rm count.bak
