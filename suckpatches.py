#! /usr/bin/env python

# Copyright (C) 2015 Ross Burton <ross.burton@intel.com>
# MIT licensed

import os
import sys
import argparse
import imapclient
import ConfigParser
import subprocess

# TODO integrate into applyotron

cp = ConfigParser.SafeConfigParser()
cp.read(os.path.expanduser("~/.config/handlepatches.conf"))

server = imapclient.IMAPClient(cp.get("Config", "SMTPServer"), ssl=True)
server.login(cp.get("Config", "SMTPUSer"), cp.get("Config", "SMTPPassword"))

server.select_folder("INBOX")
messages = server.gmail_search("label:Yocto-OE-core in:inbox is:starred")
print "Fetched %d messages" % len(messages)

response = server.fetch(messages, ['RFC822'])
# TODO sort by date sent to approximate patch order
for msgid, data in response.iteritems():
    # TODO: verify that the subject contains PATCH
    gitam = subprocess.Popen(['git', 'am', '--3way', '--signoff', '--whitespace=nowarn'],
                             stdin=subprocess.PIPE)
    gitam.communicate(data['RFC822'])
    retcode = gitam.wait()
    if retcode:
        raise subprocess.CalledProcessError(retcode, 'git')

server.add_flags(messages, imapclient.SEEN)
server.remove_flags(messages, imapclient.FLAGGED)
server.delete_messages(messages)
