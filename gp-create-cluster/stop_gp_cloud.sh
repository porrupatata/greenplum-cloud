source ./aws_functions.sh

## get gp cluster. If not provided as input argument, a menu will be prompt
select_gp_cluster "$1"
if [ -z "$greenplum_cluster" ]; then echo -e '\ngreenplum cluster not definied\n' && exit 1; fi

if [[ "$greenplum_cluster" == *"10n2D"* ]]; then
        KEY=xxxxxxx.pem.ppk
fi

get_gp_master_ip $greenplum_cluster
echo "master_ip is $MASTER_IP"

ssh -i "$KEY"  gpadmin@"$MASTER_IP" 'gpstop -a -M fast'
aws ec2 describe-instances  --filters  Name=instance-state-name,Values=running Name=tag:Name,Values="$greenplum_cluster"* --output text --query 'Reservations[*].Instances[*].InstanceId' |sed -e 's/[[:space:]]\+/\n/g' |xargs aws ec2 stop-instances --instance-ids
aws ec2 describe-instances  --filters "Name=tag:Name,Values="$greenplum_cluster"*" --output text --query 'Reservations[*].Instances[*].[State.Name]'

