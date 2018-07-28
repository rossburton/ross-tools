#! /usr/bin/env python3

import argparse, sys, subprocess, os
import arrow

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--checkout", action="store_true", default=False)
parser.add_argument("-s", "--since", required=True)
parser.add_argument("-b", "--branch", default="HEAD")
parser.add_argument('command', nargs=argparse.REMAINDER)
args = parser.parse_args()

date = then = arrow.get(args.since, "YYYY-MM-DD")
tip = subprocess.check_output(["git", "rev-parse", args.branch]).decode("ascii").strip()

# TODO argparse this
shift = {"months": +1}

# TODO save/restore current checkout

now = arrow.utcnow()
env = os.environ.copy()
while date < now:
    print("%s..." % date.format("YYYY-MM-DD"))
    env["DATE"] = date.format("YYYY-MM-DD")
    env["NEXTDATE"] = date.shift(**shift).format("YYYY-MM-DD")

    sha = subprocess.check_output(["git", "rev-list", tip, "--before", date.format("YYYY-MM-DD"), "--max-count=1"]).decode("ascii").strip()
    if args.checkout:
        # TODO use worktree?
        subprocess.check_output(["git", "checkout", "--quiet", sha])

    output = subprocess.check_output(" ".join(args.command), shell=True, env=env).decode("utf-8")
    print(output)
    # TODO option to write to named file?

    date = date.shift(**shift)
