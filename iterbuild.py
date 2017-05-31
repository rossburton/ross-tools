#! /usr/bin/env python3

import argparse

def do_init(args):
    import git
    repo = git.Repo(".", search_parent_directories=True)

    for commit in repo.iter_commits("%s^...%s" % (args.start, args.end), reverse=True):
        print("%s %s" % (commit.hexsha[:8], commit.summary))

def do_list(args):
    import git
    repo = git.Repo(".", search_parent_directories=True)

    for line in args.script:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        commit = repo.commit(line.split()[0])
        print("%s %s" % (commit.hexsha, commit.summary))


def do_build(args):
    import git, subprocess
    repo = git.Repo(".", search_parent_directories=True)

    shas = []
    for line in args.script:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        sha = line.split()[0]
        commit = repo.commit(sha)
        print("%s %s" % (commit.hexsha, commit.summary))
        shas.append(commit)

    def bitbake(commit):
        subprocess.check_call(["git", "checkout", "--quiet", commit.hexsha])
        subprocess.check_call(["bitbake"] + args.targets)

    def builddiff(counter, commit):
        with open("buildhistory-%d-%s.log" % (counter, commit.hexsha), "wt") as log:
            log.write("commit %s\n\n" % commit.hexsha)
            log.write(commit.message)
            log.write("\n")
            log.write(subprocess.check_output("buildhistory-diff", universal_newlines=True))

    bitbake(shas[0])
    for counter, commit in enumerate(shas[1:], start=1):
        bitbake(commit)
        builddiff(counter, commit)



parser = argparse.ArgumentParser(description='Iteratively run bitbake and buildhistory-diff for a series of commits taken from an instruction script.')
subparsers = parser.add_subparsers()

parser_list = subparsers.add_parser('init', help='generate an initial instruction script')
parser_list.add_argument('start', metavar='START', help='start commit')
parser_list.add_argument('end', metavar='END', default='HEAD', nargs='?', help='end commit')
parser_list.set_defaults(func=do_init)

parser_list = subparsers.add_parser('list', help='list the commits in the instruction script')
parser_list.add_argument('script', type=argparse.FileType('r'), metavar='SCRIPT', help='instruction script')
parser_list.set_defaults(func=do_list)

parser_build = subparsers.add_parser('build', help='run bitbake and buildhistory-diff for each commit in the script')
parser_build.add_argument('script', type=argparse.FileType('r'), metavar='SCRIPT', help='instruction script')
parser_build.add_argument('targets', metavar='TARGET', nargs='+', help='build targets')
parser_build.set_defaults(func=do_build)

args = parser.parse_args()
args.func(args)
