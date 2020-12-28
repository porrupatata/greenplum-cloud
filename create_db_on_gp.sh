## create GP DB
MASTER_IP=$1
psql -h $MASTER_IP -p 5432 -d postgres -U gpadmin -c "drop database if exists xxxxxxx;"
psql -h $MASTER_IP -p 5432 -d postgres -U gpadmin -c "create database xxxxxxx;"
psql -h $MASTER_IP -p 5432 -d xxxxxxx -U gpadmin -f /data/globals.dmp
psql -h $MASTER_IP -p 5432 -U gpadmin -d xxxxxxx -c "
CREATE SCHEMA TEMP;
"
#./load_db_using_gpload.sh  $MASTER_IP
#./psql_files_in_folder_parallel.sh $MASTER_IP
#psql -h $MASTER_IP -p 5432 -U gpadmin -d xxxxxxx -f post_table_load.sql

