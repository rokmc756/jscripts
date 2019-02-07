#! /usr/bin/python
import sys, getopt
from ovirtsdk.api import API
from ovirtsdk.xml import params

VERSION = params.Version(major='4', minor='1')

def help():
  print "Print help usage"
  sys.exit(2)

def main():

  try:
    opts, args = getopt.getopt(sys.argv[1:],"d:s:v:h",["datacenter=","storagedomain=","verbose","help"])
  except getopt.GetoptError as err:
    print str(err)
    help()
    sys.exit(2)

  for opt, arg in opts:
    # print opt, arg
    if opt in ('-d', '--datacenter'):
        dc_name = arg
    elif opt in ('-s', '--storagedomain'):
        sd_name = arg
    elif opt in ('-v', '--verbose'):
        verbose = True

  URL =           'https://rhv4-manager.jtest.redhat.com/ovirt-engine/api'
  USERNAME =      'admin@internal'
  PASSWORD =      'redhat'

  api = API ( url=URL,username=USERNAME, password=PASSWORD, insecure=True)

  for dc in api.datacenters.list(name=dc_name):
    for sd in dc.storagedomains.list(name=sd_name):
      for disk in sd.disks.list():
        if disk.status.get_state() == "ok": # Note : disk.status is class not a variable. You could find attributes of class with dir() method like dir(disk.status)
          print disk.id, disk.name

  api.disconnect()

if __name__ == '__main__':
  main()
