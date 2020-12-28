"""
This script simulates different DB access workloads. I
In order to simulate workloads it executes some queries on previously created queues. Those queues should be previously created by the initialize_workload.py script
The configuration settings are retrieved from the workload.ini file
The script iterates through the test queues specified on the settings.
We can provide to it one input argument. If it is 'now', it will skip the initial menu and run the script with the settings in the workload.ini
"""


import sqlite3
import configparser
import time
import random
import multiprocessing
import os
import functions as x
from functions import date_print
import table_functions as tf
from query_execution_class import query_execution
import sys

interactive=True
if len(sys.argv)>1:
  if sys.argv[1].lower() == 'now':
    interactive=False

### **********************************
### LOAD VARIRABLES FROM .INI FILE ###
### **********************************

### Initialize Config ###
config = configparser.ConfigParser()
config.read('workload.ini')

### get parameter values from .ini file:
# get execution mode ( production or development )
execution_mode= eval(config.get("general_settings", "mode"))

# get param values for the execution mode above:
workload_db=eval(config.get(execution_mode+"_settings", "sqlite_db"))
run_queries=eval(config.get(execution_mode+"_settings", "run_queries"))
frequency_seconds=eval(config.get(execution_mode+"_settings", "scheduler_frequency"))
#set dev to true or false depending on the execution mode:
dev=x.development_mode(execution_mode)

#get test settings (queues we want to use and test details)
[details, test_queue_string]=x.test_settings_menu('workload.ini',interactive)
test_queues=tuple(test_queue_string.replace("'","").split(","))
print(type(test_queues))
print(test_queues)
### ************************
### START WORKLOAD TESTS ###
###*************************

date_print('\nSTARTING TEST SET\n')
print('')
queue_iteration=1
#loops that iterates through each of the test queues
for test_queue in test_queues:
  # connect to sqlite3 workload database
  [conn, cursor]=x.sqlite3db(workload_db)
  #get current test number
  cursor.execute("select IFNULL(MAX(test_number),0) from workload_log")
  test_number = cursor.fetchone()[0]+1
  test_queue=test_queue.replace(",","")  ## For some reason the comma gets here wiht the queue name, so we remove it
  date_print('QUEUE ITERATION NUMBER: '+str(queue_iteration))
  date_print('STARTING TEST NUMBER: '+str(test_number)+'  QUEUE: '+test_queue)
  
  # (re)create table for currently running queries
  tf.create_table_running_now(workload_db)
  # generate test queue
  
  x.generate_current_queue(test_queue, workload_db)
  queue_size=x.get_queue_size(cursor)
  x.dev_print(dev,'queue_size: '+str(queue_size))

  minute=0 # current minute
  process_number=1 # current process
  process_pool=[]  # currently running process pool
  
  #while there are queries waiting to be executed:
  while queue_size > 0:
    #x.dev_print(dev,'queue_size: '+str(queue_size))
    cursor.execute("""select distinct cq.queue_id,execution_minute,cq.query, cq.query_file, filter_values, queue,wf.parallel_run,wf.only_sequential 
                      from current_queue cq 
                      left join workload_frequencies wf on (cq.query_file=wf.query) 
                      left join running_now rn on  (cq.query_file=rn.query_file) 
                      where
                      ( wf.parallel_run=1 OR ( wf.parallel_run=0 AND rn.query_file is null) ) 
                      and execution_minute <= ? 
                      and ( only_sequential=0 OR ((select count(*) from running_now) =0) )
                      order by cq.queue_id, cq.execution_minute 
                      """, (minute,))
    #cursor.execute("""select cq.queue_id,execution_minute,cq.query, cq.query_file, filter_values, queue from current_queue cq where execution_minute <= ? order by execution_minute", (minute,)) 
    results=cursor.fetchall()
	
    x.dev_print(dev,'minute '+str(minute)) 
    
    queue_ids=[]     # queue_id-s of queries launched in the following for loop
    running_now=[]   # query_file-s launched in following for loop
    query_to_run=1   # number of queries launched in following for loop
    for row in results:
	
	    ## WE CHECK REASONS BY WE SHOULDN'T RUN THE QUERY
        if row['only_sequential'] == 1 and query_to_run>1:  # only one query can be running at the same time if query is sequential
             date_print('Query '+row['query_file']+' is not going to be executed because it can only be executed when no other query is running')
             date_print('only sequential: '+str(row['only_sequential']))
             break  #we don't check more queries in this loop
        if row['parallel_run'] == 0 and row['query_file'] in running_now: # if parallel run is false, then only one query of each kind can run at the same time
             date_print('QUEUE_ID '+ str(row['queue_id']) + ' with query '+row['query_file']+' can not start because othe query already has been started in current iteration and it should NOT run in parallel')
             continue  #we skip this query but we keep checking the rest of the queries this loop
        
        #launch a process to execute the query
        current_process=multiprocessing.Process(name="Process {0}".format(process_number), target=query_execution(process_number,test_number,run_queries,row,details).run)
        process_pool.append(current_process)
        current_process.start()
        #add launched query+process to our counters and lists:
        queue_ids.append(row['queue_id'])
        running_now.append(row['query_file'])
        query_to_run+=1
        process_number+=1

    #remove launched queries from waiting queue	
    queue_id_string =','.join(map(str, queue_ids))  
    cursor.execute("delete from current_queue where queue_id in ("+queue_id_string+");")
    #x.dev_print(dev,'Removing from current queue queue_id: '+queue_id_string+' .. NOW running!')
    conn.commit()
    queue_size=x.get_queue_size(cursor)  # update queue size
 
    #remove finished processes from pool
    x.follow_processes_in_pool(process_pool)
    
    #sleep until next minute
    time.sleep(frequency_seconds - (time.time() % frequency_seconds))
    minute+=1
  
  # finish until all processes finish
  while process_pool:
   #remove finished processes from pool
   x.follow_processes_in_pool(process_pool)
   time.sleep(1)

  date_print('FINISHING TEST NUMBER: '+str(test_number)+'  QUEUE: '+test_queue+'\n\n')
  queue_iteration+=1

print('')
date_print('TEST SET FINISHED')
