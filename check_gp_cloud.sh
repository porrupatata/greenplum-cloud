source ./aws_functions.sh

## get gp cluster. If not provided as input argument, a menu will be prompt
select_gp_cluster "$1"
if [ -z "$greenplum_cluster" ]; then echo -e '\ngreenplum cluster not definied\n' && exit 1; fi

aws ec2 describe-instances  --filters "Name=tag:Name,Values="$greenplum_cluster"*" --output text --query 'Reservations[*].Instances[*].[PrivateIpAddress,InstanceId,Tags[?Key==`Name`].Value,State.Name]'
aws ec2 describe-instances  --filters "Name=tag:Name,Values="$greenplum_cluster"*" --output text --query 'Reservations[*].Instances[*].InstanceId' |sed -e 's/[[:space:]]\+/\n/g' |xargs aws ec2 describe-instance-status         --query 'InstanceStatuses[*].InstanceStatus.Status'  --output text --instance-id 
