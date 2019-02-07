#! /usr/bin/env python2.3
# -*- coding: utf-8 -*-
#
#
# 수정일 : 2007년 5월 25일 
# 수정인 : 심플렉스인터넷(주)
#		   서버개발팀  문 종 영
#
#
# 추가항목
# 1. 도메인당 메일발송량 제한
# 2. 무제한 발송을 위한 필드
# 3. 무제한 발송을 위한 옵션추가
# 4. 여유분 필드 기본값 '0'
# 5. 날짜초과 처리
#

import sys, asyncore, threading, socket, time, StringIO
import esmtpd
import memcache
import re
import time, getopt

CEMAIL="200"
CDOMAIN="40000"

DOMAIN_DEFAULT=CDOMAIN+"|F|"+str(time.strftime('%Y%m%d'))
EMAIL_DEFAULT=CEMAIL+"|F|"+str(time.strftime('%Y%m%d'))

# DOMAIN_DEFAULT=CDOMAIN+"|F|"+str(time.strftime('%Y%m%d')):
# EMAIL_DEFAULT=CEMAIL+"|F|"+str(time.strftime('%Y%m%d')):

class ESMTPChannel(esmtpd.SMTPChannel):
	def smtp_EHLO(self,arg):
		esmtpd.SMTPChannel.smtp_HELO(self,arg)


class rcptCounter(esmtpd.PureProxy):

	def __init__(self,localaddr, remoteaddr):
		self.mc = memcache.Client(['127.0.0.1:11211'],debug = 0)
		esmtpd.PureProxy.__init__(self,localaddr, remoteaddr)

	def process_message(self, peer, mailfrom, rcpttos, data):

		# print "count = : " ,len(rcpttos)
		#
		# 1. 한번에 보낼수 있는 양 제어
		#  - rcpttos 의 경우 to, cc, bcc 를 모두 포함한 주소를 , 로 구분하여 저장 되어있다.

		if len(rcpttos) > 100:
			return "550 maximal number of recipients per delivery is over"

		token = mailfrom.split()
		key = token[0].strip()

		key = key.lstrip('<')
		email = key.rstrip('>')
		domain = email.split('@')[1]
		
		eval = self.mc.get(email)

		# 2. 이메일 레코드가 없을때 
		if eval == None:

			# 2-1. 이메일키 레코드 생성처리
			if not self.mc.set(email,EMAIL_DEFAULT):
				return "451 SMTP Server Temporary Error"

			# 2-2. 메시지 전송
			eval = self.mc.get(email)
			ecnt = eval.split('|')

			# 2-3. 메일전송후 해당 이메일키에 대한 레코드에 len(rcpttos) 만큼 감소
			self.mc.set(email, str(int(ecnt[0])-len(rcpttos))+'|'+ecnt[1]+'|'+ecnt[2])

			esmtpd.PureProxy.process_message(self, peer, mailfrom, rcpttos, data)

			# 2-4. 해당 도메인 레코드 가져오기
			dval = self.mc.get(domain)

			# 2-5. 도메인 레코드가 없을때 생성
			if dval == None:
				if not self.mc.set(domain,DOMAIN_DEFAULT):
					return "451 SMTP Server Temporary Error"
				# 2-6. 생성된 해당 도메인 레코드 가져오기
				dval = self.mc.get(domain)

			dcnt = dval.split('|')
			# 2-7.  메일전송후 해당 도메인키 또한 len(rcpttos) 만큼 감소
			self.mc.set(domain, str(int(dcnt[0])-len(rcpttos))+'|'+dcnt[1]+'|'+dcnt[2])

			# * 주의 : 변경된 값을 출력을 하려면 새로 mc.get 을 수행하여 데이터를 가져와야 한다.


		# 3. 이메일 레코드에 내용이 있을때 수행
		else:

			# 3-1. 이메일 레코드 값 가져오기
			ecnt = eval.split('|')

			# 3-2. 도메인 레코드 가져오기
			dval = self.mc.get(domain)

			# 3-3. 도메인 레코드가 없을때 생성후 가져오기
			if dval == None:
				if not self.mc.set(domain,DOMAIN_DEFAULT):
					return "451 SMTP Server Temporary Error"
				dval = self.mc.get(domain)

			dcnt = dval.split('|')

			# 3-4. 도메인 발송수가 초과되었을때 리턴
			if ( int(dcnt[0]) < 1 ):
				return "550 Your domain-counter  is over"

			# 3-5. 무제한 메일발송이 아닐때
			if ( dcnt[1] == 'F' ):

				# 3-6. 계정 메일발송량을 모두 소비했을때
				if ( int(ecnt[0]) < 1 ):

					# 3-7. 메일이 초과하고 시간이 지났을때 초기화
					# if ( int(ecnt[2])+30 < int(time.time()) ):
					if ( ecnt[2] != str(time.strftime('%Y%m%d')) ):
						self.mc.set(email,CEMAIL+"|F|"+str(time.strftime('%Y%m%d')))
					else:
						return "550 Your mail-counter is over"

				esmtpd.PureProxy.process_message(self, peer, mailfrom, rcpttos, data)

				# 3-10. 이메일 값 감소처리
				#if ( int(ecnt[2])+30 > int(time.time())):
				
				if ( ecnt[2] == str(time.strftime('%Y%m%d')) ):
					self.mc.set(email, str(int(ecnt[0])-len(rcpttos))+'|'+ecnt[1]+'|'+ecnt[2])
				else:
					self.mc.set(email,CEMAIL+"|F|"+str(time.strftime('%Y%m%d')))
					# self.mc.set(email,EMAIL_DEFAULT)

				# 3-11. 도메인 값 감소처리
				#if ( int(dcnt[2])+60 > int(time.time()) ):
				if ( dcnt[2] == str(time.strftime('%Y%m%d')) ):
					self.mc.set(domain, str(int(dcnt[0])-len(rcpttos))+'|'+dcnt[1]+'|'+dcnt[2])
				else:
					self.mc.set(domain, CDOMAIN+"|F|"+str(time.strftime('%Y%m%d')))
					# self.mc.set(email,CDOMAIN"|F|"+str(int(time.time())))


				# 감소처리 테스트 용
				#
				#print int(ecnt[2])+60 , int(time.time())
				#print "--------  email start ----------"
				#print "key : ", email
				#print "cnt : ", ecnt[0]
				#print "flag : ", ecnt[1]
				#print "date : ", ecnt[2]
				#print "--------  email end ----------"

				#print int(dcnt[2])+60 , int(time.time())
				#print "--------  domain start ----------"
				#print "key : ", domain
				#print "cnt : ", dcnt[0]
				#print "flag : ", dcnt[1]
				#print "date : ", dcnt[2]
				#print "--------  domain end ----------"
				#

			# 3-12. 무제한 메일발송일때
			else:
				esmtpd.PureProxy.process_message(self, peer, mailfrom, rcpttos, data)

	def handle_accept(self):
		conn, addr = self.accept()
		channel = ESMTPChannel(self, conn, addr)

if __name__ == "__main__":

	proxy = rcptCounter(('localhost',10025),('localhost',10021))

	# proxy = rcptCounter(('',10025),(None,0))
	asyncore.loop()

	# try:
	#  	asyncore.loop()
	# except KeyboardInterrupt:
	#	pass

