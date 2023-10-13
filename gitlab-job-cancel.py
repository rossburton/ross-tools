#! /usr/bin/env python3

# Cancel jobs in a specified pipeline that match a set of critera

import argparse
import re
import gitlab

parser = argparse.ArgumentParser()
parser.add_argument("--server", nargs="?")
parser.add_argument("--project", "-p")
parser.add_argument(
    "--pipeline",
    "-l",
    required=True,
    help="pipeline ID, or branch name for latest pipeline",
)
parser.add_argument("--stage", "-s", nargs="?")
parser.add_argument(
    "--keep",
    "-k",
    action="append",
    help="Regex to match job names to keep (can be specified multiple times)",
)
# TODO make keep exclusive with --cancel
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--use-config", "-c", action="store_true")

args = parser.parse_args()

# If we're using a configuration, load it into args and re-parse to override the settings
if args.use_config:
    import configparser, git

    repo = git.Repo(search_parent_directories=True)
    with repo.config_reader() as config:
        for key in ("project", "stage"):
            try:
                value = config.get("ross-tools", key)
                setattr(args, key, value)
            except configparser.NoOptionError:
                pass
    args = parser.parse_args(namespace=args)

# TODO check variables are set

gl = gitlab.Gitlab.from_config(args.server)
gl.auth()

project = gl.projects.get(args.project)
if args.pipeline.isdigit():
    pipeline = project.pipelines.get(args.pipeline)
else:
    pipeline = project.pipelines.list(ref=args.pipeline, get_all=False)[0]
    print(f"Found pipeline {pipeline.web_url}")

for job in pipeline.jobs.list(all=True):
    cancel = True
    if args.stage and job.stage != args.stage:
        cancel = False
    elif job.status not in ("created", "pending", "running"):
        cancel = False
    elif args.keep:
        for pattern in args.keep:
            if re.search(pattern, job.name):
                cancel = False
    # TODO cancel_name

    print(
        f"{'Cancelling' if cancel else 'Leaving'} {job.stage}:{job.name} ({job.status})"
    )
    if cancel and not args.dry_run:
        real_job = project.jobs.get(job.id, lazy=True)
        real_job.cancel()
