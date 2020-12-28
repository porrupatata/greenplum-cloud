source ./aws_functions.sh

## get gp cluster. If not provided as input argument, a menu will be prompt
select_gp_cluster "$1"
if [ -z "$greenplum_cluster" ]; then echo -e '\ngreenplum cluster not definied\n' && exit 1; fi

##disable autoscalling
echo -e "\n RESUMING AUTOSCALING FOR $greenplum_cluster \n"
aws autoscaling  describe-auto-scaling-groups --query 'AutoScalingGroups[].[AutoScalingGroupName]' --output text| grep "$greenplum_cluster"-M |xargs aws autoscaling resume-processes --scaling-processes Launch ScheduledActions AddToLoadBalancer HealthCheck --auto-scaling-group-name

aws autoscaling  describe-auto-scaling-groups --query 'AutoScalingGroups[].[AutoScalingGroupName]' --output text| grep "$greenplum_cluster"-S |xargs aws autoscaling resume-processes --scaling-processes Launch ScheduledActions AddToLoadBalancer HealthCheck  --auto-scaling-group-name

aws autoscaling  describe-auto-scaling-groups --query 'AutoScalingGroups[].[AutoScalingGroupName]' --output text| grep "$greenplum_cluster"-M |xargs aws autoscaling update-auto-scaling-group --min-size 0  --auto-scaling-group-name

aws autoscaling  describe-auto-scaling-groups --query 'AutoScalingGroups[].[AutoScalingGroupName]' --output text| grep "$greenplum_cluster"-S  |xargs aws autoscaling update-auto-scaling-group --min-size 0  --auto-scaling-group-name

