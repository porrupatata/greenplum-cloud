#source ./aws_functions.sh

## get gp cluster. If not provided as input argument, a menu will be prompt
select_gp_cluster "$1"
if [ -z "$greenplum_cluster" ]; then echo -e '\ngreenplum cluster not definied\n' && exit 1; fi


## get GP master IP
MASTER_IP=`aws ec2 describe-instances  --filters "Name=tag:Name,Values=$GPCLUSTER-mdw" --output text --query 'Reservations[*].Instances[*].NetworkInterfaces[*].PrivateIpAddresses[*].PrivateIpAddress'`
if [ -z $MASTER_IP ]; then
        echo 'Could not retrieve MASTER IP. Cancelling execution'
	exit 1
else
        echo "Master IP is : $MASTER_IP"
fi

## initialise GP master: permissions, mounts 
ssh -i xxxxxxx.pem.ppk gpadmin@$MASTER_IP 'bash -s' < init_gp_master.sh

## suspend autoscaling. Otherwise we won't be able to switch off the cluster
./suspend_gp_autoscaling.sh $GPCLUSTER

## create passworless access for DB
echo "$MASTER_IP:5432:gpadmin:gpadmin:xxxxxx" >> /root/.pgpass


echo "Master IP is : $MASTER_IP"

