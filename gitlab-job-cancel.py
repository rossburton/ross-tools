#! /usr/bin/env python3

# Cancel jobs in a specified pipeline that match a set of critera

import argparse
import re
import gitlab

parser = argparse.ArgumentParser()
parser.add_argument("--server", nargs="?")
parser.add_argument("--project", "-p", required=True)
parser.add_argument("--pipeline", "-l", required=True, help="pipeline ID, or branch name for latest pipeline")
parser.add_argument("--stage", "-s", nargs="?")
parser.add_argument("--keep", "-k", nargs="?")
# TODO make keep exclusive with --cancel
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()

# TODO config file support (--config) which will read config for the arguments.
# etc meta-arm can set project/server/stage.

gl = gitlab.Gitlab.from_config(args.server)
gl.auth()

project = gl.projects.get(args.project)
if args.pipeline.isdigit():
    pipeline = project.pipelines.get(args.pipeline)
else:
    pipeline = project.pipelines.list(ref=args.pipeline)[0]
    print(f"Found pipeline {pipeline.web_url}")

for job in pipeline.jobs.list(all=True):
    cancel = True
    if args.stage and job.stage != args.stage:
        cancel = False
    elif job.status not in ("created", "pending", "running"):
        cancel = False
    elif args.keep and re.search(args.keep, job.name):
        cancel = False
    # TODO cancel_name

    print(f"{'Cancelling' if cancel else 'Leaving'} {job.stage}:{job.name} ({job.status})")
    if cancel and not args.dry_run:
        real_job = project.jobs.get(job.id, lazy=True)
        real_job.cancel()
