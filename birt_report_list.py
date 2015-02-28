#!/usr/bin/python
#coding:utf-8;
import os;

#set directory
directory=[{"个险报表":['gx','infor','weitou']},{"银保报表":['bnk','yb','labor']},{"综合报表":['all_p','all_d']},{"内勤报表":['_nq_','AAA']},{"信息技术部":['machine']}]

# write into html file.
fp = open('/opt/tomcat/webapps/birt/birt_table_list.html','w')
html_start="""
<html>
        <title>birt_table_list</title>
        <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <style type="text/css">
                #container{ 
                        width:960px; 
                        height:800px; 
                        margin:20px auto; 
                } 
                *{ 
                        margin:0;
                        padding:0;
                }
                ul{
                     overflow:auto;
                     list-style-type:none;
                }
                li{
                     height:25px;
                     float:left;
                     margin-right:0px;
                     border-right:1pxsolid#aaa;
                     padding:020px;
                     font-weight: bold;
                }
                li:last-child{
                     border-right:none;
                }
                li a{
                     text-decoration:none;
                     color:block;
                     font:25px/1Helvetica,Verdana,sans-serif;
                     text-transform:uppercase;
                     -webkit-transition:all0.5sease;
                     -moz-transition:all0.5sease;
                     -o-transition:all0.5sease;
                     -ms-transition:all0.5sease;
                     transition:all0.5sease;
                }
                li a:hover{
                     color:green;
                }
                li.activea{
                     font-weight:bold;
                     color:#333;
                }
                em{
                        font-size:6px;
                        color:#8DB6CD;
                }
        </style>
        </head>

        <body>
                <div id="container">
"""

fp.write(html_start)
for key_value in directory:
        for key,values in key_value.items():
                fp.write('<h1>'+key+'</h1><ul>')
                for value in values:
                        command="grep {select} </home/tomcat/reports_count"
                        exec_com=command.format(select=value,)
                        list = os.popen(exec_com)
                        list = list.read()
                        list = list.split()

                        for report in list:
                                report = report.split('##')
                                fp.write("\t\t<li><a href='frameset?__report=report/"+report[0]+".rptdesign',target='_blank'>"+report[1]+"<em>访问量:"+report[2]+"</em></a></li>\n")
                fp.write("</ul>\n")

html_end="""
                </div>
        </body>
</html>
"""
fp.write(html_end)
