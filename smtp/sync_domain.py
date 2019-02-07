#!/usr/bin/python

import MySQLdb
import sys

sys.path.append("/root/library/Python/Python1.1")
from LogClass import *
from PropClass import *

def logIt (logMsg=None):
    if (logMsg is None): return
    Log.log(logMsg, 'sync_domain')

def main():
    db = MySQLdb.connect('localhost', 'hdev', 'dkandldbdjqtdj', 'smtp').cursor()
    db.execute("TRUNCATE smtp_domain")

    serverList = ['webmail-003', 'webmail-002', 'webmail-001']
    prop = Properties()
    cafe24Domain = prop.get('domain')
    sdbUser = prop.get('db.webmail.user')
    sdbPasswd = prop.get('db.webmail.password')
    sdbDb = 'webmail'

    success = 0
    failure = 0

    for server in serverList:
        try:
            sdbHost = '%s.%s' % (server, cafe24Domain)
            sdb = MySQLdb.connect(sdbHost, sdbUser, sdbPasswd, sdbDb).cursor()
            query = "SELECT WA.admin_id AS userId, WD.punycode AS domain FROM webmail_admin WA, webmail_domain WD WHERE WA.idx=WD.admin_idx AND WA.server='%s'" % sdbHost
            sdb.execute(query)
            rows = sdb.fetchall()

            for row in rows:
                try:
                    userId, domain = tuple(row)
                    insertQuery = "INSERT INTO smtp_domain (userId, domain, regDate) VALUES ('%s', '%s', NOW())" % (userId, domain)
                    db.execute(insertQuery)
                except Exception, err:
                    #logIt('[Error] %s, %s' % (str(err), userId))
                    failure += 1
                else:
                    success += 1
            
            sdb.close()

        except Exception, err:
            logIt('[Error] %s, %s' % (server, str(err)))

    message = '[Result] success=%s, failure=%s\n\n' % (success, failure)
    logIt(message)
    print message


if __name__ == '__main__':
    main()
