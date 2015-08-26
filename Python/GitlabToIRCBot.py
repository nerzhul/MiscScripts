#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2015, Loïc Blot
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of the FreeBSD Project.
"""
# An IRC bot which listens to gitlab hooks to send messages

import irc.bot
import irc.strings
import logging
import json
from logging.handlers import TimedRotatingFileHandler
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
from threading import Thread
import BaseHTTPServer

botName = "GitlabBot"
ircServer = "irc.freenode.net"
ircChannels = ("#devchan1","#devchan2")
ircAllowedPriv = ("adminirc")
logFileName = "/var/log/gitlabbot.log"

class EpixelBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channels, nickname, server, port=6667):
    	logger.info("Starting EpixelBot")
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
	self.channelist = channels

    def on_nicknameinuse(self, c, e):
    	logger.warn("Nickname %s already in use" % c.get_nickname())
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
    	for chan in self.channelist:
	    	logger.info("Joining channel %s" % chan)
        	c.join(chan)
	self.c = c
    
    def on_kick(self, c, e):
    	chan = e.target
    	logger.info("Somebody kicked me, re-joining channel %s" % chan)
        c.join(chan)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
    	author = e.source.nick
	message = e.arguments[0].lower()
    	targetchan = e.target
	logger.info("%s - %s: %s" % (targetchan, author, message))
        a = e.arguments[0].split(":", 1)
        if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
            self.do_command(e, a[1].strip())
        return

    def on_dccmsg(self, c, e):
        c.privmsg("You said: " + e.arguments[0])

    def on_dccchat(self, c, e):
        if len(e.arguments) != 2:
            return
        args = e.arguments[1].split()
        if len(args) == 4:
            try:
                address = ip_numstr_to_quad(args[2])
                port = int(args[3])
            except ValueError:
                return
            self.dcc_connect(address, port)

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection

	if nick not in ircAllowedPriv:
		c.notice(nick, "I don't want to talk with you !")
		return

        if cmd == "disconnect":
            self.disconnect()
        elif cmd == "die":
            self.die()
        elif cmd == "stats":
            for chname, chobj in self.channels.items():
                c.notice(nick, "--- Channel statistics ---")
                c.notice(nick, "Channel: " + chname)
                users = chobj.users()
                users.sort()
                c.notice(nick, "Users: " + ", ".join(users))
                opers = chobj.opers()
                opers.sort()
                c.notice(nick, "Opers: " + ", ".join(opers))
                voiced = chobj.voiced()
                voiced.sort()
                c.notice(nick, "Voiced: " + ", ".join(voiced))
        elif cmd == "dcc":
            dcc = self.dcc_listen()
            c.ctcp("DCC", nick, "CHAT chat %s %d" % (
                ip_quad_to_numstr(dcc.localaddress),
                dcc.localport))
        else:
            c.notice(nick, "Not understood: " + cmd)

class HttpRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
    	logger.info(self.path)
    def do_POST(self):
    	jsonquery = self.rfile.read(int(self.headers['Content-Length']))
	jsonparsed = json.loads(jsonquery)
	if "object_kind" in jsonparsed:
		if jsonparsed["object_kind"] == "push":
			repository = jsonparsed["repository"]["name"]
			branch = jsonparsed["ref"]
			for commit in jsonparsed["commits"]:
				commitmsg = commit["message"].splitlines()[0]
				ircmsg = "[%s {%s}] Commit pushed: '%s' (%s) /=> %s" % (repository, branch, commitmsg, commit["author"]["name"], commit["url"])
				for chan in bot.channelist:
					bot.c.notice(chan, ircmsg)
		elif jsonparsed["object_kind"] == "issue":
			ircmsg = "[Issue %s {%s}] %s /=> %s" % (jsonparsed["object_attributes"]["id"],jsonparsed["object_attributes"]["action"],jsonparsed["object_attributes"]["title"],jsonparsed["object_attributes"]["url"])
			for chan in bot.channelist:
				bot.c.notice(chan, ircmsg)
		
		# Answer ok, else gitlab thinks there is a problem
		self.send_response(200)
		self.end_headers()
		self.wfile.write("OK")

class HttpListener(Thread):
	def __init__(self):
		Thread.__init__(self)
		server_class = BaseHTTPServer.HTTPServer
		self.httpd = server_class(("0.0.0.0", 80), HttpRequestHandler)

	def run(self):
		self.httpd.serve_forever()

def main():
	logger.setLevel(logging.DEBUG)

	formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
	filehandler = TimedRotatingFileHandler(logFileName,'midnight')
	filehandler.setLevel(logging.INFO)
	filehandler.setFormatter(formatter)
	logger.addHandler(filehandler)

	steamhandler = logging.StreamHandler()
	steamhandler.setLevel(logging.INFO)
	steamhandler.setFormatter(formatter)
	logger.addHandler(steamhandler)

	httpd = HttpListener()
	httpd.start()
	bot.start()

logger = logging.getLogger()
bot = EpixelBot(ircChannels, botName, ircServer, 6667)

if __name__ == "__main__":
    main()
