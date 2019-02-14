#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# jomoon@pivotal.io
#

import os, sys, time, getpass, fileinput, re, glob, getopt
from datetime import datetime,timedelta
from ruamel.yaml import YAML

# brew install libyaml
# brew reinstall libyaml
# pip install virtualenv
# pip install ruamel_yaml==0.15.87

yaml = YAML()
input_file = 'vms_vmware_config.yml'

iV = ""
PREFIX = ""
MEMORY = ""
CPUS = ""
IPADDR = ""
OSVAR = ""
BASE_IMAGE = ""
IP = ""
MACADDR = ""
OUTPUT = ""
VIP = ""
VIF = ""
CI_ISO = ""
HOST_OS = ""
PROD = ""
USER = ""
VALID_IP_ADDR = ""

# Cloud init files
USER_DATA = "user-data"
META_DATA = "meta-data"

# Bridge for VMs (default on Fedora is virbr0)
BRIDGE = "virbr1"

class InstallVMs():

    def __init__(self):

        self.initvar = ""
        self.IS_VALID = 0
        self.IP = ""

    # vmware-vdiskmanager -e file location
    # /Users/pivotal/Documents/Virtual\ Machines.localized/
    # ./vmware-vdiskmanager -e /Users/pivotal/Documents/Virtual\ Machines.localized/CentOS7.5-temp.vmwarevm/Virtual\ Disk.vmdk
    # Disk chain is consistent.
    #
    # Pivotals-MacBook-Pro-4:Library root# ./vmrun list
    # Total running VMs: 0

    def initialize_domain( self, PREFIX, BASE_DIR, HOST_OS, PROD, CMD_BASE_DIR, IMG_BASE_DIR, IMG_FILE_NAME ):

        # 이미지 없을때 Error 처리할것
        osr = os.system(CMD_BASE_DIR + "vmware-vdiskmanager -e " + IMG_BASE_DIR + PREFIX + "/" + PREFIX + IMG_FILE_NAME + " > /dev/null 2>&1")
        print CMD_BASE_DIR + "vmware-vdiskmanager -e " + IMG_BASE_DIR + PREFIX + "/" + PREFIX + IMG_FILE_NAME
        # print osr

        if osr == 0:
            print "[WARNING] " + PREFIX + " already exists.  "
            p = getpass.getpass(prompt='Do you want to overwrite ' + PREFIX + ' [y/N]? ')
            if p.lower() == 'y':
                print ''
            else:
                print '\nNot overwriting ' + PREFIX +'. Exiting...'
                sys.exit(2)

        # vmrun stop /storage/centos610-temp/centos610.vmx
        # vmrun deleteVM /storage/centos610-temp/centos610.vmx
        #
        # The below error appear when clicking it's menu on UI.
        # Error: Insufficient permissions

        # /home/jomoon/.vmware/inventory.vmls
        # "<none>" ./inventory.vmls:vmlist5.config = "/storage/centos610-temp/centos610.vmx"
        # should be removed ./inventory.vmls:vmlist5.DisplayName = "centos610-temp"
        # should be removed ./inventory.vmls:index1.id = "/storage/centos610-temp/centos610.vmx"

        # Create log file
        os.system('sudo mkdir ' + WORK_DIR + PREFIX )
        os.system('sudo touch ' + WORK_DIR + '/' + PREFIX + '.log')
        print str(datetime.now()) + " Destroying the " + PREFIX + " domain (if it exists)..."


        # Need to handle error when no images
        os.system(CMD_BASE_DIR + "vmrun stop " + IMG_BASE_DIR + PREFIX + "/" + PREFIX + ".vmx > /dev/null 2>&1")
        os.system(CMD_BASE_DIR + "vmrun deleteVM " + IMG_BASE_DIR + PREFIX + "/" + PREFIX + ".vmx > /dev/null 2>&1")


    def config_cloudinit(self, PREFIX, WORK_DIR, USER_DATA, IPADDR):

        fd = open(WORK_DIR + "/" + PREFIX + "/" + USER_DATA, 'w')
        fd.write("#cloud-config\n")
        fd.write("preserve_hostname: False\n")
        fd.write("hostname: " + PREFIX + "\n")
        fd.write("fqdn: " + PREFIX + ".jtest.pivotal.io\n")
        fd.write("network: {config: disabled}\n")
        fd.write("bootcmd:\n")
        fd.write("  - set -x; echo '#user-data/bootcmd:' >> /etc/sysconfig/network-scripts/ifcfg-eth0\n")
        fd.write("  - set -x; sed -i -e '/^BOOTPROTO/ s/dhcp/static/g' -e '/PERSISTENT_DHCLIENT/d' /etc/sysconfig/network-scripts/ifcfg-eth0\n")
        fd.write("  - set -x; echo 'DEVICE=eth0' >> /etc/sysconfig/network-scripts/ifcfg-eth0\n")
        fd.write("  - set -x; echo 'TYPE=Ethernet' >> /etc/sysconfig/network-scripts/ifcfg-eth0\n")
        fd.write("  - set -x; echo 'IPADDR=" + IPADDR + "' >> /etc/sysconfig/network-scripts/ifcfg-eth0\n")
        fd.write("  - set -x; echo 'NETMASK=255.255.255.0' >> /etc/sysconfig/network-scripts/ifcfg-eth0\n")
        fd.write("  - set -x; echo 'DNS1=8.8.8.8' >> /etc/sysconfig/network-scripts/ifcfg-eth0\n")
        fd.write("  - set -x; echo 'ONBOOT=yes' >> /etc/sysconfig/network-scripts/ifcfg-eth0\n")
        fd.write("  - set -x; echo 'NM_CONTROLLED=no' >> /etc/sysconfig/network-scripts/ifcfg-eth0\n")
        fd.write("  - ifdown eth0\n")
        fd.write("  - ifup eth0\n")
        fd.write("# Remove cloud-init when finished with it\n")
        fd.write("runcmd:\n")
        fd.write("  - [ yum, -y, remove, cloud-init ]\n")
        fd.write("output:\n")
        fd.write("  all: \">> /var/log/cloud-init.log\"\n")
        fd.write("ssh_svcname: ssh\n")
        fd.write("ssh_deletekeys: True\n")
        fd.write("ssh_genkeytypes: ['rsa', 'ecdsa']\n")
        fd.write("ssh_authorized_keys:\n")
        fd.write("  - ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDEv4Q0604MrukxXF7d4RKbLOrfdo29vSLRXTxdNBFFDxZjkyKqq3OnRHboAMc57P74vFDGA/sOJ8Qsqrbo7G/SD4So07RO+PGpGObCkgMtbZoQUC/uDI9W5Ae6fS+Uz8td8GaYz9D1I53ZuHQ+Pzzuu2h43HwWrtgTIdUTAZB7fJhpwASrwb5iLy2EGf7IacBUl/R7G2SNmcTN3i9L2JMVruvnEt1iVU6t0GyXaXftFaXKzQ4ub1OqBcDiyYTv8jiILet/8z5Yl2IqqpF03HHBkAya7q8/WFsJ/QDCTBKsFao/rH8EFqHiXwyMfHkrcnQu3Ga3at6QJJs+CdzYTsfn jomoon@jomoon.jtest.pivotal.io\n")
        fd.write("ssh_pwauth: True\n")
        fd.write("timezone: Aisa/Seoul\n")
        fd.close()


    def create_image( self, PREFIX, WORK_DIR, META_DATA, MEMORY, CPUS, TARGET_IMAGE, OSVAR, BASE_IMAGE, HOST_OS, PROD, CMD_BASE_DIR, IMG_BASE_DIR, IMG_FILE_NAME ):

        print "sudo echo instance-id: " + PREFIX + "\; local-hostname: " + PREFIX + " > " + WORK_DIR + PREFIX + "/" + META_DATA
        os.system("sudo echo instance-id: " + PREFIX + "\; local-hostname: " + PREFIX + " > " + WORK_DIR + PREFIX + "/" + META_DATA)
        print str(datetime.now()) + " Copying template image..."


        # https://communities.vmware.com/thread/515096

        if HOST_OS == "mac":
            os.system("mkdir " + IMG_BASE_DIR + PREFIX + ".vmwarevm")
            IDENT = ".vmwarevm/"
        elif HOST_OS == "rhel" or HOST_OS == "centos":
            os.system("mkdir " + IMG_BASE_DIR + PREFIX )
            IDENT = "/"

        print ""
        print "Create Dir " + IMG_BASE_DIR + PREFIX + IDENT + PREFIX
        print "Cloning VM ..."
        # *************** Need to be modified , source and destination

        print CMD_BASE_DIR + "vmrun -T " + PROD + " clone " + IMG_BASE_DIR + BASE_IMAGE + IDENT + BASE_IMAGE + ".vmx "  + IMG_BASE_DIR + PREFIX + IDENT + PREFIX + ".vmx full -cloneName=" + PREFIX
        os.system( CMD_BASE_DIR + "vmrun -T " + PROD + " clone " + IMG_BASE_DIR + BASE_IMAGE + IDENT + BASE_IMAGE + ".vmx "  + IMG_BASE_DIR + PREFIX + IDENT + PREFIX + ".vmx full -cloneName=" + PREFIX )

        # https://www.computerhope.com/issues/ch001721.htm
        # /home/jomoon/.vmware/preferences


        # Create CD-ROM ISO with cloud-init config
        print str(datetime.now()) + " Generating ISO for cloud-init..."

        if HOST_OS == "mac":
            os.system( "hdiutil makehybrid -o " + WORK_DIR + CI_ISO + " -hfs -joliet -iso -default-volume-name cidata " + BASE_DIR + PREFIX )
        elif HOST_OS == "rhel" or HOST_OS == "centos":
            os.system( CMD_BASE_DIR + "genisoimage -input-charset utf-8 -output " + WORK_DIR + "/" + CI_ISO + " -volid cidata -joliet -r " + WORK_DIR + "/" + USER_DATA + " " + WORK_DIR + "/" + META_DATA + " &>> " + WORK_DIR + "/" + PREFIX + ".log")

        print IMG_BASE_DIR + PREFIX + IDENT + PREFIX + ".vmx"

        # Need to trim line added by this function.
        for line in fileinput.input( glob.glob(IMG_BASE_DIR + PREFIX + IDENT + PREFIX + ".vmx"), inplace=1 ):
            if re.search("^sata0:1", line):
                line = re.sub('^sata0:1','#sata0:1', line.rstrip('\r\n'))
            print(line)

        fp = open( IMG_BASE_DIR + PREFIX + IDENT + PREFIX + ".vmx", 'a' )
        fp.write("sata0:1.deviceType = \"cdrom-image\"\n")
        fp.write("sata0:1.fileName = \"" + WORK_DIR + CI_ISO +"\"\n")
        fp.write("sata0:1.present = \"TRUE\"\n")
        fp.write("sata0:1.connectionStatus = \"4\"\n")
        fp.close()


        # In order to appear it on UI, it should be started with the following command
        os.system(CMD_BASE_DIR + "vmrun -T ws start " + IMG_BASE_DIR + PREFIX + "/" + PREFIX + ".vmx")

        # http://talk.manageiq.org/t/cloud-init-on-vmware-provider/1254/13 - Read comment of ramrexx

        print str(datetime.now()) + " Installing the domain and adjusting the configuration..."
        print "[INFO] Installing with the following parameters:"


    def wait_for_complete(self, PREFIX, HOST_OS, PROD, CMD_BASE_DIR, IMG_BASE_DIR, IMG_FILE_NAME ):
        global VIF
        while True:
            OUTPUT = os.popen("sudo vmrun -T ws getGuestIPAddress " + IMG_BASE_DIR + PREFIX + "/" + PREFIX + ".vmx")
            for CONTENT in OUTPUT:
                VALID_IP_ADDR = re.match("^([1][0-9][0-9].|^[2][5][0-5].|^[2][0-4][0-9].|^[1][0-9][0-9].|^[0-9][0-9].|^[0-9].)([1][0-9][0-9].|[2][5][0-5].|[2][0-4][0-9].|[1][0-9][0-9].|[0-9][0-9].|[0-9].)([1][0-9][0-9].|[2][5][0-5].|[2][0-4][0-9].|[1][0-9][0-9].|[0-9][0-9].|[0-9].)([1][0-9][0-9]|[2][5][0-5]|[2][0-4][0-9]|[1][0-9][0-9]|[0-9][0-9]|[0-9])$",CONTENT)
                if VALID_IP_ADDR:
                    # print VALID_IP_ADDR.group(1)+VALID_IP_ADDR.group(2)+VALID_IP_ADDR.group(1)+VALID_IP_ADDR.group(1)
                    IP = CONTENT
                    self.IS_VALID = 1
                    break
                else:
                    continue

            if self.IS_VALID == 1:
                break

        return IP

    # If there are no command to eject iso image, just remove it in the vmx file
    # Otherwise just eject cdrom in running virtual machine by umount command and then remove it in the vmx file


    def disable_cloudinit( self, PREFIX, BASE_DIR, USER_DATA, CI_ISO, VIP, HOST_OS, PROD, CMD_BASE_DIR, IMG_BASE_DIR, IMG_FILE_NAME ):

        print str(datetime.now()) + " Cleaning up cloud-init..."

        # vmrun -T ws -gu root -gp rmsidwoalfh runScriptInGuest /storage/centos610-temp/centos610.vmx /bin/bash "touch /etc/cloud/cloud-init.disabled"
        # Eject cdrom
        # os.system("sudo virsh change-media " + PREFIX + " hda --eject --config >> " + WORK_DIR + "/"+ PREFIX +".log")
        # Remove the unnecessary cloud init files
        # os.system("sudo rm " + WORK_DIR + "/" + PREFIX + "/" + USER_DATA + " " + WORK_DIR + "/" + CI_ISO)


