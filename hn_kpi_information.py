#!/usr/bin/python
#coding:utf-8
import os
import time
import datetime
import pyodbc
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

#设置数据库连接
conn=pyodbc.connect('DRIVER={DB2};SERVER=0.0.0.0;DATABASE=data;UID=user;PWD=pass;charset=utf-8')
cur = conn.cursor()

#设置SQL语句
sql_yj="""
delete from administrator.hn_kpi_information where category='{category_zh}' and series='{series}' and kpi_name='{kpi_name}' and kpi_mon={setMon};
insert into administrator.hn_kpi_information
with
team_kpi_this as(
		select
		branch,
		aracde,
		partnum,
		teamnum,
		{selectFieled} as sum_this
		from table(f.get_gx_team_kpi({thisDateStart},{thisDateEnd},'{category}',{rangeStart},{rangeEnd}))a ),
	      team_kpi_last as(
			      select
			      branch,
			      aracde,
			      partnum,
			      teamnum,
			      {selectFieled} as sum_last
			      from table(f.get_gx_team_kpi({lastDateStart},{lastDateEnd},'{category}',{rangeStart},{rangeEnd}))a )    
	      select 
	      '{category_zh}' as categroy,
	      trim('{series}') as series,
	      trim(f.getbranchname(case when a.branch is null then b.branch else a.branch end)) as branch,
	      trim(administrator.getaracdename(case when a.aracde is null then b.aracde else a.aracde end)) as aracde,
	      case when a.partnum is null 
	      then (select trim(agntname)||'部' from administrator.hn_agntinfo c where c.agntnum=b.partnum)
	      else (select trim(agntname)||'部' from administrator.hn_agntinfo c where c.agntnum=a.partnum) end as partname,
	      case when a.teamnum is null 
	      then (select trim(agntname)||'组' from administrator.hn_agntinfo c where c.agntnum=b.teamnum)
	      else (select trim(agntname)||'组' from administrator.hn_agntinfo c where c.agntnum=a.teamnum) end as teamname,
	      '{kpi_name}'as kpi_name,
{setMon} as mon,
	value(sum_this,0) as this_mon,
	value(sum_last,0) as last_mon,
	current timestamp as currentTime
	from team_kpi_this a full join team_kpi_last b 
	on a.branch=b.branch and a.aracde=b.aracde
	and a.partnum=b.partnum and a.teamnum=b.teamnum
"""

