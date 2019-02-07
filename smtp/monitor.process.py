#!/usr/bin/python
"""
Usage: %(program)s DAEMON_PROGRAM_PROPERTIES_NAME
for example: $ %(program)s daemons.pcdnname
        
date   : 2006.11
author : unturtle
"""
import os, sys, re

sys.path.append('/root/library/Python/Python1.1') 

from MonitorClass import *
from PropClass import Properties

class Proc:
    """ Super Class """
    def __init__(self, prop_daemon_name):
        Monitor.isBlock()

        prop = Properties()
        self.daemons = prop.get(prop_daemon_name)
       
        if type(self.daemons) != type([]):
            tempData = self.daemons
            self.daemons = []
            self.daemons.append(tempData)

    def chkproc(self):
        for daemon in self.daemons:
            # print "daemon : " + daemon
            if daemon is None or daemon == "":
                continue

            args = daemon.split('_')

            result = Monitor.checkProcess(args[0])
			
            if result is None:
                daemon = ""
                for i in args:
                   daemon += i+" "
                print self.execute(daemon)
                print daemon
			
    def execute(self, daemon):
        try:
            os.system(daemon)
            print 'Restart %s' % (daemon)
        except:
            raise Exception, '%s : Proc.execute() : %s' % (sys.exc_info()[0], sys.exc_info()[1])


class MyProc(Proc):
    def execute(self, daemon):
        from UtilClass import mysms
        try:
#            mysms('%s stop!!!!' % daemon)
            print '%s stop!!!!' % daemon
        except:
            raise Exception, '%s : MyProc.execute() : %s' % (sys.exc_info()[0], sys.exc_info()[1])


def main():
    try:
        mon = MyProc(sys.argv[1])
        mon.chkproc()

    except Exception ,msg:
		print "Exception : ", msg


if __name__ == '__main__':
    main()
