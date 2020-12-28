"""
This class is used by the processes to run the queries
"""

import random
import os
import time
import wl_database
import functions as x
import configparser
import datetime
from functions import date_print

class query_execution:

    def __init__(self, cid,test_number,run_queries,row,details):
        self.__cid=cid
        self.test_number=test_number
        self.run_queries=run_queries
        self.query_data=row
        self.query=row['query']
        self.query_file=row['query_file']
        self.queue_name=row['queue']
        self.queue_id=row['queue_id']
        self.query_filters=row['filter_values']

        ### Initialize Config ###
        config = configparser.ConfigParser()
        config.read('workload.ini')
        # get execution mode ( production or development )
        self.execution_mode= eval(config.get("general_settings", "mode"))
        # get param values for the execution mode above
        self.workload_db=eval(config.get(self.execution_mode+"_settings", "sqlite_db"))
        self.platform= eval(config.get("test_settings", "platform"))
        self.test_details=details
        date_print("Process {0} STARTS! - QUEUE_ID: {1} running query {2}".format(self.__cid,self.query_data['queue_id'],self.query_data['query_file']))

    
    # main execution function
    # switch beteen query execution or just workload script test
    def run(self):
        self.pid=os.getpid()
        self.add_query_to_running_now()
        if self.run_queries == 'yes':
            self.run_sql()
        else:
           self.run_sleep()

    # It executes the queries
    def run_sql(self,):
        self.connection_start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        db = wl_database.WLDatabase()
        db.connect()
        self.query_start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        try:
            db.execute_sql(self.query,self.query_file)
        except:
            print('SQL execution error at '+self.query_file)
            #print(e)
            self.query_finish_time = None 
        else:
            print('sql sucessfully executed:' + self.query_file)
            self.query_finish_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        db.close()
        #date_print(get_query_to_run())
        self.log_execution()
        return
    
    # It just makes the process sleep for some random seconds instead of executing the queries
    def run_sleep(self):
        self.connection_start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        sleep_time=random.randrange(1,30)
        date_print("""Process {0} with PID {1}, running {2} is goint to sleep  {3} seconds  """.format(self.__cid,self.pid,self.query_data['query_file'],sleep_time))
        self.query_start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        time.sleep(sleep_time)
        self.query_finish_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        self.log_execution()
        date_print("""Process {0} FINISHES! after it has slept  {1} seconds  """.format(self.__cid,sleep_time))

    # log query execution times
    def log_execution(self):
       [conn, cursor]=x.sqlite3db(self.workload_db)
       cursor.execute("""insert into workload_log (
                          test_number,
                          platform,
                          test_details,
			  queue_name,
                          queue_id,
                          pid,
		          query_file,
                          filters, 
                          query_text, 
                          connection_start_time,
                          start_time, 
                          finish_time) 
                          values (?,?, ?, ?,?,?,?,?,?,?,?,?)
                       """,
                         (self.test_number, 
                          self.platform,
                          self.test_details, 
                          self.queue_name,
                          self.queue_id,
                          self.pid,
                          self.query_file,
                          self.query_filters,
                          self.query,
                          self.connection_start_time, 
                          self.query_start_time, 
                          self.query_finish_time
                         )
                      )
       self.remove_query_from_running_now(cursor)
       conn.commit()
       cursor.close()

    # adds query to "currently running" table
    def add_query_to_running_now(self):
       [conn, cursor]=x.sqlite3db(self.workload_db)
       cursor.execute("""
                          insert into running_now (
                          queue_id,
                          query_file,
                          pid)
                          values (?,?,?)
                       """,
                          (self.queue_id,
                           self.query_file,
                           self.pid
                          )
                       )
       conn.commit()
       cursor.close()

    def remove_query_from_running_now(self,cursor):
       cursor.execute("delete from running_now where queue_id=?",(self.queue_id,))
