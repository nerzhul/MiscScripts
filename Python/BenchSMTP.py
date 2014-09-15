# -*- Coding: utf-8 -*-
#
#  Copyright (C) 2014 Loic BLOT
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#  
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following disclaimer
#    in the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of the Europages nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#  

import smtplib, datetime, random, string, thread, time
from email.MIMEText import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Lock

threadNumber = 24
maxRunTimePerThread = 600
maxMails = 2000
virusChance = 30
spamChance = 30

smtpAddress = 'smtp.example.org'
senderName = "Test sender"
senderMail = "test.sender@example.org"
receiverName = "Test recv"
receiverMail = 'trcv@example.org'

spamTestString = "XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-EMAIL*C.34X"

virusTest = MIMEText("X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*#")
virusTest.add_header('Content-Disposition', 'attachment', filename="virus.txt")

randomMsgBufferSize = 50
msgBuffers = []

verboseSent = False

# For threading wait
lock = []

# For threading mail counter
mailCounter = []
	
def send_mails(threadId):
	lock[threadId-1] = True
	mailCounter[threadId-1] = 0
	print "Sending mails from Thread %d" % threadId
	starttime = datetime.datetime.now()
	testNb = 1

# Uncomment the test you want to use. Time or Mail number

	while (datetime.datetime.now() - starttime).seconds < maxRunTimePerThread:
	#while testNb <= (maxMails / threadNumber):
		hasVirus = False
		hasSpam = False
		msgIdChoose = random.randint(1,randomMsgBufferSize-1)
		
		msg = MIMEMultipart('alternative')
		msg["From"] = "\"%s\" <%s>" % (senderName, senderMail)
		msg["Subject"] = "Test mail (Thread %d / Msg %d)" % (threadId, testNb)
		
		if random.randint(1,100) < spamChance:
			hasSpam = True
		
		# If spam, add the test string
		body = "%s%s" % (msgBuffers[msgIdChoose], spamTestString 
		if hasSpam == True else "")
		
		msg.attach(MIMEText(body, 'plain'))
		
		# If virus, add virus attachment
		if random.randint(1,100) < virusChance:
			msg.attach(virusTest)
			hasVirus = True
		
		if verboseSent == True:
			print "Send mail %d for thread %s (virus: %s / spam %s)" % (msgIdChoose, threadId, "true" if hasVirus == True else "false",
				"true" if hasSpam == True else "false")
		
		
		try:
		   smtpObj = smtplib.SMTP(smtpAddress)
		   smtpObj.sendmail(senderMail, [receiverMail], msg.as_string())
		except smtplib.SMTPException, e:
		   print "Error: unable to send email"
		   print e
		   lock[threadId-1] = False
		

		testNb += 1
		mailCounter[threadId-1] += 1
		#increaseMailCounter()
		
		
	print "Send %d mails for thread %s. Total time: %s" % (testNb, threadId, datetime.datetime.now() - starttime)
	
	lock[threadId-1] = False


print "Generating random message buffers"
for i in range(0,randomMsgBufferSize):
	msgBuffers.append(''.join(random.choice(string.ascii_uppercase) for _ in range(random.randint(20,125000))))

print "Sending mails using %d threads" % threadNumber
for i in range(1,threadNumber+1):
	lock.append(False)
	mailCounter.append(0)
	thread.start_new_thread(send_mails, (i,))

time.sleep(1)

runTime = datetime.datetime.now()
runMinutes = 0

# lock table must contain False everywhere, else some threads are running
while True in lock:
	if (datetime.datetime.now() - runTime).seconds >= 60:
		runMinutes += 1
		totalMails = 0
		for ct in mailCounter:
			totalMails += ct
		print "Test was running since %d minute(s). %d mails sent" % (runMinutes, totalMails)
		runTime = datetime.datetime.now()
		
	pass
	
print "Done"

