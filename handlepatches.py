#! /usr/bin/env python

# Copyright (C) 2015 Ross Burton <ross.burton@intel.com>
# MIT licensed

import os
import sys
import imapclient
import ConfigParser

cp = ConfigParser.SafeConfigParser({"Verbose": "False",
                                    "NumberOfCommits": "10000"})
cp.read(os.path.expanduser("~/.config/handlepatches.conf"))

verbose = cp.getboolean("Config", "Verbose")
num_commits = cp.getint("Config", "NumberOfCommits")

def get_commits(branch):
    import os, subprocess
    os.chdir(os.path.expanduser(cp.get("Config", "RepoPath")))
    revlist = subprocess.Popen("git log %s --format=oneline -n %d" % (branch, num_commits), shell=True, stdout=subprocess.PIPE).communicate()[0]
    revlist = revlist.decode("utf-8")
    revdata = {}
    for line in revlist.split("\n"):
        if not line:
            continue
        rev, desc = line.split(" ", 1)

        if verbose: print "Storing commit '%s'" % desc
        revdata[desc] = rev
    return revdata

def match_messages(server, folder, search=None):
    server.select_folder(folder)
    if search:
        messages = server.gmail_search(search)
    else:
        messages = server.search()
    print "Fetched %d messages" % len(messages)

    response = server.fetch(messages, ['ENVELOPE'])
    for msgid, data in response.iteritems():
        subject = data["ENVELOPE"].subject
        if "]" in subject:
            subject = subject.rsplit("]", 1)[1].strip()

        if verbose: print "Searching for subject '%s'" % subject
        if subject in revdata:
            if verbose:
                print "Found match for %s" % subject
        else:
            messages.remove(msgid)

    print "Found %d merged patches" % len(messages)
    return messages



if len(sys.argv) > 1:
    branch = sys.argv[1]
else:
    branch = "origin/master"
revdata = get_commits(branch)

server = imapclient.IMAPClient(cp.get("Config", "SMTPServer"), ssl=True)
server.login(cp.get("Config", "SMTPUSer"), cp.get("Config", "SMTPPassword"))

print "oe-core..."
messages = match_messages(server, "INBOX", "label:Yocto-OE-core in:inbox PATCH*")
server.add_flags(messages, imapclient.SEEN)
server.delete_messages(messages)

print "Poky..."
messages = match_messages(server, "INBOX", "label:Yocto-Poky in:inbox PATCH")
server.add_flags(messages, imapclient.SEEN)
server.delete_messages(messages)

print "Rework..."
messages = match_messages(server, "[Gmail]/All Mail", "label:Patches/Rework")
server.add_flags(messages, imapclient.SEEN)
server.remove_gmail_labels(messages, "Patches/Rework")

print "Later..."
messages = match_messages(server, "[Gmail]/All Mail", "label:Patches/Later")
server.add_flags(messages, imapclient.SEEN)
server.remove_gmail_labels(messages, "Patches/Later")