sql_rl="""
delete from administrator.hn_kpi_information where category='{category_zh}' and series = '{series}' and kpi_name ='{kpi_name}' and kpi_mon={setMon};
insert into administrator.hn_kpi_information
	with 
	team_rl_this as(
			select 
			branch,
			aracde,
			partnum,
			teamnum,
			{selectFieled} as this_rl
			from table(f.get_gx_teamname({thisDateStart},{thisDateEnd},'{category}'))a),
	team_rl_last as(
			select 
			branch,
			aracde,
			partnum,
			teamnum,
			{selectFieled} as last_rl
			from table(f.get_gx_teamname({lastDateStart},{lastDateEnd},'{category}'))a)
	select 
	'{category_zh}' as categroy,
	'{series}' as series,
	trim(f.getbranchname(case when a.branch is null then b.branch else a.branch end)) as branch,
	trim(administrator.getaracdename(case when a.aracde is null then b.aracde else a.aracde end)) as aracde,
	case when a.partnum is null 
	then (select trim(agntname)||'部' from administrator.hn_agntinfo c where c.agntnum=b.partnum)
	else (select trim(agntname)||'部' from administrator.hn_agntinfo c where c.agntnum=a.partnum) end as partname,
	case when a.teamnum is null 
	then (select trim(agntname)||'组' from administrator.hn_agntinfo c where c.agntnum=b.teamnum)
	else (select trim(agntname)||'组' from administrator.hn_agntinfo c where c.agntnum=a.teamnum) end as teamname,
	'{kpi_name}'as kpi_name,
{setMon} as mon,
	value(this_rl,0) as this_mon,
	value(last_rl,0) as last_mon,
	current timestamp as currentTime
	from team_rl_this a full join team_rl_last b 
	on a.branch=b.branch and a.aracde=b.aracde
	and a.partnum=b.partnum and a.teamnum=b.teamnum
"""
sql_sum="""
delete from administrator.hn_kpi_information where branch='合计' and kpi_name ='{kpi_name}' ;
insert into administrator.hn_kpi_information
	select 
	category,
	series,
	'合计',
	'',
	'',
	'',
	kpi_name,
	kpi_mon,
	sum(this_mon),
	sum(last_mon),
	processing_time
	from  administrator.hn_kpi_information
	where kpi_name='{kpi_name}'
	group by         
	category,
	series,
	kpi_name,
	kpi_mon,
	processing_time
"""
#主管人力
sql_zg="""
delete from administrator.hn_kpi_information where category='{category_zh}' and series='{series}' and kpi_name='{kpi_name}' and kpi_mon={setMon};
insert into administrator.hn_kpi_information
select 
	'{category_zh}' as categroy,
      	trim('{series}') as series,
      	trim(f.getbranchname(branch)) as branch,
      	trim(administrator.getaracdename(aracde)) as aracde,
      	partname,
	teamname,
	'{kpi_name}',
	{setMon},
	count(case when mon={setMon} then agntnum end),
        count(case when mon={last_setMon} then agntnum end),
	current timestamp as currentTime
        	from administrator.hn_agnt_his
        		where mon in({setMon},{last_setMon})
        		and agtype in('AS','SS','UM','AD') 
                		group by 
                        	branch,
                       	 	aracde,
	                        partname,
       		                teamname
"""
	


########################################################################################################################
#########数据处理
########################################################################################################################

#设置时间
dateStart = int(time.strftime("%Y"))*10000+101
dateEnd   = int(time.strftime("%Y"))*10000+131
lastDateStart = dateStart - 10000
lastDateEnd = dateEnd - 10000
currentDate = int(time.strftime("%Y%m%d"))
lastCurrentDate = currentDate - 10000
setMon = int(time.strftime("%Y"))*100+1
last_setMon=setMon-100
currentHour=int(time.strftime("%H"))
my_hour=19


#设置系列
category = [['YX','营销'],['SZ','收展']]

