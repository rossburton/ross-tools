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
DRY_RUN = False

cp = ConfigParser.SafeConfigParser()
cp.read(os.path.expanduser("~/.config/handlepatches.conf"))

server = imapclient.IMAPClient(cp.get("Config", "SMTPServer"), ssl=True)
server.login(cp.get("Config", "SMTPUSer"), cp.get("Config", "SMTPPassword"))

server.select_folder("INBOX")
# TODO Configure this in some way. git config?
messages = server.gmail_search("label:Yocto-OE-core label:Patches-Apply in:inbox")
print "Fetched %d messages" % len(messages)

response = server.fetch(messages, ['RFC822 ENVELOPE'])
for data in sorted(response.itervalues(), key=lambda d: d['ENVELOPE'].date):
    if DRY_RUN:
        print data['ENVELOPE'].subject
        continue

    # TODO: verify that the subject contains PATCH
    gitam = subprocess.Popen(['git', 'am', '--3way', '--signoff', '--whitespace=nowarn'],
                             stdin=subprocess.PIPE)
    gitam.communicate(data['RFC822'])
    retcode = gitam.wait()
    if retcode:
        raise subprocess.CalledProcessError(retcode, 'git')

if not DRY_RUN:
    server.add_flags(messages, imapclient.SEEN)
    server.remove_gmail_labels(messages, "Patches/Apply")
    server.delete_messages(messages)
