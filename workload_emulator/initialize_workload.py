import sqlite3
import configparser
import random
import json
import functions as x
import table_functions as tf
import shutil
from datetime import datetime

### Initialize Config ###
config = configparser.ConfigParser()
config.read('workload.ini')
create_test_queue= eval(config.get("query_queue", "create_test_queue"))
queue_settings= eval(config.get("query_queue", "queue_creation"))
backup_restore_query_files = eval(config.get("query_queue", "backup_restore_query_files"))
#print(query_settings)
query_folder= eval(config.get("general_settings", "query_folder"))
filter_choices=dict(config.items('query_filters'))

# get execution mode ( production or development )
execution_mode= eval(config.get("general_settings", "mode"))
# get param values for the execution mode above
workload_db=eval(config.get(execution_mode+"_settings", "sqlite_db"))
query_frequency_file=eval(config.get(execution_mode+"_settings", "query_frequency_file"))

dev=x.development_mode(execution_mode)

### backup previous workload db
dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%Y%m%d_%H%M%S")
shutil.copy(workload_db, workload_db+'.'+timestampStr)

### initialize sqlite
[conn, cursor]=x.sqlite3db(workload_db)

# reads query names from csv, read query SQL from query folder, searches required filters in query sql
queries=x.load_query_files(query_frequency_file)
x.populate_workload_frequency_table(workload_db,queries)

tf.create_table_workload_queues(workload_db)
tf.create_table_workload_log(workload_db)

#create each queue
for queueid, values in queue_settings.items():
 duration=values['duration']
 frequency_multiplier=values['freq']
 x.dev_print(dev,'QUEUEID: '+queueid)
 #print(duration)
 
 #create execution times for each query
 for index, row in queries.iterrows():
   x.dev_print(dev,row['file']+str(row['frequency']))
   query_file=row['file']
   with open(query_folder+'/'+query_file+'.sql', 'r') as myfile:
    original_query_text = myfile.read()
   hour=0
   #for each duration value (each hour)
   while hour < duration :
    count=0
    while count < row['frequency']*frequency_multiplier:
     count+=1
     start_time=random.randrange(0,60,1)+(hour*60)
     x.dev_print(dev,'time: '+str(start_time))
     fields={}
     for filter in row['filters']:
       #print(filter)
       value_list=filter_choices[filter].split(',')
       if "date" not in filter:
        # between 1 and 4 values
        number_of_values=random.randrange(1,5)
        filter_values=random.sample(value_list,k=number_of_values)
        filter_value = ','.join(map(str, filter_values))
        #print(type(filter_values))
        #print(random.sample(value_list,k=2))
       else:
        filter_value=random.choice(value_list)
       #print(filter_value)
       fields[filter]=filter_value
     x.dev_print(dev,fields)
     #print(original_query_text.format(**fields))
     filtered_query_text=original_query_text.format(**fields)     
     #print(type(fields))
     json_fields=json.dumps(fields)
     cursor.execute("insert into workload_queues (queue, execution_minute, query_file,filter_values) values ( ?,?,?,?)",(queueid,start_time,row['file'],json_fields))
    hour+=1
conn.commit() 

if create_test_queue == 't' :
  cursor.execute("insert into workload_queues (queue, execution_minute, query_file,filter_values) select 'q0', 0, query_file, min(filter_values) from workload_queues group by 1,2,3;")

#create backup/restore queue
start_minute=0
no_filters={}
for query_file in backup_restore_query_files:
  cursor.execute("insert into workload_queues (queue, execution_minute, query_file,filter_values) values (?,?,?,?)", ('q_br', start_minute, query_file,json.dumps(no_filters)))
  cursor.execute("insert into workload_frequencies ( query, parallel_run, only_sequential) values (?,?,?)",(query_file,0,1))
  start_minute+=1

conn.commit()
cursor.close()

