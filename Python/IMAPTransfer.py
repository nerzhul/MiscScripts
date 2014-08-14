# -*- coding: utf-8 -*-

"""
Copyright (c) 2014, Loic Blot <loic dot blot at unix-experience dot fr>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import imaplib, email, time

moveRules = { 
	"GMAIL-TO-EXAMPLE": {
		"server": "imap.gmail.com",
		"port": 993,
		"login": "sourcelogin",
		"password": "sourcepwd",
		"dest_server": "imap.example.org",
		"dest_port": 993,
		"dest_login": "destlogin",
		"dest_password": "destpwd",
		"filters": [
			{ "imap_filter": 'HEADER FROM @plus.google.com', "dest": "Informatique.Sites Internet.Google Plus", "mark_deleted": True },
		]
	}
}

for importRule in moveRules:
	print "Executing rule %s" % importRule
	
	print "Connect to %s" % importRule["server"]
	conn = imaplib.IMAP4_SSL(importRule["server"],importRule["port"])
	
	try:
		print "Login to %s" % importRule["server"]
		conn.login("%s" % importRule["login"],"%s" % importRule["password"])
	except:
		print "Failed to login to %s !!!" % importRule["server"]
		exit()

	print "Connect to %s" % importRule["dest_server"]
	conn2 = imaplib.IMAP4_SSL("%s" % importRule["dest_server"],"%s" % importRule["dest_port"])
	
	try:
		print "Login to %s" % importRule["dest_server"]
		conn2.login("%s" % importRule["dest_login"], "%s" %importRule["dest_password"])
	except:
		print "Failed to login to %s !!!" % importRule["dest_server"]
		conn.logout()
		exit()

	conn.select()
	conn2.select()

	for importFilter in importRule["filters"]:
		mbExists = conn2.select("%s" % importFilter["dest"])
		if mbExists[0] != "OK":
			print "Mailbox %s doesn't exists, cannot apply this filter !" % importFilter["dest"]
			continue
		typ, data = conn.search(None, '(%s)' % importFilter["imap_filter"])
		msgList = data[0].split()

		if len(msgList) > 0:
			print "Copying %s messages. Please wait..." % len(msgList)
			for msgId in msgList:
				typ, data = conn.fetch(msgId, '(RFC822)')
				print "Copying message from %s" % email.message_from_string(data[0][1])["From"]
				conn2.append("%s" % importFilter["dest"],
					'',
					imaplib.Time2Internaldate(time.time()),
					str(email.message_from_string(data[0][1]))
				)
	
				if importFilter["mark_deleted"] == True:
					# Mark mail as deleted
					conn.store(msgId,'+FLAGS','\\Deleted')
	
			print "%s messages imported." % len(msgList)

	# Clear all the DELETED flagged mails
	conn.expunge()

	# And now close the connection
	conn.close()
	conn.logout()
	conn2.select()
	conn2.close()
	conn2.logout()
