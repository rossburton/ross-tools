#! /usr/bin/env python

# TODO
# - options to show full details or just summary
# - option to just list all broken files
# - test suite
# - blame for pending patches




def patchreview(patches):
    import re

    # Optional whitespace, Upstream Status with optional hyphen or space, maybe
    # a colon, some whitespace, then the first word, case insensitive.
    status_re = re.compile(r"\n?[\t ]*(Upstream[- ]Status:?)[\t ]*(\w*)", re.IGNORECASE)

    status_values = ("accepted", "pending", "inappropriate", "backport", "submitted", "denied")

    total_patches = 0
    patches_with_status = 0
    malformed_status = 0
    pending_patches = 0

    for patch in patches:
        total_patches += 1
        valid = True

        # Find the Upstream-Status tag
        content = file(patch).read()
        match = status_re.search(content)
        if not match:
            print "Missing Upstream-Status tag (%s)" % patch
            continue

        patches_with_status += 1
        value = match.group(1)
        if value != "Upstream-Status:":
            print "Malformed Upstream-Status tag name '%s' (%s)" % (value, patch)
            valid = False

        value = match.group(2).lower()
        # TODO: check case
        if value not in status_values:
            print "Unknown Upstream-Status value '%s' (%s)" % (value, patch)
            valid = False
        if value == "pending":
            pending_patches += 1

        if not valid:
            malformed_status += 1


    print
    print """Total patches found: %d
Patches missing Upstream-Status: %d
Patches with malformed Upstream-Status: %d
Patches in Pending state: %d""" % (total_patches,
                                   total_patches - patches_with_status,
                                   malformed_status,
                                   pending_patches)


if __name__ == "__main__":
    import subprocess
    patches = subprocess.check_output(("git", "ls-files", "*.patch", "*.diff")).split()
    patchreview(patches)
