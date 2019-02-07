#!/bin/bash
#
#
# jomoon@pivotal.io

# Take one argument from the commandline: VM name
if ! [ $# -eq 1 ]; then
    echo "Usage: $0 <node-name>"
    exit 1
fi

# Check if domain already exists
virsh dominfo $1 > /dev/null 2>&1
if [ "$?" -eq 0 ]; then
    echo -n "[WARNING] $1 already exists.  "
    read -p "Do you want to overwrite $1 [y/N]? " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
    else
        echo -e "\nNot overwriting $1. Exiting..."
        exit 1
    fi
fi

# Directory to store images
DIR=/storage

# Location of cloud image
IMAGE=$DIR/rhel76-temp.qcow2

# Amount of RAM in MB
MEM=4096

# Number of virtual CPUs
CPUS=2

# Number of virtual CPUs CPUS=2
# Cloud init files
USER_DATA=user-data
META_DATA=meta-data
CI_ISO=$1-cidata.iso
DISK=$1.qcow2

# Bridge for VMs (default on Fedora is virbr0)
BRIDGE=virbr1

# Start clean
rm -rf $DIR/$1
mkdir -p $DIR/$1

pushd $DIR/$1 > /dev/null

    # Create log file
    sudo touch $DIR/$1/$1.log

    echo "$(date -R) Destroying the $1 domain (if it exists)..."

    # Remove domain with the same name
    sudo virsh destroy $1 >> $DIR/$1/$1.log 2>&1
    sudo virsh undefine $1 >> $DIR/$1/$1.log 2>&1

    # cloud-init config: set hostname, remove cloud-init package,
    # and add ssh-key 
    sudo cat > $USER_DATA << _EOF_
#cloud-config

preserve_hostname: False
hostname: $1
fqdn: $1.jtest.pivotal.io

network: {config: disabled}
bootcmd:
  - set -x; echo '#user-data/bootcmd:' >> /etc/sysconfig/network-scripts/ifcfg-eth0
  - set -x; sed -i -e '/^BOOTPROTO/ s/dhcp/static/g' -e '/PERSISTENT_DHCLIENT/d' /etc/sysconfig/network-scripts/ifcfg-eth0
  - set -x; echo 'IPADDR=192.168.0.10' >> /etc/sysconfig/network-scripts/ifcfg-eth0
  - set -x; echo 'NETMASK=255.255.255.0' >> /etc/sysconfig/network-scripts/ifcfg-eth0
  - set -x; echo 'GATEWAY=192.168.0.1' >> /etc/sysconfig/network-scripts/ifcfg-eth0
  - set -x; echo 'DNS1=8.8.8.8' >> /etc/sysconfig/network-scripts/ifcfg-eth0
  - set -x; echo 'ONBOOT="yes"' >> /etc/sysconfig/network-scripts/ifcfg-eth0
  - set -x; echo 'NM_CONTROLLED=no' >> /etc/sysconfig/network-scripts/ifcfg-eth0
  - ifdown eth0
  - ifup eth0

# Remove cloud-init when finished with it
runcmd:
  - [ yum, -y, remove, cloud-init ]

output:
  all: ">> /var/log/cloud-init.log"

ssh_svcname: ssh
ssh_deletekeys: True
ssh_genkeytypes: ['rsa', 'ecdsa']

ssh_authorized_keys:
  - ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDEv4Q0604MrukxXF7d4RKbLOrfdo29vSLRXTxdNBFFDxZjkyKqq3OnRHboAMc57P74vFDGA/sOJ8Qsqrbo7G/SD4So07RO+PGpGObCkgMtbZoQUC/uDI9W5Ae6fS+Uz8td8GaYz9D1I53ZuHQ+Pzzuu2h43HwWrtgTIdUTAZB7fJhpwASrwb5iLy2EGf7IacBUl/R7G2SNmcTN3i9L2JMVruvnEt1iVU6t0GyXaXftFaXKzQ4ub1OqBcDiyYTv8jiILet/8z5Yl2IqqpF03HHBkAya7q8/WFsJ/QDCTBKsFao/rH8EFqHiXwyMfHkrcnQu3Ga3at6QJJs+CdzYTsfn jomoon@jomoon.jtest.pivotal.io
ssh_pwauth: False
timezone: Aisa/Seoul
_EOF_

    echo "instance-id: $1; local-hostname: $1" > $META_DATA

    echo "$(date -R) Copying template image..."
    sudo cp $IMAGE $DISK

    # Create CD-ROM ISO with cloud-init config
    echo "$(date -R) Generating ISO for cloud-init..."
    echo "sudo genisoimage -input-charset utf-8 -output $CI_ISO -volid cidata -joliet -r $USER_DATA $META_DATA &>> $DIR/$1/$1.log"
    sudo genisoimage -input-charset utf-8 -output $CI_ISO -volid cidata -joliet -r $USER_DATA $META_DATA &>> $DIR/$1/$1.log

    echo "$(date -R) Installing the domain and adjusting the configuration..."
    echo "[INFO] Installing with the following parameters:"
    echo "virt-install --import --name $1 --ram $MEM --vcpus $CPUS --disk $DISK,format=qcow2,bus=virtio --disk $CI_ISO,device=cdrom --network bridge=virbr0,model=virtio --os-type=linux --os-variant=rhel7 --noautoconsole"

    sudo virt-install --import --name $1 --ram $MEM --vcpus $CPUS --disk $DISK,format=qcow2,bus=virtio --disk $CI_ISO,device=cdrom \
    --network bridge=br0,model=virtio --network bridge=virbr1,model=virtio --os-type=linux --os-variant=rhel7 --noautoconsole

    CNT=1
    for CONT in $(sudo virsh dumpxml $1 | sed -n -e "/mac address/,/source bridge/p" | grep -v 'model\|interface\|function' | awk -F\' '/mac address/,/source/ {print $2}')
    do
        if [ $CNT == 3 ]; then
            MAC=$CONT
        elif [ $CNT == 4 ]; then
            VIF=$CONT
            while true
            do
                IP=$(grep -B1 $MAC /var/lib/libvirt/dnsmasq/$VIF.status | head -n 1 | awk '{print $2}' | sed -e s/\"//g -e s/,//)
                # echo $IP
                if [ "$IP" = "" ]; then
                    sleep 1
                else
                    break
                fi
            done
        fi
        CNT=$(( CNT + 1 ))
    done
    echo ""

    # Eject cdrom
    echo "$(date -R) Cleaning up cloud-init..."
    sudo virsh change-media $1 hda --eject --config >> $DIR/$1/$1.log

    # Remove the unnecessary cloud init files
    # sudo rm $USER_DATA $CI_ISO

    echo "$(date -R) DONE. SSH to $1 using $IP, with  username 'jomoon'."

popd > /dev/null