#循环：循环加工当年1-当前月的数据，数据内容由循环体决定
while(dateStart<=currentDate):
	#如果当前时间晚于9点，则跳出循环
	if(currentHour>=my_hour):
		#当前日期-指定天数
		lastMon=datetime.datetime.now()-datetime.timedelta(days=2)
		dateStart = int(lastMon.strftime("%Y%m"))
		setMon = dateStart
		last_setMon=setMon-100
		dateStart = dateStart*100+1
		dateEnd   = dateStart+30
		lastDateStart = dateStart - 10000
		lastDateEnd = dateEnd - 10000

	#主管人力
	currentSQL=sql_zg.format(
		category_zh='营销',
		series='营业组',
		kpi_name='主管人力',
		setMon=setMon,
		last_setMon=last_setMon
	)
	#执行语句
	for curr_sql in currentSQL.split(";"):
		cur.execute(curr_sql.decode('utf-8'))
	cur.commit()			

	#营销，收展循环
	for m_category in category:
		m_cate=m_category[0]
		m_cate_zh=m_category[1]
		print(m_cate+":"+str(dateStart))		
		#设定SQL语句参数
		currentSQL=sql_yj.format(
			category=m_cate,
			category_zh=m_cate_zh,
			series='营业组',
			kpi_name='规模保费',
			selectFieled='gmbf_range',
			setMon=setMon,
			thisDateStart=dateStart,
			thisDateEnd=dateEnd,
			lastDateStart=lastDateStart,
			lastDateEnd=lastDateEnd,
			rangeStart=-10000000,
			rangeEnd=10000000,
		)
		#执行语句
		for curr_sql in currentSQL.split(";"):
			cur.execute(curr_sql.decode('utf-8'))
		cur.commit()			

		#--------营销标准保费--------------------------------------------------------------------------------
		#设定SQL语句参数
		currentSQL=sql_yj.format(
			category=m_cate,
			category_zh=m_cate_zh,
			series='营业组',
			kpi_name='标准保费',
			selectFieled='bzbf_range',
			setMon=setMon,
			thisDateStart=dateStart,
			thisDateEnd=dateEnd,
			lastDateStart=lastDateStart,
			lastDateEnd=lastDateEnd,
			rangeStart=-10000000,
			rangeEnd=10000000,
		)
		#执行语句
		for curr_sql in currentSQL.split(";"):
			cur.execute(curr_sql.decode('utf-8'))
		cur.commit()			

		#--------营销活动人力--------------------------------------------------------------------------------
		#设定SQL语句参数
		currentSQL=sql_yj.format(
			category=m_cate,
			category_zh=m_cate_zh,
			series='营业组',
			kpi_name='活动人力',
			selectFieled='rl_range',
			setMon=setMon,
			thisDateStart=dateStart,
			thisDateEnd=dateEnd,
			lastDateStart=lastDateStart,
			lastDateEnd=lastDateEnd,
			rangeStart=0,
			rangeEnd=10000000,
		)
		#执行语句
		for curr_sql in currentSQL.split(";"):
			cur.execute(curr_sql.decode('utf-8'))
		cur.commit()			

		#--------营销千P人力--------------------------------------------------------------------------------
		#设定SQL语句参数
		currentSQL=sql_yj.format(
			category=m_cate,
			category_zh=m_cate_zh,
			series='营业组',
			kpi_name='千P人力',
			selectFieled='rl_range',
			setMon=setMon,
			thisDateStart=dateStart,
			thisDateEnd=dateEnd,
			lastDateStart=lastDateStart,
			lastDateEnd=lastDateEnd,
			rangeStart=1000,
			rangeEnd=10000000,
		)
		#执行语句
		for curr_sql in currentSQL.split(";"):
			cur.execute(curr_sql.decode('utf-8'))
		cur.commit()			

		#--------营销3千P人力--------------------------------------------------------------------------------
		#设定SQL语句参数
		currentSQL=sql_yj.format(
			category=m_cate,
			category_zh=m_cate_zh,
			series='营业组',
			kpi_name='3千P人力',
			selectFieled='rl_range',
			setMon=setMon,
			thisDateStart=dateStart,
			thisDateEnd=dateEnd,
			lastDateStart=lastDateStart,
			lastDateEnd=lastDateEnd,
			rangeStart=3000,
			rangeEnd=10000000,
		)
		#执行语句
		for curr_sql in currentSQL.split(";"):
			cur.execute(curr_sql.decode('utf-8'))
		cur.commit()			

		#--------营销万P人力--------------------------------------------------------------------------------
		#设定SQL语句参数
		currentSQL=sql_yj.format(
			category=m_cate,
			category_zh=m_cate_zh,
			series='营业组',
			kpi_name='1万P人力',
			selectFieled='rl_range',
			setMon=setMon,
			thisDateStart=dateStart,
			thisDateEnd=dateEnd,
			lastDateStart=lastDateStart,
			lastDateEnd=lastDateEnd,
			rangeStart=10000,
			rangeEnd=10000000,
		)
		#执行语句
		for curr_sql in currentSQL.split(";"):
			cur.execute(curr_sql.decode('utf-8'))
		cur.commit()			

		#--------营销2万P人力--------------------------------------------------------------------------------
		#设定SQL语句参数
		currentSQL=sql_yj.format(
			category=m_cate,
			category_zh=m_cate_zh,
			series='营业组',
			kpi_name='2万P人力',
			selectFieled='rl_range',
			setMon=setMon,
			thisDateStart=dateStart,
			thisDateEnd=dateEnd,
			lastDateStart=lastDateStart,
			lastDateEnd=lastDateEnd,
			rangeStart=20000,
			rangeEnd=10000000,
		)
		#执行语句
		for curr_sql in currentSQL.split(";"):
			cur.execute(curr_sql.decode('utf-8'))
		cur.commit()			

		#--------营销3万P人力--------------------------------------------------------------------------------
		#设定SQL语句参数
		currentSQL=sql_yj.format(
			category=m_cate,
			category_zh=m_cate_zh,
			series='营业组',
			kpi_name='3万P人力',
			selectFieled='rl_range',
			setMon=setMon,
			thisDateStart=dateStart,
			thisDateEnd=dateEnd,
			lastDateStart=lastDateStart,
			lastDateEnd=lastDateEnd,
			rangeStart=30000,
			rangeEnd=10000000,
		)
		#执行语句
		for curr_sql in currentSQL.split(";"):
			cur.execute(curr_sql.decode('utf-8'))
		cur.commit()			

		#--------营销5万P人力--------------------------------------------------------------------------------
		#设定SQL语句参数
		currentSQL=sql_yj.format(
			category=m_cate,
			category_zh=m_cate_zh,
			series='营业组',
			kpi_name='5万P人力',
			selectFieled='rl_range',
			setMon=setMon,
			thisDateStart=dateStart,
			thisDateEnd=dateEnd,
			lastDateStart=lastDateStart,
			lastDateEnd=lastDateEnd,
			rangeStart=50000,
			rangeEnd=10000000,
		)
		#执行语句
		for curr_sql in currentSQL.split(";"):
			cur.execute(curr_sql.decode('utf-8'))
		cur.commit()			

		#--------营销10万P人力--------------------------------------------------------------------------------
		#设定SQL语句参数
		currentSQL=sql_yj.format(
			category=m_cate,
			category_zh=m_cate_zh,
			series='营业组',
			kpi_name='10万P人力',
			selectFieled='rl_range',
			setMon=setMon,
			thisDateStart=dateStart,
			thisDateEnd=dateEnd,
			lastDateStart=lastDateStart,
			lastDateEnd=lastDateEnd,
			rangeStart=100000,
			rangeEnd=10000000,
		)
		#执行语句
		for curr_sql in currentSQL.split(";"):
			cur.execute(curr_sql.decode('utf-8'))
		cur.commit()			

		#--------营销人力--------------------------------------------------------------------------------
		#设定SQL语句参数
		currentSQL=sql_rl.format(
			category=m_cate,
			category_zh=m_cate_zh,
			series='营业组',
			kpi_name='月初人力',
			selectFieled='rl',
			setMon=setMon,
			thisDateStart=dateStart,
			thisDateEnd=dateStart,
			lastDateStart=lastDateStart,
			lastDateEnd=lastDateStart,
		)
		#执行语句
		for curr_sql in currentSQL.split(";"):
			cur.execute(curr_sql.decode('utf-8'))
		cur.commit()			

	#------------循环体结尾，更改时间变量-------------------------------------------------------------------
	dateStart += 100
	dateEnd   += 100
	lastDateStart += 100
	lastDateEnd   += 100
	setMon += 1  
	last_setMon += 1  
	print("#############################################################################################")
	print(dateStart)
	print(setMon)
	print("#############################################################################################")


