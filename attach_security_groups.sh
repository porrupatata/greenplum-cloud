#!/bin/bash
source ./aws_functions.sh

## get gp cluster. If not provided as input argument, a menu will be prompt
select_gp_cluster "$1"
if [ -z "$greenplum_cluster" ]; then echo -e '\ngreenplum cluster not definied\n' && exit 1; fi

file_server_security_group=sg-xxxxx
cluster_security_groups=$(aws ec2 describe-security-groups --filters Name=group-name,Values=*"$greenplum_cluster"* --output text --query 'SecurityGroups[*].GroupId')
cluster_security_group=( $cluster_security_groups )
echo ${cluster_security_group[0]} 
echo ${cluster_security_group[1]} 
## add tags to volumes
for INSTANCEID in $(aws ec2 describe-instances  --filters Name=tag:Name,Values="$greenplum_cluster"*  --output text --query 'Reservations[*].Instances[*].InstanceId' |sed -e 's/[[:space:]]\+/\n/g') 
do
	#echo "instance_id: $INSTANCEID"
        INSTANCE_NAME=$(aws ec2 describe-instances --instance-ids $INSTANCEID --output text --query 'Reservations[*].Instances[*].{Name:Tags[?Key==`Name`]|[0].Value}')	
	# we only want to update the nodes cause the master has different sec groups
	if [[ $INSTANCE_NAME == *"sdw"* ]]; then
		echo "INSTACE_NAME= $INSTANCE_NAME"
		aws ec2 modify-instance-attribute --instance-id $INSTANCEID --groups ${cluster_security_group[0]} ${cluster_security_group[1]} $file_server_security_group
	fi
done;