def usage():
    print "check your command"

try:
    opts, args = getopt.getopt(sys.argv[1:], "u:o:p:", ["user","os","product"])
except getopt.GetoptError:
    usage()
    sys.exit(2)

for opt, arg in opts:
    if opt in ("-u", "--user"):
        USER = arg
    if opt in ("-o", "--os"):
        HOST_OS = arg
    if opt in ("-p", "--product"):
        PROD = arg


if HOST_OS == "rhel" or HOST_OS == "centos":
    # Directory to store images
    BASE_DIR = "/storage/"
    WORK_DIR = "/home/" + USER + "/"
    if PROD == "fusion":
        IMG_BASE_DIR = BASE_DIR
        CMD_BASE_DIR = "/usr/bin/"
        IMG_FILE_NAME = ".vmdk"
    elif PROD == "ws":
        IMG_BASE_DIR = BASE_DIR
        CMD_BASE_DIR = "/usr/bin/"
        IMG_FILE_NAME = ".vmdk"
    else:
        print "No product at rhel or centos"
        sys.exit(2)
elif HOST_OS == "mac":
    # Directory to store images
    WORK_DIR = "/Users/" + USER + "/"
    BASE_DIR = WORK_DIR
    if PROD == "fusion":
        IMG_BASE_DIR = BASE_DIR + "Documents/Virtual\ Machines.localized/"
        CMD_BASE_DIR = "/Applications/VMware\ Fusion.app/Contents/Library/"
        IMG_FILE_NAME = ".vmwarevm/" + PREFIX + "/Virtual\ Disk.vmdk"
    elif PROD == "ws":
        IMG_BASE_DIR = "/Users/pivotal/Documents/Virtual\ Machines.localized/"
        CMD_BASE_DIR = "/Applications/VMware\ Workstation.app/Contents/Library/"
        IMG_FILE_NAME = ".vmwarevm/" + PREFIX + "/Virtual\ Disk.vmdk"
    else:
        print "No product at macos"
        sys.exit(2)