print("循环结束，开始加工当日业绩")





#--------当日业绩--------------------------------------------------------------------------------
#删除当日业绩
cur.execute("delete from administrator.hn_kpi_information where length(trim(char(kpi_mon)))=8".decode('utf-8')) 
cur.commit()

for m_category in category:
	m_cate=m_category[0]
	m_cate_zh=m_category[1]
	
	#设定SQL语句参数
	currentSQL=sql_yj.format(
		category=m_cate,
		category_zh=m_cate_zh,
		series='营业组',
		kpi_name='规模保费',
		selectFieled='gmbf_range',
		setMon=currentDate,
		thisDateStart=currentDate,
		thisDateEnd=currentDate,
		lastDateStart=lastCurrentDate,
		lastDateEnd=lastCurrentDate,
		rangeStart=-10000000,
		rangeEnd=10000000,
	)
	#执行语句
	for curr_sql in currentSQL.split(";"):
		cur.execute(curr_sql.decode('utf-8'))
	cur.commit()			
	
	#--------营销标准保费--------------------------------------------------------------------------------
	#设定SQL语句参数
	currentSQL=sql_yj.format(
		category=m_cate,
		category_zh=m_cate_zh,
		series='营业组',
		kpi_name='标准保费',
		selectFieled='bzbf_range',
		setMon=currentDate,
		thisDateStart=currentDate,
		thisDateEnd=currentDate,
		lastDateStart=lastCurrentDate,
		lastDateEnd=lastCurrentDate,
		rangeStart=-10000000,
		rangeEnd=10000000,
	)
	#执行语句
	for curr_sql in currentSQL.split(";"):
		cur.execute(curr_sql.decode('utf-8'))
	cur.commit()			
	
	#--------营销活动人力--------------------------------------------------------------------------------
	#设定SQL语句参数
	currentSQL=sql_yj.format(
		category=m_cate,
		category_zh=m_cate_zh,
		series='营业组',
		kpi_name='活动人力',
		selectFieled='rl_range',
		setMon=currentDate,
		thisDateStart=currentDate,
		thisDateEnd=currentDate,
		lastDateStart=lastCurrentDate,
		lastDateEnd=lastCurrentDate,
		rangeStart=0,
		rangeEnd=10000000,
	)
	#执行语句
	for curr_sql in currentSQL.split(";"):
		cur.execute(curr_sql.decode('utf-8'))
	cur.commit()			
	
	#--------营销千P人力--------------------------------------------------------------------------------
	#设定SQL语句参数
	currentSQL=sql_yj.format(
		category=m_cate,
		category_zh=m_cate_zh,
		series='营业组',
		kpi_name='千P人力',
		selectFieled='rl_range',
		setMon=currentDate,
		thisDateStart=currentDate,
		thisDateEnd=currentDate,
		lastDateStart=lastCurrentDate,
		lastDateEnd=lastCurrentDate,
		rangeStart=1000,
		rangeEnd=10000000,
	)
	#执行语句
	for curr_sql in currentSQL.split(";"):
		cur.execute(curr_sql.decode('utf-8'))
	cur.commit()			
	
	#--------营销3千P人力--------------------------------------------------------------------------------
	#设定SQL语句参数
	currentSQL=sql_yj.format(
		category=m_cate,
		category_zh=m_cate_zh,
		series='营业组',
		kpi_name='3千P人力',
		selectFieled='rl_range',
		setMon=currentDate,
		thisDateStart=currentDate,
		thisDateEnd=currentDate,
		lastDateStart=lastCurrentDate,
		lastDateEnd=lastCurrentDate,
		rangeStart=3000,
		rangeEnd=10000000,
	)
	#执行语句
	for curr_sql in currentSQL.split(";"):
		cur.execute(curr_sql.decode('utf-8'))
	cur.commit()			
	
	#--------营销万P人力--------------------------------------------------------------------------------
	#设定SQL语句参数
	currentSQL=sql_yj.format(
		category=m_cate,
		category_zh=m_cate_zh,
		series='营业组',
		kpi_name='1万P人力',
		selectFieled='rl_range',
		setMon=currentDate,
		thisDateStart=currentDate,
		thisDateEnd=currentDate,
		lastDateStart=lastCurrentDate,
		lastDateEnd=lastCurrentDate,
		rangeStart=10000,
		rangeEnd=10000000,
	)
	#执行语句
	for curr_sql in currentSQL.split(";"):
		cur.execute(curr_sql.decode('utf-8'))
	cur.commit()			
	
	#--------营销2万P人力--------------------------------------------------------------------------------
	#设定SQL语句参数
	currentSQL=sql_yj.format(
		category=m_cate,
		category_zh=m_cate_zh,
		series='营业组',
		kpi_name='2万P人力',
		selectFieled='rl_range',
		setMon=currentDate,
		thisDateStart=currentDate,
		thisDateEnd=currentDate,
		lastDateStart=lastCurrentDate,
		lastDateEnd=lastCurrentDate,
		rangeStart=20000,
		rangeEnd=10000000,
	)
	#执行语句
	for curr_sql in currentSQL.split(";"):
		cur.execute(curr_sql.decode('utf-8'))
	cur.commit()			
	
	#--------营销3万P人力--------------------------------------------------------------------------------
	#设定SQL语句参数
	currentSQL=sql_yj.format(
		category=m_cate,
		category_zh=m_cate_zh,
		series='营业组',
		kpi_name='3万P人力',
		selectFieled='rl_range',
		setMon=currentDate,
		thisDateStart=currentDate,
		thisDateEnd=currentDate,
		lastDateStart=lastCurrentDate,
		lastDateEnd=lastCurrentDate,
		rangeStart=30000,
		rangeEnd=10000000,
	)
	#执行语句
	for curr_sql in currentSQL.split(";"):
		cur.execute(curr_sql.decode('utf-8'))
	cur.commit()			
	
	#--------营销5万P人力--------------------------------------------------------------------------------
	#设定SQL语句参数
	currentSQL=sql_yj.format(
		category=m_cate,
		category_zh=m_cate_zh,
		series='营业组',
		kpi_name='5万P人力',
		selectFieled='rl_range',
		setMon=currentDate,
		thisDateStart=currentDate,
		thisDateEnd=currentDate,
		lastDateStart=lastCurrentDate,
		lastDateEnd=lastCurrentDate,
		rangeStart=50000,
		rangeEnd=10000000,
	)
	#执行语句
	for curr_sql in currentSQL.split(";"):
		cur.execute(curr_sql.decode('utf-8'))
	cur.commit()			
	
	#--------营销10万P人力--------------------------------------------------------------------------------
	#设定SQL语句参数
	currentSQL=sql_yj.format(
		category=m_cate,
		category_zh=m_cate_zh,
		series='营业组',
		kpi_name='10万P人力',
		selectFieled='rl_range',
		setMon=currentDate,
		thisDateStart=currentDate,
		thisDateEnd=currentDate,
		lastDateStart=lastCurrentDate,
		lastDateEnd=lastCurrentDate,
		rangeStart=100000,
		rangeEnd=10000000,
	)
	#执行语句
	for curr_sql in currentSQL.split(";"):
		cur.execute(curr_sql.decode('utf-8'))
	cur.commit()			


