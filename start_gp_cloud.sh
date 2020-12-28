#!/bin/bash
source ./aws_functions.sh


## get gp cluster. If not provided as input argument, a menu will be prompt
select_gp_cluster "$1"
if [ -z "$greenplum_cluster" ]; then echo -e '\ngreenplum cluster not definied\n' && exit 1; fi


KEY=greenplum-cloud.pem
if [[ "$greenplum_cluster" == *"10n2D"* ]]; then
	KEY=xxxxxxx.pem.ppk
fi

echo "master_ip is $MASTER_IP"


aws ec2 describe-instances  --filters  Name=instance-state-name,Values=stopped Name=tag:Name,Values="$greenplum_cluster"*  --output text --query 'Reservations[*].Instances[*].InstanceId' |sed -e 's/[[:space:]]\+/\n/g' |xargs aws ec2 start-instances --instance-ids
iterations=1
all_running=0
echo 'STARTING INSTANCES'
while [ $all_running -eq 0 ]
do
	sleep 10
	output=$(aws ec2 describe-instances  --filters "Name=tag:Name,Values="$greenplum_cluster"*" --output text --query 'Reservations[*].Instances[*].InstanceId' |sed -e 's/[[:space:]]\+/\n/g' |xargs aws ec2 describe-instance-status --query 'InstanceStatuses[*].InstanceStatus.Status'  --output text --instance-id )
	seconds=$(($iterations*10))
	echo "status after $seconds seconds : $output"
	 if [ ${#output} -gt 0 ]; then # we are checking if there is some output, as there is only output when instances running
		all_running=1
	 fi
	for status in $output
	do
		#echo "status: $status"
		if [ "$status" != "ok" ]; then
		   	#echo "status: $status"
			all_running=0
		fi
	done
	iterations=$(($iterations+1))
	if [ "$iterations" -gt 30 ]; then
		echo "THIS IS TAKING TOO LONG. INSTANCES ARE NOT STARTING UP. EITHER TAKE A LOOK OR  TRY AGAIN, please."
		exit
	fi
	
done


get_gp_master_ip $greenplum_cluster
ssh  -i "$KEY"  gpadmin@"$MASTER_IP" 'gpstart -a'
## start pgbouncer normally and restart 5 secs later cause it looks like the rewrite doesnt work otherwise.. why?
ssh  -i "$KEY"  gpadmin@"$MASTER_IP" 'pgbouncer -d /data1/master/pgbouncer/pgbouncer.ini'
sleep 5
ssh  -i "$KEY"  gpadmin@"$MASTER_IP" 'pgbouncer -R -d /data1/master/pgbouncer/pgbouncer.ini'
ssh  -i "$KEY"  gpadmin@"$MASTER_IP" 'gpcc start'
