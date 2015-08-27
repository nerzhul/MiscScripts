#! /usr/bin/python
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

import getopt, sys, json, re
import urllib2, logging
from logging.handlers import SysLogHandler

PROG_NAME = "ELS-Purge-Old-Idx"
host = None
port = None
dryRun = False
dryRunSuffix = ""
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def initLoggingSystem():
	screenformatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
	syslogformatter = logging.Formatter('ELS-Purge-Old-Idx[%(process)d]: %(levelname)s - %(message)s')
	sysloghandler = SysLogHandler(address = '/dev/log', facility=SysLogHandler.LOG_CRON)
	sysloghandler.setFormatter(syslogformatter)
	logger.addHandler(sysloghandler)
	steamhandler = logging.StreamHandler()
	steamhandler.setLevel(logging.INFO)
	steamhandler.setFormatter(screenformatter)
	logger.addHandler(steamhandler)

def getHTTPJson(url):
	logging.debug("getHTTPJson: %s" % url)
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	return json.loads(response.read())

def deleteHTTP(url):
	logging.debug("deleteHTTP: %s" % url)
	opener = urllib2.build_opener(urllib2.HTTPHandler)
	req = urllib2.Request(url, None, {})
	req.get_method = lambda: 'DELETE'
	response = urllib2.urlopen(req)
	return json.loads(response.read())

def fetchELSAliases():
	logging.info("Fetching elasticsearch aliases.")
	return getHTTPJson("http://%s:%s/_alias/*" % (host, port))

def fetchELSClusterState():
	logging.info("Fetching elasticsearch cluster state.")
	return getHTTPJson("http://%s:%s/_cluster/state" % (host, port))

def removeELSIndex(idxname):
	logging.info("Remove index: %s%s" % (idxname, dryRunSuffix))
	if dryRun == False:
		deleteHTTP("http://%s:%s/%s/" % (host, port, idxname))

# ELS v0.9: for retrieve index we should parse cluster state
def fetchELSIndexes():
	data = fetchELSClusterState()
	logging.info("Retrieving indexes from cluster state.")
	elsIndexes = []
	for index in data["routing_table"]["indices"]:
		elsIndexes += [index, ]
	return elsIndexes

if __name__ == "__main__":
	try:
		opts, args = getopt.getopt(sys.argv[1:], "h:p:n", ["host=", "port=", "dryrun"])
		for o, a in opts:
			if o in ("-h", "--host"):
				host = a
			elif o in ("-p", "--port"):
				port = a
			elif o in ("-n", "--dryrun"):
				dryRun = True
	except getopt.GetoptError:
		print "Invalid options passed to %s" % PROG_NAME
		sys.exit(3)

	if host == None:
		print "No option --host given for %s, aborting" % PROG_NAME
		sys.exit(3)

	if port == None:
		print "No option --port given for %s, aborting" % PROG_NAME
		sys.exit(3)

	# Init logging system
	initLoggingSystem()

	if dryRun:
		dryRunSuffix = " (skipped, running in dryrun mode)"
		logging.info("/!\\ Running %s in dryrun mode /!\\" % PROG_NAME)

	# Fetch datas from elasticsearch
	elsAliases = fetchELSAliases()
	elsIndexes = fetchELSIndexes()
	elsIndexesAssoc = {}

	# Deduce index names by matching the date and deduce which indexes are
	# different version of the same index. Also set a variable to tell on
	# which date is the current alias
	logging.info("Analyze indexes to find the current cluster state")
	for index in elsIndexes:
		reres = re.findall("(.*)_\d{8}", index)
		if reres == []:
			logging.error("Invalid index found: '%s'. Aborting the process." % index)
			sys.exit(4)
		if reres[0] not in elsIndexesAssoc:
			elsIndexesAssoc[reres[0]] = {"indexes": [], "alias": False}

		idxDate = re.sub("%s_" % reres[0],"", index)
		elsIndexesAssoc[reres[0]]["indexes"] += [int(idxDate), ]
		logging.debug("Found date %s for index %s" % (idxDate, reres[0]))

		if index in elsAliases:
			# Index alias already set: fail, there is a duplicate
			if elsIndexesAssoc[reres[0]]["alias"] != False:
				logging.error("Duplicate alias for index %s, aborting !" % index)
				sys.exit(5)
			elsIndexesAssoc[reres[0]]["alias"] = int(idxDate)

	# Now find indexes to remove
	logging.info("Processing index analysis to find old indexes to remove...")
	removedIndexesNb = 0
	for index in elsIndexesAssoc:
		# No alias found for this index, don't do anything
		if elsIndexesAssoc[index]["alias"] == False:
			logging.debug("No alias found for index '%s', skipping" % index)
			continue

		# Remove current index alias from index list to check & purge; this prevent
		# removal of current used index
		elsIndexesAssoc[index]["indexes"].remove(elsIndexesAssoc[index]["alias"])

		# We need to have at least 2 indexes to cleanup something
		if len(elsIndexesAssoc[index]["indexes"]) < 2:
			logging.debug("No indexes to remove for index '%s', skipping" % index)
			continue

		# Sort indices dates to have a incremental list
		indexesToDelete = sorted(elsIndexesAssoc[index]["indexes"])

		# Remove last indice from the list, we need to keep it as a backup
		indexesToDelete.pop()

		for idtod in indexesToDelete:
			removeELSIndex("%s_%s" % (index, idtod))
			removedIndexesNb = removedIndexesNb + 1

	logging.info("Indexes cleanup done. %s indexes removed%s" % (removedIndexesNb, dryRunSuffix))