#执行合计-------------------------------------------------------------------------------------------------------
currentSQL=sql_sum.format(kpi_name='规模保费')
for curr_sql in currentSQL.split(";"):
	cur.execute(curr_sql.decode('utf-8'))
cur.commit()			

currentSQL=sql_sum.format(kpi_name='标准保费')
for curr_sql in currentSQL.split(";"):
	cur.execute(curr_sql.decode('utf-8'))
cur.commit()			

currentSQL=sql_sum.format(kpi_name='活动人力')
for curr_sql in currentSQL.split(";"):
	cur.execute(curr_sql.decode('utf-8'))
cur.commit()			

currentSQL=sql_sum.format(kpi_name='月初人力')
for curr_sql in currentSQL.split(";"):
	cur.execute(curr_sql.decode('utf-8'))
cur.commit()			

currentSQL=sql_sum.format(kpi_name='千P人力')
for curr_sql in currentSQL.split(";"):
	cur.execute(curr_sql.decode('utf-8'))
cur.commit()			

currentSQL=sql_sum.format(kpi_name='3千P人力')
for curr_sql in currentSQL.split(";"):
	cur.execute(curr_sql.decode('utf-8'))
cur.commit()			

currentSQL=sql_sum.format(kpi_name='1万P人力')
for curr_sql in currentSQL.split(";"):
	cur.execute(curr_sql.decode('utf-8'))
