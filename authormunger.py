#! /usr/bin/env python3

"""
When groups.io can't agree who is sending an email for SMTP being horrible
reasons, you end up with patches with bad authorship:

Author: wangmy via lists.openembedded.org
<wangmy=fujitsu.com@lists.openembedded.org>

Extract the email address, find a matching S-o-b, and use that name/email as the
correct author.

Alters the current commit (specifically, HEAD), so can be used in a rebase
operation:

$ git rebase --exec=authormunger.py origin/master
"""

# SPDX-License-Identifier: MIT

import pygit2
import os
import email.utils

path = pygit2.discover_repository(os.getcwd())
repo = pygit2.Repository(path)
commit = repo.revparse_single(repo.head.name)

old_sig = commit.author
if "via lists.openembedded.org" in old_sig.name:
    target_email = old_sig.email.split("@")[0].replace("=", "@")
    print(f"Looking for {target_email}")
    # Can't use commit.message_trailers as that is a dict so doesn't preserve
    # multiple S-o-b (https://github.com/libgit2/pygit2/issues/1170)
    for line in commit.message.splitlines():
        if "Signed-off-by" in line and target_email in line:
            addr = line.split(":")[1].strip()
            name, email = email.utils.parseaddr(addr)

            signature = pygit2.Signature(name, email, old_sig.time, old_sig.offset)
            repo.amend_commit(commit, repo.head.name, author=signature)
            break
