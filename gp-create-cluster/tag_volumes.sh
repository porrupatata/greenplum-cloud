#!/bin/bash
source ./aws_functions.sh

## get gp cluster. If not provided as input argument, a menu will be prompt
select_gp_cluster "$1"
if [ -z "$greenplum_cluster" ]; then echo -e '\ngreenplum cluster not definied\n' && exit 1; fi

## add tags to volumes
for INSTANCEID in $(aws ec2 describe-instances  --filters Name=tag:Name,Values="$greenplum_cluster"*  --output text --query 'Reservations[*].Instances[*].InstanceId' |sed -e 's/[[:space:]]\+/\n/g') 
do
	echo "instance_id: $INSTANCEID"
	INSTANCE_NAME=$(aws ec2 describe-instances --instance-ids $INSTANCEID --output text --query 'Reservations[*].Instances[*].{Name:Tags[?Key==`Name`]|[0].Value}') 
	
	VOLUME_NAME="$INSTANCE_NAME"-DATA1
	VOLUMEID=$(aws ec2 describe-volumes --output text --query "Volumes[*].{ID:VolumeId}" --filters Name=volume-type,Values=st1 Name=attachment.device,Values=/dev/sdb  Name=attachment.instance-id,Values=$INSTANCEID)
	aws ec2 create-tags --resources $VOLUMEID --tags Key=Name,Value=$VOLUME_NAME

	VOLUME_NAME="$INSTANCE_NAME"-DATA2
	VOLUMEID=$(aws ec2 describe-volumes --output text --query "Volumes[*].{ID:VolumeId}" --filters Name=volume-type,Values=st1 Name=attachment.device,Values=/dev/sdc  Name=attachment.instance-id,Values=$INSTANCEID)
	aws ec2 create-tags --resources $VOLUMEID --tags Key=Name,Value=$VOLUME_NAME
	
	VOLUME_NAME="$INSTANCE_NAME"-DATA3
	VOLUMEID=$(aws ec2 describe-volumes --output text --query "Volumes[*].{ID:VolumeId}" --filters Name=volume-type,Values=st1 Name=attachment.device,Values=/dev/sdd  Name=attachment.instance-id,Values=$INSTANCEID)
	aws ec2 create-tags --resources $VOLUMEID --tags Key=Name,Value=$VOLUME_NAME
done;
