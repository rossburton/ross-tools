#! /usr/bin/env python

# TODO
# - options to show full details or just summary
# - option to just list all broken files
# - test suite
# - blame for pending patches



class Result:
    # Whether the patch has an Upstream-Status or not
    missing_upstream_status = False
    # If the Upstream-Status tag is malformed in some way (string for bad bit)
    malformed_upstream_status = None
    # If the Upstream-Status value is unknown (boolean)
    unknown_upstream_status = False
    # The upstream status value (Pending, etc)
    upstream_status = None
    # The full matched Upstream-Status line
    upstream_status_line = None

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
            print "Missing Upstream-Status tag (%s)" % patch
            result.missing_upstream_status = True
            continue

        result.upstream_status_line = match.group(0)
        value = match.group(1)
        if value != "Upstream-Status:":
            result.malformed_upstream_status = value
            print "Malformed Upstream-Status '%s' (%s)" % (value, patch)

        value = match.group(2).lower()
        # TODO: check case
        if value not in status_values:
            result.unknown_upstream_status = True
            print "Unknown Upstream-Status value '%s' (%s)" % (value, patch)
        result.upstream_status = value

    return results


def analyse(results):
    total_patches = 0
    missing_status = 0
    malformed_status = 0
    pending_patches = 0

    for r in results.itervalues():
        total_patches += 1
        if r.missing_upstream_status:
            missing_status += 1
        if r.malformed_upstream_status or r.unknown_upstream_status:
            malformed_status += 1
        if r.upstream_status == "pending":
            pending_patches += 1

    print
    print """Total patches found: %d
Patches missing Upstream-Status: %d
Patches with malformed Upstream-Status: %d
Patches in Pending state: %d""" % (total_patches,
                                   missing_status,
                                   malformed_status,
                                   pending_patches)


if __name__ == "__main__":
    import subprocess
    patches = subprocess.check_output(("git", "ls-files", "*.patch", "*.diff")).split()
    analyse(patchreview(patches))
