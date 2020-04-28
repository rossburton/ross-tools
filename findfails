#! /usr/bin/env python3

# Given a bitbake log, identify what tasks were running in parallel with any
# failed tasks.
#
# Helpful when you suspect that there is a race in the build tree, such as two
# tasks writing to the same file.
#
# Licensed under the GPLv2.

import sys, re

started_re = re.compile(r"NOTE: recipe (?P<recipe>.+): task (?P<task>.+): Started")
ended_re = re.compile(r"NOTE: recipe (?P<recipe>.+): task (?P<task>.+): Succeeded")
failed_re = re.compile(r"NOTE: recipe (?P<recipe>.+): task (?P<task>.+): Failed")

def name(match):
    return match.group("recipe") + ":" + match.group("task")

active = set()
for line in open(sys.argv[1], encoding="utf-8"):
    m = started_re.search(line)
    if m:
        active.add(name(m))
        continue

    m = ended_re.search(line)
    if m:
        active.remove(name(m))
        continue

    m = failed_re.search(line)
    if m:
        task = name(m)
        print("Task %s failed" % task)
        print("Active tasks are:")
        for t in active:
            print(" %s" % t)
        print()

        active.remove(task)
        continue
