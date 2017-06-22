#! /usr/bin/env python3

# Copyright (C) 2015 Ross Burton <ross.burton@intel.com>
# MIT licensed

import os
import sys
import argparse
import imapclient
import configparser
import subprocess

cp = configparser.SafeConfigParser()
cp.read(os.path.expanduser("~/.config/handlepatches.conf"))

parser = argparse.ArgumentParser()
parser.add_argument("branch", nargs="?", help="The branch to scan (default origin/master)", default="origin/master")
parser.add_argument("-c", "--commits", help="Number of commits back to go in history", type=int, default=10000)
parser.add_argument("-v", "--verbose", help="Verbose mode", action="store_true", default=False)
parser.add_argument("-d", "--dryrun", help="Dry-run only", action="store_true", default=False)
args = parser.parse_args()

verbose = args.verbose

def check_git_workdir():
    devnull = open(os.devnull, "w")
    return subprocess.call(["git", "rev-parse", "--is-inside-work-tree"],
                           stdout=devnull, stderr=subprocess.STDOUT) == 0

def get_commits(branch, num_commits):
    revlist = subprocess.Popen("git log %s --format=oneline -n %d" % (branch, num_commits), shell=True, stdout=subprocess.PIPE).communicate()[0]
    revlist = revlist.decode("utf-8")
    revdata = {}
    for line in revlist.split("\n"):
        if not line:
            continue
        rev, desc = line.split(" ", 1)

        if verbose: print("Storing commit '%s'" % desc)
        revdata[desc] = rev
    return revdata

def match_messages(server, folder, search=None):
    server.select_folder(folder)
    if search:
        messages = server.gmail_search(search)
    else:
        messages = server.search()
    print("Fetched %d messages" % len(messages))

    response = server.fetch(messages, ['ENVELOPE'])
    for msgid, data in response.items():
        if b"ENVELOPE" not in data:
            print("Skipping %s without ENVELOPE" % msgid)
            continue

        # Assume subject is UTF-8
        subject = data[b"ENVELOPE"].subject.decode("utf-8")
        if "]" in subject:
            subject = subject.rsplit("]", 1)[1].strip()

        if verbose: print("Searching for subject '%s'" % subject)
        if subject in revdata:
            if verbose:
                print("Found match for %s" % subject)
        else:
            messages.remove(msgid)

    print("Found %d merged patches" % len(messages))
    return messages


if not check_git_workdir():
    print("handlepatches wasn't ran inside a git clone, aborting")
    sys.exit(1)

revdata = get_commits(args.branch, args.commits)

server = imapclient.IMAPClient(cp.get("Config", "IMAPServer"), ssl=True)
server.login(cp.get("Config", "IMAPUSer"), cp.get("Config", "IMAPPassword"))

print("oe-core...")
messages = match_messages(server, "INBOX", "label:Yocto-OE-core in:inbox")
if not args.dryrun:
    server.add_flags(messages, imapclient.SEEN)
    server.remove_flags(messages, imapclient.FLAGGED)
    server.delete_messages(messages)

print("Poky...")
messages = match_messages(server, "INBOX", "label:Yocto-Poky in:inbox")
if not args.dryrun:
    server.add_flags(messages, imapclient.SEEN)
    server.remove_flags(messages, imapclient.FLAGGED)
    server.delete_messages(messages)

print("Rework...")
messages = match_messages(server, "[Gmail]/All Mail", "label:Patches/Rework")
if not args.dryrun:
    server.add_flags(messages, imapclient.SEEN)
    server.remove_flags(messages, imapclient.FLAGGED)
    server.remove_gmail_labels(messages, "Patches/Rework")

print("Later...")
messages = match_messages(server, "[Gmail]/All Mail", "label:Patches/Later")
if not args.dryrun:
    server.add_flags(messages, imapclient.SEEN)
    server.remove_flags(messages, imapclient.FLAGGED)
    server.remove_gmail_labels(messages, "Patches/Later")
