#!/usr/bin/python
#
#
#
# jomoon@pivotal.io
#

import os, sys, time, getpass, re
from datetime import datetime,timedelta
from ruamel.yaml import YAML

yaml = YAML()
input_file = 'gpdb5_config.yaml'
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

# Directory to store images
BASE_DIR = "/storage"

# Cloud init files
USER_DATA = "user-data"
META_DATA = "meta-data"

# Bridge for VMs (default on Fedora is virbr0)
BRIDGE = "virbr1"
CI_ISO = ""
iV = ""

class InstallVMs():

    def __init__(self):
        self.initvar =""

    def initialize_domain(PREFIX, BASE_DIR):
        global WORK_DIR
        WORK_DIR = BASE_DIR + "/" + PREFIX
        osr = os.system("virsh dominfo " + PREFIX + " > /dev/null 2>&1")
        # print osr
        # sys.exit(2)
    
        if osr == 0:
            print "[WARNING] " + PREFIX + " already exists.  "
            p = getpass.getpass(prompt='Do you want to overwrite ' + PREFIX + ' [y/N]? ')
            if p.lower() == 'y':
                print ''
            else:
                print '\nNot overwriting ' + PREFIX +'. Exiting...'
                sys.exit(2)
    
        # Start clean
        os.system('rm -rf ' + WORK_DIR )
        os.system('mkdir -p ' + WORK_DIR )
    
        # Start pushd
        # cwd = os.getcwd()
        # os.chdir( BASE_DIR + "/" + PREFIX)
    
        # Create log file
        os.system('sudo touch ' + WORK_DIR + '/' + PREFIX + '.log')
        print str(datetime.now())+" Destroying the " + PREFIX + " domain (if it exists)..."
    
        # Remove domain with the same name
        os.system("sudo virsh destroy " + PREFIX + " >> " + WORK_DIR + "/" + PREFIX + ".log 2>&1")
        os.system("sudo virsh undefine " + PREFIX + " >> " + WORK_DIR + "/" + PREFIX + ".log 2>&1")
    
    
    def config_cloudinit(PREFIX, USER_DATA, IPADDR):
        fd = open(WORK_DIR + "/" + USER_DATA, 'w')
        fd.write("#cloud-config\n")
        fd.write("preserve_hostname: False\n")
        fd.write("hostname: " + PREFIX + "\n")
        fd.write("fqdn: " + PREFIX + ".jtest.pivotal.io\n")
        fd.write("network: {config: disabled}\n")
        fd.write("bootcmd:\n")
        fd.write("  - set -x; echo '#user-data/bootcmd:' >> /etc/sysconfig/network-scripts/ifcfg-eth0\n")
        fd.write("  - set -x; sed -i -e '/^BOOTPROTO/ s/dhcp/static/g' -e '/PERSISTENT_DHCLIENT/d' /etc/sysconfig/network-scripts/ifcfg-eth0\n")
        fd.write("  - set -x; echo 'IPADDR=" + IPADDR + "' >> /etc/sysconfig/network-scripts/ifcfg-eth0\n")
        fd.write("  - set -x; echo 'NETMASK=255.255.255.0' >> /etc/sysconfig/network-scripts/ifcfg-eth0\n")
        fd.write("  - set -x; echo 'GATEWAY=192.168.0.1' >> /etc/sysconfig/network-scripts/ifcfg-eth0\n")
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
        fd.write("ssh_pwauth: False\n")
        fd.write("timezone: Aisa/Seoul\n")
        fd.close()
    
    #    fd.write("- [users-groups,always]\n")
    #    fd.write("users:\n")
    #    fd.write(" - name: jomoon\n")
    #    fd.write("   groups: [ wheel ]\n")
    #    fd.write("   sudo: [ \"ALL=(ALL) NOPASSWD:ALL\" ]\n")
    #    fd.write("   shell: /bin/bash\n")
    #    fd.write("   ssh-authorized-keys:\n")
    #    fd.write("      - ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDEv4Q0604MrukxXF7d4RKbLOrfdo29vSLRXTxdNBFFDxZjkyKqq3OnRHboAMc57P74vFDGA/sOJ8Qsqrbo7G/SD4So07RO+PGpGObCkgMtbZoQUC/uDI9W5Ae6fS+Uz8td8GaYz9D1I53ZuHQ+Pzzuu2h43HwWrtgTIdUTAZB7fJhpwASrwb5iLy2EGf7IacBUl/R7G2SNmcTN3i9L2JMVruvnEt1iVU6t0GyXaXftFaXKzQ4ub1OqBcDiyYTv8jiILet/8z5Yl2IqqpF03HHBkAya7q8/WFsJ/QDCTBKsFao/rH8EFqHiXwyMfHkrcnQu3Ga3at6QJJs+CdzYTsfn jomoon@jomoon.jtest.pivotal.io\n")
    #    fd.write("network: {config: disabled}\n")
    
    def create_image(PREFIX, META_DATA, MEMORY, CPUS, TARGET_IMAGE, OSVAR, BASE_IMAGE):
    
        os.system("sudo echo instance-id: " + PREFIX + "\; local-hostname: " + PREFIX + " > " + WORK_DIR + "/" + META_DATA)
        print str(datetime.now()) + " Copying template image..."
    
        os.system('sudo cp ' + BASE_DIR + '/' + BASE_IMAGE + ' ' + BASE_DIR + '/' + TARGET_IMAGE)
    
        # Create CD-ROM ISO with cloud-init config
        print str(datetime.now()) + " Generating ISO for cloud-init..."
        os.system("sudo genisoimage -input-charset utf-8 -output " + WORK_DIR + "/" + CI_ISO + " -volid cidata -joliet -r " + WORK_DIR + "/" + USER_DATA + " " + WORK_DIR + "/" + META_DATA + " &>> " + WORK_DIR + "/" + PREFIX + ".log")
    
        print str(datetime.now()) + " Installing the domain and adjusting the configuration..."
        print "[INFO] Installing with the following parameters:"
        os.system("sudo virt-install --import --name " + PREFIX + " --ram " + str(MEMORY) + " --vcpus " + str(CPUS) + " --disk " + BASE_DIR + "/" + TARGET_IMAGE + ",format=qcow2,bus=virtio --disk " + WORK_DIR + "/" + CI_ISO + ",device=cdrom --network bridge=br0,model=virtio --network bridge=" + BRIDGE + ",model=virtio --os-type=linux --os-variant=" + OSVAR + " --noautoconsole")
    
    
    def wait_for_complete(PREFIX):
        global VIF
        COUNT=1
        OUTPUT = os.popen("sudo virsh dumpxml " + PREFIX + " | sed -n -e '/mac address/,/source bridge/p' | grep -v 'model|interface|function' | awk -F\\' '/mac address/,/source/ {print $2}'")
        for LINE in OUTPUT.readlines():
            if ( COUNT == 3 ):
                MACADDR=LINE.rstrip('\n')
            elif ( COUNT == 4 ):
                VIF=LINE.rstrip('\n')
            COUNT = COUNT + 1
        OUTPUT.close()
    
        # Need to check why the following is not working
        #COUNT=1
        #while True:
        #    OUTPUT = os.popen("grep -B1 " + MACADDR +" /var/lib/libvirt/dnsmasq/" + VIF + ".status | head -n 1 | awk '{print $2}' | sed -e s/\\\"//g -e s/,//").readlines()
        #    for line in OUTPUT:
        #        if re.search(str(MACADDR), str(line)):
        #            print str(COUNT) + ' : found a match!' + line
        #            COUNT = 0
        #            break
        #        else:
        #            continue
        #            # print str(COUNT) + ' : no match'
        #        COUNT = COUNT + 1
        #    if COUNT == 0:
        #        break
    
        BCOUNT=1
        while True:
            with open("/var/lib/libvirt/dnsmasq/" + VIF + ".status", "r") as file_to_read:
                COUNT=1
                for line in file_to_read:
                    if re.search(str(MACADDR), str(line)):
                        # print str(COUNT) + ' : found a match!' + line
                        BCOUNT = 0
                        OUTPUT = os.popen("grep -B1 " + MACADDR +" /var/lib/libvirt/dnsmasq/" + VIF + ".status | head -n 1 | awk '{print $2}' | sed -e s/\\\"//g -e s/,//").readlines()
                        for CONTENT in OUTPUT:
                            if CONTENT != "":
                                global VIP
                                VIP = CONTENT.rstrip('\n')
                        break
                    else:
                        continue
                        print str(COUNT) + ' : no match'
                    COUNT = COUNT + 1
            if BCOUNT == 0:
                break
    
    
    def cleanup_cloudinit(PREFIX, BASE_DIR, USER_DATA, CI_ISO, VIP):
        # Eject cdrom
        print str(datetime.now()) + " Cleaning up cloud-init..."
        os.system("sudo virsh change-media " + PREFIX + " hda --eject --config >> " + WORK_DIR + "/"+ PREFIX +".log")
        # Remove the unnecessary cloud init files
        os.system("sudo rm " + WORK_DIR + "/" + USER_DATA + " " + WORK_DIR + "/" + CI_ISO)
        print str(datetime.now()) + " DONE. SSH to " + PREFIX + " using " + VIP + ", with username 'jomoon'."


    # Main fuctions
    for key, value in yaml.load(open(input_file)).items():
        # print("key:", key)
        if key == "mst":
            for key in value:
                if key == "active" or "standby":
                    for key1, value1 in value[key].items():
                        if key1 == 'hostname':
                            PREFIX = value1
                        if key1 == 'memory':
                            MEMORY = value1
                        if key1 == 'cpus':
                            CPUS = value1
                        if key1 == 'ipaddr':
                            IPADDR = value1
                        if key1 == 'osvar':
                            OSVAR = value1
                        if key1 == 'base_image':
                            BASE_IMAGE = value1
    
                        CI_ISO = PREFIX + "-cidata.iso"
                        TARGET_IMAGE = PREFIX + ".qcow2"
    
                    print PREFIX, MEMORY, CPUS, IPADDR, OSVAR, BASE_IMAGE, CI_ISO, TARGET_IMAGE 

                    iV.initialize_domain(PREFIX, BASE_DIR)
                    iV.config_cloudinit(PREFIX, USER_DATA, IPADDR)
                    iV.create_image(PREFIX, META_DATA, MEMORY, CPUS, TARGET_IMAGE, OSVAR, BASE_IMAGE)
                    iV.wait_for_complete(PREFIX)
                    iV.cleanup_cloudinit(PREFIX, BASE_DIR, USER_DATA, CI_ISO, VIP)
                    sys.exit(1)
                    
    
        elif key == "sgmt":
            for key in value:
                if key != "":
                    for key1, value1 in value[key].items():
                        if key1 == 'hostname':
                            PREFIX = value1
                        if key1 == 'memory':
                            MEMORY = value1
                        if key1 == 'cpus':
                            CPUS = value1
                        if key1 == 'ipaddr':
                            IPADDR = value1
                        if key1 == 'osvar':
                            OSVAR = value1
                        if key1 == 'base_image':
                            BASE_IMAGE = value1
    
                        CI_ISO = PREFIX + "-cidata.iso"
                        TARGET_IMAGE= PREFIX + ".qcow2"
    
                    iV.initialize_domain(PREFIX, BASE_DIR)
                    iV.config_cloudinit(PREFIX, USER_DATA, IPADDR)
                    iV.create_image(PREFIX, META_DATA, MEMORY, CPUS, TARGET_IMAGE, OSVAR, BASE_IMAGE)
                    iV.wait_for_complete(PREFIX)
                    iV.cleanup_cloudinit(PREFIX, BASE_DIR, USER_DATA, CI_ISO, VIP)


if __name__ == "__main__":

    iV = installVMs()
