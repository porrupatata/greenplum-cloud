function select_gp_cluster() {
	clear
	greenplum_stacks=$(aws cloudformation describe-stacks  --query   'Stacks[?StackName!=`null`]|[?contains(StackName, `greenplum`) == `true`].StackName' --output text|sed 's/[[:space:]]/\n/g')
	if [ -z "$1" ]; then
		stack_count=`echo "$greenplum_stacks"|wc|awk '{print $1}'`
		if [ "$stack_count" -eq 0 ]; then
			echo -e "No available greenplum clusters"
			exit 1
		elif [ "$stack_count" -eq 1 ]; then
			greenplum_cluster=$(echo "$greenplum_stacks"|sed 's/\n//g')
			echo "Processing the only available cluster : $greenplum_cluster"
		else
			echo -e '\nPlease select greenplum cluster name from bellow and press enter\n'
			echo "$greenplum_stacks"
			echo -e '\nPlease input cluster name:'
			read greenplum_cluster
		fi
	else

		greenplum_cluster="$1"
		if [[ ${greenplum_cluster} != *"greenplum-"* ]]; then
		        echo ' Cluster name should be greenplum-something'
       			exit 1
		fi
	fi
	if [[ "$greenplum_stacks" == *"$greenplum_cluster"* ]]; then
	       if [ -z "$greenplum_cluster" ];then
		   echo -e "\nNo valid greenplum cluster name provided!\n"
	           exit 1
	       fi 	
	else
		echo -e "\nNo valid greenplum cluster name provided! $greenplum_cluster\n"
		exit 1
	fi
	echo "Processing cluster:"
	echo "$greenplum_cluster"
}

function get_gp_master_ip() {
	GPCLUSTER=$1
	## get GP master IP
	MASTER_IP=`aws ec2 describe-instances  --filters "Name=tag:Name,Values=$GPCLUSTER-mdw" --output text --query 'Reservations[*].Instances[*].NetworkInterfaces[*].PrivateIpAddresses[*].PrivateIpAddress'`
	if [ -z $MASTER_IP ]; then
        	echo 'Could not retrieve MASTER IP. Cancelling execution'
        	exit 1
	else
        	echo -e "Master IP is :\n"
		echo "$MASTER_IP"
	fi
}
