#!/bin/bash
##password login gpadmin
sudo su
echo 'root:smart642' | sudo chpasswd
echo 'gpadmin:xxxxxxx' | sudo chpasswd
echo 'backup:xxxxxxx' | sudo chpasswd
sudo sed 's/PasswordAuthentication/#PasswordAuthentication/g' -i /etc/ssh/sshd_config
sudo sed 's/PermitRootLogin/#PermitRootLogin/g' -i /etc/ssh/sshd_config
sudo echo -e '\nPasswordAuthentication yes' >> /etc/ssh/sshd_config
sudo echo -e '\nPermitRootLogin yes' >> /etc/ssh/sshd_config
sudo service sshd restart
##passwordless login to gpadmin from backup@hotdb
sudo cat /home/backup/.ssh/authorized_keys |grep hotdb >> /home/gpadmin/.ssh/authorized_keys
##passwordless ssh from backup to gpadmin on GP mdw
sudo cat /home/backup/.ssh/id_rsa.pub >> /home/gpadmin/.ssh/authorized_keys
sudo cat /home/gpadmin/.bashrc > /home/backup/.bashrc

##mount drives
sudo yum install -y nfs-utils mailx
sudo mkdir -p /yyyyyyyy && sudo echo 'x.x.x.x:/xxxxxxxx   /yyyyyyyy      nfs        defaults,nofail    0 0' >> /etc/fstab
sudo mount -a


##mount efs
sudo yum -y install rpm-build
cd /home/gpadmin
git clone https://github.com/aws/efs-utils
cd efs-utils
sudo make rpm
sudo yum -y install ./build/amazon-efs-utils*rpm
sudo mkdir /mnt/gp_efs && sudo echo 'xxxxxxxxx.efs.eu-west-1.amazonaws.com:/ /mnt/zzzzzzz      efs defaults,nofail 0 0' >> /etc/fstab
sudo mount -a




##AWS timeout issue:
sudo /sbin/sysctl -w net.ipv4.tcp_keepalive_time=300 net.ipv4.tcp_keepalive_intvl=300 net.ipv4.tcp_keepalive_probes=60
sudo cat <<EOT>> /etc/sysctl.d/aws_timeout.conf
net.ipv4.tcp_keepalive_time=300
net.ipv4.tcp_keepalive_intvl=300
net.ipv4.tcp_keepalive_probes=60
EOT

##create folder for data_files to load
mkdir /data/xxxxxx
chown gpadmin -R /data/xxxxxx

##set GP psql credentials
sudo su - gpadmin
psql -c "alter role gpadmin with password 'xxxxxxx'"
psql -c "alter role mon with password 'xxxxxxx'"
gpconfig -c default_statistics_target -v 500
gpconfig --skipvalidation -c datestyle -v "'iso, dmy'"

echo '*:*:*:backup:xxxxxxx'>>/home/gpadmin/.pgpass
##restart
gpstop -ar -M fast
