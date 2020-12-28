DB=workload.db
if [ ! -z "$1" ]; then
	DB="$1"
fi
echo "using DB $DB"
QUERY="select test_number, platform, test_details, queue_name, sum(strftime('%s',finish_time) - strftime('%s',start_time)), 
sum(case when finish_time is null then 0 else 1 end) as finished_queries from workload_log 
where test_number<10 or test_number > ((select max(test_number) from workload_log)-5)
group by 1,2,3,4
;"
sqlite3 $DB "$QUERY"