else:
    print "None OS or Product"
    usage()
    sys.exit(2)


if __name__ == "__main__":

    iV = InstallVMs()

    # Main fuctions
    for key, value in yaml.load(open(input_file)).items():
        for key in value:
            if key == 'hostname':
                PREFIX = value[key]
            if key == 'memory':
                MEMORY = value[key]
            if key == 'cpus':
                CPUS = value[key]
            if key == 'ipaddr':
                IPADDR = value[key]
            if key == 'osvar':
                OSVAR = value[key]
            if key == 'base_image':
                BASE_IMAGE = value[key]

        CI_ISO = PREFIX + "-cidata.iso"
        TARGET_IMAGE = PREFIX + ".qcow2"

        # print PREFIX, MEMORY, CPUS, IPADDR, OSVAR, BASE_IMAGE, CI_ISO, TARGET_IMAGE, HOST_OS, PROD, CMD_BASE_DIR, IMG_BASE_DIR, IMG_FILE_NAME

        iV.initialize_domain( PREFIX, BASE_DIR, HOST_OS, PROD, CMD_BASE_DIR, IMG_BASE_DIR, IMG_FILE_NAME )
        iV.config_cloudinit( PREFIX, WORK_DIR, USER_DATA, IPADDR )
        iV.create_image( PREFIX, WORK_DIR, META_DATA, MEMORY, CPUS, TARGET_IMAGE, OSVAR, BASE_IMAGE, HOST_OS, PROD, CMD_BASE_DIR, IMG_BASE_DIR, IMG_FILE_NAME )
        IP = iV.wait_for_complete( PREFIX, PROD, HOST_OS, CMD_BASE_DIR, IMG_BASE_DIR, IMG_FILE_NAME )
        iV.disable_cloudinit( PREFIX, BASE_DIR, USER_DATA, CI_ISO, VIP, HOST_OS, PROD, CMD_BASE_DIR, IMG_BASE_DIR, IMG_FILE_NAME )

        IP = re.sub(r'^\s+$|\n', '', IP)

        print str(datetime.now()) + " - DONE. SSH to " + PREFIX + " using " + IP + " with username '" + USER + "'."
        sys.exit(1)
