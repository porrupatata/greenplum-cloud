"""
Set of functions used by the workload scripts
"""

import sqlite3
import json
import configparser
import table_functions as tf
import pandas as pd
import re
import datetime
from os import system

### **********************************
### LOAD VARIRABLES FROM .INI FILE ###
### **********************************

### Initialize Config ###
config = configparser.ConfigParser()
config.read('workload.ini')
query_folder= eval(config.get("general_settings", "query_folder"))

### get parameter values from .ini file:
# get execution mode ( production or development )
execution_mode= eval(config.get("general_settings", "mode"))



### **********************************
### GENERAL USAGE FUNCTIONS        ###
### **********************************


#Function that rovides connection to sqlite workload DB
def sqlite3db(db):
 conn = sqlite3.connect(db,timeout=30)
 conn.row_factory=sqlite3.Row
 cursor = conn.cursor()
 return [conn, cursor]


#Function that adds timestamp to the print
def date_print(whatever):
  nowDateTime=str(datetime.datetime.now().strftime("%Y%m%d|%H:%M:%S.%f"))
  print(nowDateTime+' - '+str(whatever))


#Function that only prints if we are in development mode
def dev_print(dev, whatever):
 if dev:
   date_print('DEVELOPMENT : '+str(whatever))
   #date_print(whatever)


#Function to leverage the development mode. Basically says if development mode is trur or not.
def development_mode(execution_mode):
 if execution_mode == "development":
   print('DEVELOPMENT MODE!!')
   dev=True
 elif execution_mode == "production":
  print ('PRODUCTION MODE!!')
  dev=False
 return dev

dev=development_mode(execution_mode)


#Function to return the details (cpu, instance type, ram... ) of the test we are running
#Not done yet
#Could have defaults and allow user input??
def get_details():
 #needs to be implemented
 return('no details so far')





### ***********************************
### INITIALIZATION SCRIPT FUNCTIONS ###
### ***********************************

#Function to load the query files specified in the the reference csv file
def load_query_files(query_frequency_file):
   queries=pd.read_csv(query_frequency_file)

   #get query filter fields
   placeholders=[]
   for index, row in queries.iterrows():
      query_file=row['file']
      with open(query_folder+'/'+query_file+'.sql', 'r') as myfile:
         query_text = myfile.read()
      placeholders.append(re.findall(r"{([a-zA-Z_]+)}",query_text))
   queries["filters"]=placeholders
   return queries


#Function that creates a table with info about the queries we want to use
def populate_workload_frequency_table(workload_db,queries):
  tf.create_table_workload_frequencies(workload_db)
  [conn, cursor]=sqlite3db(workload_db)
  for index, row in queries.iterrows():
     if row['parallel'] == 't':
       parallel_run=1
     else:
       parallel_run=0
     #date_print('parallel:'+str(parallel))
     cursor.execute("INSERT INTO workload_frequencies ( query, frequency, parallel_run, only_sequential) values (?,?,?,?)",(row['file'],row['frequency'],parallel_run,0))
  conn.commit()
  cursor.close()


### ***********************************
### WORKLOAD EXECUTION FUNCTIONS    ###
### ***********************************

#Function to create and populate the table that will keep the query queue currently in use
def generate_current_queue(queue_id,workload_db):
 [conn,cursor] = sqlite3db(workload_db)
 original_query_text={}
 cursor.execute("SELECT distinct query_file from workload_queues where queue=?",(queue_id,))
 for file in cursor:
  query_file=''.join(file)
  with open(query_folder+'/'+query_file+'.sql', 'r') as myfile:
   original_query_text[query_file] = myfile.read()
 tf.create_table_current_queue(workload_db)
 cursor.execute("SELECT execution_minute,query_file, filter_values,queue from workload_queues where queue=? order by 1",(queue_id,))
 results=cursor.fetchall()
 i=1
 for execution_minute, query_file, filter_values, queue in results:
  #date_print(i)
  fields=json.loads(filter_values)
  fields['id']=i
  i+=1
  filtered_query_text=original_query_text[query_file].format(**fields)
  #date_print(filtered_query_text)
  #date_print(str(execution_minute)+' '+query_file)
  cursor.execute("insert into current_queue (execution_minute,query, query_file, filter_values, queue) values (?,?,?,?,?)", (execution_minute,filtered_query_text,query_file,filter_values,queue))
 conn.commit()
 cursor.execute("select * from current_queue")
 for row in cursor:
  dev_print(dev,'QUEUEID: '+str(row['queue_id'])+ ' - execution minute: '+str(row['execution_minute']) +' - Query: '+row['query_file'])

