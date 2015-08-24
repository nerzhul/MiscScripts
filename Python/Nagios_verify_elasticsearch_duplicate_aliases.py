#! /usr/bin/python
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

import getopt, sys, json
import urllib2

PROG_NAME = "check_els_indexes"

def doELSVerification(url):
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        jsonresp = json.loads(response.read())

        # Count all elasticsearch server aliases
        elsAliases = {}
        for index in jsonresp:
            if "aliases" in jsonresp[index]:
                for idx in jsonresp[index]["aliases"]:
                    elsAliases["%s" % idx] = elsAliases["%s" % idx] + 1 if idx in elsAliases else 1

        # Filter aliases to show only problematic aliases
        filteredAliases = []
        for alias in elsAliases:
            if elsAliases[alias] > 1:
                filteredAliases += ["%s (%d occurences)" % (alias, elsAliases[alias]), ]

        # Do error message
        if len(filteredAliases) > 0:
            print "Some aliases are duplicated: %s" % ", ".join(filteredAliases)
            return 2
        else:
            print "No duplicate alias occurence found"
            return 0


if __name__ == "__main__":
    try:
        host = None
        port = None
        index = None
        opts, args = getopt.getopt(sys.argv[1:], "h:p:", ["host=", "port="])
        for o, a in opts:
            if o in ("-h", "--host"):
                host = a
            elif o in ("-p", "--port"):
                port = a
    except getopt.GetoptError:
        print "Invalid options passed to %s" % PROG_NAME
        sys.exit(3)

    if host == None:
        print "No option --host given for %s, aborting" % PROG_NAME
        sys.exit(3)

    if port == None:
        print "No option --port given for %s, aborting" % PROG_NAME
        sys.exit(3)

    els_alias_url = "http://%s:%s/_alias/*" % (host, port)

    elsStatus = doELSVerification(els_alias_url)
    sys.exit(elsStatus)
