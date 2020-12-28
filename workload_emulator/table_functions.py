"""
Functions to create tables used by the workload script either to manage queues or store results
"""

import functions as x

## Table that keeps the queries that are running right now
def create_table_running_now(db):
 [conn,cursor] = x.sqlite3db(db)
 cursor.execute("DROP TABLE IF EXISTS running_now;")
 conn.commit()
 cursor.execute("""CREATE TABLE IF NOT EXISTS running_now
                  (
                   queue_id INTEGER,
                   query_file text,
                   query text,
                   pid integer,
                   start_time timestamp default current_timestamp
                   )
                """)
 conn.commit()
 cursor.close()


## Table that keeps the query queue we are currently executing
def create_table_current_queue(db):
 [conn,cursor] = x.sqlite3db(db)
 cursor.execute("DROP TABLE IF EXISTS current_queue;")
 conn.commit()
 cursor.execute("""CREATE TABLE IF NOT EXISTS current_queue
                  (
                   queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                   execution_minute integer,
                   query text,
                   query_file text,
                   filter_values text,
                   queue text
                   )
                """)
 conn.commit()
 cursor.close()

## Table that keeps all the queues of our test set
def create_table_workload_queues(db):
 [conn,cursor] = x.sqlite3db(db)
 cursor.execute("""DROP TABLE IF EXISTS workload_queues;""")
 conn.commit()
 cursor.execute("""CREATE TABLE if not exists workload_queues
                 (workload_queues_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  queue text,
                  execution_minute integer,
                  query_file text,
                  filter_values text
                  )
               """)
 conn.commit()
 cursor.close()


## Table with info about our query set
def create_table_workload_frequencies(db):
  [conn,cursor] = x.sqlite3db(db)
  cursor.execute("""DROP TABLE IF EXISTS workload_frequencies;""")
  conn.commit()
  cursor.execute("""CREATE TABLE if not exists workload_frequencies
                   (workload_frequency_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query text,
                    frequency integer,
                    parallel_run integer,
                    only_sequential integer
                  )
                """)
  conn.commit()
  cursor.close()

## Table to log test results
def create_table_workload_log(db):
 [conn,cursor] = x.sqlite3db(db)
 cursor.execute("""DROP TABLE IF EXISTS workload_log;""")
 conn.commit()
 cursor.execute("""CREATE TABLE if not exists workload_log
                 (test_number integer,
                  platform text,
                  test_details text,
                  queue_name text,
                  queue_id integer,
                  pid integer,
                  query_file text,
                  filters text,
                  query_text text,
                  connection_start_time text,
                  start_time text,
                  finish_time text)
              """)
 conn.commit()
 cursor.close()