cur.commit()			

currentSQL=sql_sum.format(kpi_name='2万P人力')
for curr_sql in currentSQL.split(";"):
	cur.execute(curr_sql.decode('utf-8'))
cur.commit()			

currentSQL=sql_sum.format(kpi_name='3万P人力')
for curr_sql in currentSQL.split(";"):
	cur.execute(curr_sql.decode('utf-8'))
cur.commit()			

currentSQL=sql_sum.format(kpi_name='5万P人力')
for curr_sql in currentSQL.split(";"):
	cur.execute(curr_sql.decode('utf-8'))
cur.commit()			

currentSQL=sql_sum.format(kpi_name='10万P人力')
for curr_sql in currentSQL.split(";"):
	cur.execute(curr_sql.decode('utf-8'))
cur.commit()			

currentSQL=sql_sum.format(kpi_name='主管人力')
for curr_sql in currentSQL.split(";"):
	cur.execute(curr_sql.decode('utf-8'))
cur.commit()			


#对表中的数据进行特殊处理---------------------------------------------------------------------------------------
cur.execute("update administrator.hn_kpi_information set partname='无头部' where series='营业组' and partname is null ".decode('utf-8'))
cur.execute("update administrator.hn_kpi_information set teamname=\'无头组\' where series=\'营业组\' and teamname is null ".decode('utf-8'))
cur.commit()			


