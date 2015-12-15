#! /usr/bin/env python

# TODO
# - option to just list all broken files
# - test suite
# - validate signed-off-by


class Result:
    # Whether the patch has an Upstream-Status or not
    missing_upstream_status = False
    # If the Upstream-Status tag is malformed in some way (string for bad bit)
    malformed_upstream_status = None
    # If the Upstream-Status value is unknown (boolean)
    unknown_upstream_status = False
    # The upstream status value (Pending, etc)
    upstream_status = None

def blame_patch(patch):
    """
    From a patch filename, return a list of "commit summary (author name <author
    email>)" strings representing the history.
    """
    import subprocess
    return subprocess.check_output(("git", "log",
                                    "--follow", "--find-renames", "--diff-filter=A",
                                    "--format=%s (%aN <%aE>)",
                                    "--", patch)).splitlines()

def patchreview(patches):
    import re

    # Optional whitespace, Upstream Status with optional hyphen or space, maybe
    # a colon, some whitespace, then the first word, case insensitive.
    status_re = re.compile(r"[\t ]*(Upstream[- ]Status:?)[\t ]*(\w*)", re.IGNORECASE)

    status_values = ("accepted", "pending", "inappropriate", "backport", "submitted", "denied")

    results = {}

    for patch in patches:
        result = Result()
        results[patch] = result

        # Find the Upstream-Status tag
        content = file(patch).read()
        match = status_re.search(content)
        if not match:
            result.missing_upstream_status = True
            continue

        value = match.group(1)
        if value != "Upstream-Status:":
            result.malformed_upstream_status = value

        value = match.group(2).lower()
        # TODO: check case
        if value not in status_values:
            result.unknown_upstream_status = True
        result.upstream_status = value

    return results


def analyse(results, want_blame=False, verbose=True):
    """
    want_blame: display blame data for each malformed patch
    verbose: display per-file results instead of just summary
    """

    # want_blame requires verbose, so disable blame if we're not verbose
    if want_blame and not verbose:
        want_blame = False

    total_patches = 0
    missing_status = 0
    malformed_status = 0
    pending_patches = 0

    for patch in sorted(results):
        r = results[patch]
        total_patches += 1
        need_blame = False

        # Build statistics
        if r.missing_upstream_status:
            missing_status += 1
        if r.malformed_upstream_status or r.unknown_upstream_status:
            malformed_status += 1
        if r.upstream_status == "pending":
            pending_patches += 1

        # Output warnings
        if r.missing_upstream_status:
            need_blame = True
            if verbose:
                print "Missing Upstream-Status tag (%s)" % patch
        if r.malformed_upstream_status:
            need_blame = True
            if verbose:
                print "Malformed Upstream-Status '%s' (%s)" % (r.malformed_upstream_status, patch)
        if r.unknown_upstream_status:
            need_blame = True
            if verbose:
                print "Unknown Upstream-Status value '%s' (%s)" % (r.upstream_status, patch)

        if want_blame and need_blame:
            print "\n".join(blame_patch(patch)) + "\n"

    def percent(num):
        try:
            return "%d (%d%%)" % (num, round(num * 100.0 / total_patches))
        except ZeroDivisionError:
            return "N/A"

    if verbose:
        print

    print """Total patches found: %d
Patches missing Upstream-Status: %s
Patches with malformed Upstream-Status: %s
Patches in Pending state: %s""" % (total_patches,
                                   percent(missing_status),
                                   percent(malformed_status),
                                   percent(pending_patches))



def histogram(results):
    from toolz import recipes, dicttoolz
    import math
    counts = recipes.countby(lambda r: r.upstream_status, results.itervalues())
    bars = dicttoolz.valmap(lambda v: "#" * int(math.ceil(float(v) / len(results) * 100)), counts)
    for k in bars:
        print "%-20s %s (%d)" % (k.capitalize() if k else "No status", bars[k], counts[k])


if __name__ == "__main__":
    import argparse, subprocess

    args = argparse.ArgumentParser(description="Patch Review Tool")
    args.add_argument("-b", "--blame", action="store_true", help="show blame for malformed patches")
    args.add_argument("-v", "--verbose", action="store_true", help="show per-patch results")
    args.add_argument("-g", "--histogram", action="store_true", help="show patch histogram")
    args = args.parse_args()

    patches = subprocess.check_output(("git", "ls-files", "*.patch", "*.diff")).split()
    results = patchreview(patches)
    analyse(results, want_blame=args.blame, verbose=args.verbose)
    if args.histogram:
        print
        histogram(results)