#Function to check if there is any process left in the process pool so make sure all of them finish
def follow_processes_in_pool(process_pool):
 for process in process_pool:
        # check if process has died
        if not process.is_alive():
            date_print(process.name+' with PID '+str(process.pid)+' has finished and it is being removed from the pool')
            # recover/join the process and remove it from the pool
            process.join()
            process_pool.remove(process)
            del(process)

# Function that checks how many queries are waiting to be executed in the queue
def get_queue_size(cursor):
  cursor.execute("select count(*) as queue_size from current_queue")
  queue_size=cursor.fetchone()[0]
  return queue_size

### ***************************************
### WORKLOAD EXECUTION MENU FUNCTIONS  ###
### ***************************************


def read_test_settings(configuration_ini_file):
  ### Initialize Config ###
  config = configparser.ConfigParser()
  config.read(configuration_ini_file)
  test_settings=dict(config.items('test_settings'))
  return test_settings

def get_execution_mode(configuration_ini_file):
  ### Initialize Config ###
  config = configparser.ConfigParser()
  config.read(configuration_ini_file)
  execution_mode= eval(config.get("general_settings", "mode"))
  return execution_mode


##function to process user input and update the corresponding param
def process_input_selection(menu,selection):
      index=int(selection)-1 
      new_value=input("\nInsert new value for parameter   ## "+menu.iloc[index]['parameter']+" ##  :\n Or press ENTER to return to main menu\n")
      if new_value != '':
          menu.iloc[index]['value']=new_value
      system('clear')

##function to print the header of the menu
def print_menu_header(test_settings, execution_mode):
  system('clear')
  print('\n')
  print('\n#############################################################################################\n')
  print(' 	# # # # # #    		 WORKLOAD SIMULATION SCRIPT      	# # # # # #             ')
  print('\n#############################################################################################\n')
  print('\nThe simulation is about to start with the following settings:\n')
  print('Execution Mode: '+str(execution_mode))
  print('Platform: '+str(test_settings['platform'])+'\n')

##function to show and edit the test details
def get_details(test_settings,execution_mode):
  test_details=json.loads(test_settings['details'])
  param_count=len(test_details)
  menu=pd.DataFrame(list(test_details.items()), columns=['parameter','value'])
  while True: 
    print_menu_header(test_settings,execution_mode)
    for entry,row in menu.iterrows(): 
         print(str(entry+1)+' - '+row['parameter']+': '+str(row['value']))

    selection=input("\n\nPLEASE, PRESS ENTER TO CONTINUE\nOr select the option you'd like change:\n") 
  
    if selection in tuple(''.join(str(i) for i in range(1,param_count+1))):
        process_input_selection(menu,selection)
    elif selection == '': 
        break
    else: 
        print ("\nUnknown Option Selected!\n")

  #generate details output string
  details={}
  for entry, row in menu.iterrows():
    details[row['parameter']]=row['value']
  db_ready_details=json.dumps(details)
  return db_ready_details


##function to show and edit test_queues
def get_test_queues(queues):
  while True:
    selection=input("\nQUEUES TO TEST: "+str(queues.replace("'",""))+  "\nPRESS ENTER TO CONTINUE or\nInsert queue options comma separated ( or add comma at the end if only one queue selected ): \n")
    if selection == '':
       break
    else: 
       queues=selection
  return queues

##function to show and edit test settings
def test_settings_menu(configuration_ini_file,interactive):
  test_settings=read_test_settings(configuration_ini_file)
  if interactive:
    execution_mode=get_execution_mode(configuration_ini_file)
    details=get_details(test_settings,execution_mode)
    test_queues=get_test_queues(test_settings['queues'])
  else:
    test_queues=test_settings['queues']
    details=json.dumps(json.loads(test_settings['details']))
  return [details,test_queues]

