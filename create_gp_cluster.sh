CREATE_DB=YES
CREATE_DB=NO


## check if we have provided the cluster name
if [ -z "$1" ]; then
	echo 'Please enter GP cluster name'
	exit 1
fi

GPCLUSTER="$1"

## cluster name should be lower case and without underscores. For example greenplum-super-cluster
if [[ ${GPCLUSTER} != *"greenplum-"* ]]; then
	echo ' Cluster name should be greenplum-something'
	exit 1
fi

## upload to S3 new cloudformation template if needed
aws s3 cp GP_cloudformation.json s3://cloud-warehouse/cloudformation/

## create GP cluster
aws cloudformation create-stack --stack-name "$1" \
--template-url https://cloud-warehouse.s3-eu-west-1.amazonaws.com/cloudformation/GP_cloudformation.json \
--capabilities CAPABILITY_IAM \
--tags Key=Project,Value=greenplum \
--parameters file://gp_cluster_parameters.json

echo -e "
PRESS ENTER WHEN THE $GPCLUSTER CLUSTER HAS BEEN CREATED
"
read

## get GP master IP
MASTER_IP=`aws ec2 describe-instances  --filters "Name=tag:Name,Values=$GPCLUSTER-mdw" --output text --query 'Reservations[*].Instances[*].NetworkInterfaces[*].PrivateIpAddresses[*].PrivateIpAddress'`
if [ -z $MASTER_IP ]; then
        echo 'Could not retrieve MASTER IP. Cancelling execution'
	exit 1
else
	MASTER=$(echo $MASTER|awk '{print $1}')  # in case we also have the vip, we only need one ip
        echo "Master IP is : $MASTER_IP"
fi

## initialise GP master: permissions, mounts 
ssh -i greenplum-cloud.pem  gpadmin@$MASTER_IP 'bash -s' < init_gp_master.sh

## suspend autoscaling. Otherwise we won't be able to switch off the cluster
./suspend_gp_autoscaling.sh $GPCLUSTER

## attached security groups
./attach_security_groups.sh $GPCLUSTER

## tag EBS volumes
./tag_volumes.sh $GPCLUSTER

## create passworless access for DB
echo "$MASTER_IP:5432:gpadmin:gpadmin:xxxxxxx" >> /root/.pgpass
echo "$MASTER_IP:5432:xxxxxxx:gpadmin:xxxxxxx" >> /root/.pgpass
echo "$MASTER_IP:5432:postgres:gpadmin:xxxxxxx" >> /root/.pgpass


if [ "$CREATE_DB" == "YES" ]; then
	## create GP DB
	./create_db_on_gp.sh "$MASTER_IP"
fi

##load globals
psql -h $MASTER_IP -p 5432 -d postgres -U gpadmin -f cloud_globals.dmp

##create missin resource groups and assign roles to them 
psql -h $MASTER_IP -p 5432 -d postgres -U gpadmin -f resource_group_settings.sql 

echo "Master IP is : $MASTER_IP"


