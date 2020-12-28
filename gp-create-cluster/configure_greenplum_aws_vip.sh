#!/bin/bash
myself=$(whoami)
if [ "$myself" != "root" ]; then
	echo "this script should be executed as root"
	exit
fi

GP_ZEUS_VIP_NETWORK_INTERFACE_NAME=greenplum-xxxxx-vip

NEW_MAC=$(aws ec2 describe-network-interfaces --filters Name=tag:Name,Values=$GP_ZEUS_VIP_NETWORK_INTERFACE_NAME  --output text --query 'NetworkInterfaces[*].MacAddress')
IP=$(hostname -i)
VIP=$(aws ec2 describe-network-interfaces --filters Name=tag:Name,Values=$GP_ZEUS_VIP_NETWORK_INTERFACE_NAME  --output text --query 'NetworkInterfaces[*].PrivateIpAddress')
echo "VIP: $VIP"
SUBNET=$(echo "$IP" | sed -e 's/\(.*\)\.[0-9]*$/\1/g')

GATEWAYSET=$(cat /etc/sysconfig/network |grep GATEWAYDEV=eth0|wc|awk '{print $1}')
if [ "$GATEWAYSET" -eq "0" ]; then
	echo 'GATEWAYDEV=eth0' >> /etc/sysconfig/network
fi
cd /etc/sysconfig/network-scripts
:
echo 'creating  ifcfg-eth1 file'
cp ifcfg-eth0 ifcfg-eth1
sed -i 's/eth0/eth1/g' ifcfg-eth1
sed -i "s/HWADDR=.*/HWADDR=$NEW_MAC/g" ifcfg-eth1

echo 'creating route-ethX files '
cat <<EOF > route-eth0
default via $SUBNET.1 dev eth0 table 1
$SUBNET.0/24 dev eth0 src $IP table 1
EOF
cat <<EOF > route-eth1
default via $SUBNET.1 dev eth1 table 2
$SUBNET.0/24 dev eth1 src $VIP table 2
EOF

echo 'creating rule-ethX files '
echo "from $IP/32 table 1" > rule-eth0
echo "from $VIP/32 table 2" > rule-eth1

service network restart 2>/dev/null || true