#加工营业部-----------------------------------------------------------------------------------------------------
print("加工营业部")
cur.execute("delete from administrator.hn_kpi_information where series='营业部'".decode('utf-8'))
curr_sql="""
insert into administrator.hn_kpi_information 
select 
        category,
        '营业部',
        branch,
        aracde,
        partname,
        '',
        kpi_name,
        kpi_mon,
        sum(this_mon),
        sum(last_mon),
        processing_time
        from administrator.hn_kpi_information
                where series='营业组'
                        group by         
                        category,
                        branch,
                        aracde,
                        partname,
                        kpi_name,
                        kpi_mon,
                        processing_time
"""
cur.execute(curr_sql.decode('utf-8')) 
cur.commit()			


#加工支公司-----------------------------------------------------------------------------------------------------
print("加工支公司")
cur.execute("delete from administrator.hn_kpi_information where series='支公司'".decode('utf-8'))
curr_sql="""
insert into administrator.hn_kpi_information 
select 
        category,
        '支公司',
        branch,
        aracde,
        '',
        '',
        kpi_name,
        kpi_mon,
        sum(this_mon),
        sum(last_mon),
        processing_time
        from administrator.hn_kpi_information
                where series='营业组'
                        group by         
                        category,
                        branch,
                        aracde,
                        kpi_name,
                        kpi_mon,
                        processing_time
"""
cur.execute(curr_sql.decode('utf-8')) 
cur.commit()			


#加工中支-----------------------------------------------------------------------------------------------------
print("加工中支")
cur.execute("delete from administrator.hn_kpi_information where series='中支'".decode('utf-8'))
curr_sql="""
insert into administrator.hn_kpi_information 
select 
        category,
        '中支',
        branch,
	'',
        '',
        '',
        kpi_name,
        kpi_mon,
        sum(this_mon),
        sum(last_mon),
        processing_time
        from administrator.hn_kpi_information
                where series='营业组'
                        group by         
                        category,
                        branch,
                        kpi_name,
                        kpi_mon,
                        processing_time
"""
cur.execute(curr_sql.decode('utf-8')) 
cur.commit()			

#加工个险
print("加工个险")
cur.execute("delete from administrator.hn_kpi_information where category='个险'".decode('utf-8'))
curr_sql="""
insert into  administrator.hn_kpi_information
select 
        '个险',
        series,
        branch,
        aracde,
        partname,
        teamname,
        kpi_name,
        kpi_mon,
        sum(case when this_mon is null then 0 else this_mon end),
        sum(case when last_mon is null then 0 else last_mon end),
        current timestamp
        from administrator.hn_kpi_information
                        group by         
                        series,
                        branch,
                        aracde,
                        partname,
                        teamname,
                        kpi_name,
                        kpi_mon
"""
cur.execute(curr_sql.decode('utf-8')) 
cur.commit()			
cur.close()

