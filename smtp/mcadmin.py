#! /usr/bin/env python2.3
# -*- coding: utf-8 -*-
# 
# 
# 
# 작성일 : 2007년 5월 25일 
# 작성인 : 심플렉스인터넷(주)
#		   서버개발팀  문 종 영
#  
#  
#  
# 1차 수정
#  수정일 : 2007년 7월 2일
#  수정인 : 문 종 영
#  
#  
#  수정내용
#  
#  - email -
#    key   : id@example.com
#    value : 제한수|무제한여부|시작시간
#  - domain -
#    key   : example.com
#    value : 제한수|무제한여부|시작시간
#  
#  1. 특정 이메일 레코드 삭제 기능
#  2. 특정 도메인 레코드 삭제 기능
#  3. 모든 데이터 소멸 기능
#  4. 특정 이메일 레코드 발송 제한수, 무제한 발송 toggle, 날짜 수정 기능
#  5. 특정 도메인 레코드 발송 제한수, 무제한 발송 toggle, 날짜 수정 기능
#  6. 전체 레코드 보기 기능
#  7. 특정 이메일, 도메인 상태 보기
#  8. 전체 레코드를 가져오기 위한 MySQLdb 파이썬 코드 추가

import sys, asyncore, threading, socket, time, StringIO
import esmtpd
import memcache
import re
import time, getopt
import MySQLdb

DOMAIN_DEFAULT="40000|0|F|"+time.strftime('%Y%m%d')
EMAIL_DEFAULT="400|0|F|"+time.strftime('%Y%m%d')

mm = memcache.Client(['127.0.0.1:11211'],debug = 0)


# 모든 데이터 소멸
def all_data_flush():
	print mm.flush_all()

# 메일발송 제한 풀기
def modify_restriction(rkey):
	cvalue = mm.get(rkey)

	if cvalue == None:
		print rkey+": not found record"
	else:
		arr_cval = cvalue.split('|')

		if arr_cval[1] == 'T':
			arr_cval[1] = 'F'
			message = "restriction field is changed to 'F'"
		else:
			arr_cval[1] = 'T'
			message = "restriction field is changed to 'T'"

		mm.set(rkey, arr_cval[0]+'|'+arr_cval[1]+'|'+arr_cval[2])

		print message

# 레코드 가져오기
def get_record(idx):
	cvalue = mm.get(idx)
	return cvalue

# 만료날짜 수정 
def modify_date(domain, mdate):
	cvalue = mm.get(domain)

	if cvalue == None:
		print domain+": not found record"
	else:
		arr_cval = cvalue.split('|')
		mm.set(domain, arr_cval[0]+'|'+arr_cval[1]+'|'+mdate)
		print "date is changed to " + mdate

# 메일제한수 수정
def modify_mnum(domain, mnum):
	cvalue = mm.get(domain)

	if cvalue == None:
		print domain+": not found record"
	else:
		arr_cval = cvalue.split('|')
		mm.set(domain, mnum+'|'+arr_cval[1]+'|'+arr_cval[2])
		print "mail's restriction number is changed to " + mnum

# 도메인 상태보기
def view_record(vkey):

	print vkey

	cvalue = mm.get(vkey)

	if cvalue == None:
		print vkey+": not found record"
	else:
		key_cval = cvalue.split('|')

	print "------------------------"
	print "key : ", vkey
	print "cnt : ", key_cval[0]
	print "flag : ", key_cval[1]
	print "date : ", key_cval[2]
	print "------------------------"

# 도메인 삭제
def erase_record(domain):
	mm.delete(domain)

def mc_get_state():
	print mm.get_stats()


# 전체보기
def view_all_record():

	# python-memcache 모듈에 전체 레코드를 가져오는 함수가 없어서 데이터베이스에서 키(이메일,도메인)를
	# 가져와서 get_multi 함수로 레코드 전체의 통계를 가져오는것으로 대신함.

	db=MySQLdb.connect('localhost', 'hdev', 'dkandldbdjqtdj', 'smtp').cursor()
	db.execute("select u.emailId, d.domain from smtp_user u, smtp_domain d where u.userId=d.userId")
	erows=db.fetchall()
	db.execute("select domain from smtp_domain")
	drows=db.fetchall()

	keys = []

	for row in erows:
		userId, domain = tuple(row)
		keys.append(userId+"@"+domain)

	for row in drows:
		keys.append(row[0])

	# data type : dictionary
	data = mm.get_multi(keys)

	# data type convert
	for i in data.items():
		print i

def usage():
	print '무제한 발송 :      ./mcadmin.py -r id@example.com'
	# 반드시 id@expampel.com 을 키로 해야 함.
	# * 도메인의 무제한 발송은 도메인내의 다수개의 이메일주소가 무제한 기능을 사용해야 하는데 이는 각 사용자들에게
	#   무제한 필드를 허용해주는것이 더 편리하다고 판단됨. 도메인만 무제한 발송을 한다면 현재 프로그램상에서 순서적
	#   인 문제가 보임. ( 도메인 무제한 발송도 구현은 가능하다고 판단됨. )
	#
	print '모든 레코드 삭제 : ./mcadmin.py -f or --flush'
	print '날짜 변경 :        ./mcadmin.py -k example.com ( or id@example.com) -d 20070702'
	print '제한 숫자변경 :    ./mcadmin.py -k example.com ( or id@example.com) -n 4000'
	print '해당 레코드 삭제 : ./mcadmin.py -e example.com ( or id@example.com)'
	print '해당 레코드 보기 : ./mcadmin.py -v example.com ( or id@example.com)'
	print '전체 레코드 보기 : ./mcadmin.py -a'
	print '메모리 캐쉬 상태보기 : ./mcadmin.py -s'

def main():

	try:
		# sys.argv 는 인수전체(명령어를 포함한)를 sys.argv[1:] 은 인수만을 가져온다.
		#
		#
		# 콜론의 의미 ( r:fd:k:n:V:D: )
		#
		# - 콜론을 붙일경우에는 반드시 인자를 요구하고 붙이지 않을경우에는 인자를 요구하지 않는다.
		#
		# Parses command line options and parameter list. args is the argument list to be parsed, without the leading reference to the running program.
		# Typically, this means "sys.argv[1:]".
		# options is the string of option letters that the script wants to recognize, with options that require an argument followed by a colon
		# (":"; i.e., the same format that Unix getopt() uses). 
		# Note: Unlike GNU getopt(), after a non-option argument, all further arguments are considered also non-options.
		# This is similar to the way non-GNU Unix systems work. 
		opts, args = getopt.getopt(sys.argv[1:], "r:fd:k:n:v:e:as", ["restriction","flush","date","key","number","view","erase","all","state"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)

#	output = None
#	verbose = False

#	print opts
#	print args		# 인자다음에 따라오는 인자가 아닌 그 이외의 인자를 받는 배열변수

	for opt, arg in opts:

		if opt in ("-r", "--restriction"):
				modify_restriction(arg)

		if opt in ("-f", "--flush"):
				all_data_flush()

		if opt in ("-k", "--key"):
				if get_record(arg) == None:
						usage()
						sys.exit(2)
				else:
					key = arg	
		if opt in ("-d", "--date"):
				modify_date(key, arg)

		if opt in ("-n", "--number"):
				modify_mnum(key, arg)

		if opt in ("-v", "--view"):
				view_record(arg)

		if opt in ("-e", "--erase"):
				erase_record(arg)

		if opt in ("-a", "--all"):
				view_all_record()

		if opt in ("-s", "--state"):
				mc_get_state()

if __name__ == "__main__":
	main()

