#! /usr/bin/env python3

import argparse
import gitlab
import subprocess

remote = "gitlab"

parser = argparse.ArgumentParser()
parser.add_argument("--close", "-l", action="store_true")
parser.add_argument("--server", nargs="?")
parser.add_argument("--project", "-p")
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

def patchid(sha):
    """
    Given a git commit hash, return a (patch-id, sha) tuple as per git-patch-id.
    """
    diff = subprocess.run(("git", "show", sha), capture_output=True, text=True, check=True)
    out = subprocess.run(("git", "patch-id", "--stable"), input=diff.stdout, capture_output=True, text=True, check=True)
    patchid, out_sha = out.stdout.strip().split(" ", 1)
    assert out_sha == sha
    return patchid, sha

def list_patch_ids(base, branch):
    """
    Given two commits, return a dictionary of patch id:sha for each commit in the range.
    """
    output = subprocess.run(("git", "rev-list", f"{base}...{branch}"), capture_output=True, text=True, check=True)
    return dict(patchid(line) for line in output.stdout.splitlines())

def get_merge_base(mr):
    """
    For a given MR, return the merge base of the source and target branches.
    """
    cmd = ("git", "merge-base", f"{remote}/{mr.target_branch}", f"{remote}/{mr.source_branch}")
    output = subprocess.run(cmd, text=True, capture_output=True, check=True)
    return output.stdout.strip()

def get_commit_summary(sha):
    """
    Return a short summary of the given commit.
    """
    return subprocess.run(("git", "show", "--format=format:%h %s", "--no-patch", sha), check=True, capture_output=True, text=True).stdout

def with_patch_id(mr):
    base = get_merge_base(mr)
    source_shas = list_patch_ids(base, f"{remote}/{mr.source_branch}")
    target_shas = list_patch_ids(base, f"{remote}/{mr.target_branch}")

    for pid, sha in source_shas.items():
        if pid not in target_shas:
            return False, [f"Cannot find {get_commit_summary(sha)}"]
    else:
        return True, [f"- {get_commit_summary(target_shas[pid])}" for pid in source_shas]

for mr in project.mergerequests.list(state="opened", iterator=True):
    if mr.draft or not mr.approvals.get().approved:
        continue

    print(f"{mr.title}")
    print(f"{mr.web_url}")

    merged, message = with_patch_id(mr)
    if merged:
        body = ["Merged in:"] + message
        for line in body: print(line)

        if args.close:
            mr_note = mr.notes.create({"body": "\n".join(body)})
            mr.state_event = "close"
            mr.save()
    else:
        print("Not merged:")
        for line in message: print(line)

    print()
