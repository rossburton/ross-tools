#! /usr/bin/env python

# Copyright (C) 2015 Ross Burton <ross.burton@intel.com>
# MIT licensed

import email, subprocess, os, sys

class PatchSource:
      def enumerate(self):
            """
            Return a summary of the patches to be applied as a list of strings.
            """
            pass

      def apply(self):
            """
            Apply the patches, raising an exception if there is an error.
            """
            pass

class ClipboardPatch(PatchSource):
      def __init__(self):
            import tempfile

            # Save the clipboard contents for passing to git-am in apply()
            # TODO: respect platform, eg pbcopy for osx
            self.mail = subprocess.check_output(["xsel", "-b"])

            # Check the clipboard contains something that looks like a patch.
            # As the clipboard contains an email it could be encoded, so use
            # git-mailinfo to extract the patch itself first.  It's a shame
            # git-am doesn't have a --dry-run option.
            with tempfile.NamedTemporaryFile(prefix="applyotron") as patchfile:
                  process = subprocess.Popen(["git", "mailinfo", "/dev/null", patchfile.name],
                                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                  process.communicate(self.mail)
                  retcode = process.wait()
                  if retcode:
                        raise subprocess.CalledProcessError(retcode, "git-mailinfo")

                  process = subprocess.check_call(["git", "apply", "--check", patchfile.name])

      def enumerate(self):
            return (email.message_from_string(self.mail)["Subject"],)

      def apply(self):
            gitam = subprocess.Popen(["git", "am", "--3way", "--signoff", "--whitespace=nowarn"],
                                  stdin=subprocess.PIPE)
            gitam.communicate(self.mail)
            retcode = gitam.poll()
            if retcode:
                  raise subprocess.CalledProcessError(retcode, "git")


class FilePatch(PatchSource):
      def __init__(self, files):
            self.files = files

      def enumerate(self):
            return (email.message_from_file(open(f))["Subject"] for f in self.files)

      def apply(self):
            subprocess.check_call(["git", "am", "--3way", "--signoff", "--whitespace=nowarn"] + self.files)


class RevisionsPatch(PatchSource):
      def __init__(self, revisions):
            self.revs = revisions

      def enumerate(self):
            return subprocess.check_output(["git", "show", "--no-patch", "--format=format:%s"] + self.revs).split("\n")

      def apply(self):
            subprocess.check_call(["git", "cherry-pick", "--signoff"] + self.revs)


class GMailPatch(PatchSource):
      def __init__(self):
            server = self.connect()

            # TODO Configure this in some way.
            # l:^ss_co means "has:orange-guillemet"
            messages = server.gmail_search("in:inbox l:^ss_co")
            # TODO abort if no messages found

            # List of (msgid, mail body) pairs
            self.patches = []
            response = server.fetch(messages, ['ENVELOPE RFC822'])
            for msgid, data in sorted(response.iteritems(), key=lambda d: d[1]['ENVELOPE'].date):
                  self.patches.append((msgid, data['RFC822']))

      def connect(self):
            import ConfigParser, imapclient

            cp = ConfigParser.SafeConfigParser()
            cp.read(os.path.expanduser("~/.config/handlepatches.conf"))

            server = imapclient.IMAPClient("imap.gmail.com", ssl=True, use_uid=True)
            server.login(cp.get("Config", "IMAPUSer"), cp.get("Config", "IMAPPassword"))
            server.select_folder("INBOX")
            return server

      def enumerate(self):
            return (email.message_from_string(mail)["Subject"] for msgid, mail in self.patches)

      def apply(self):
            server = self.connect()
            for msgid, mail in self.patches:
                  import imapclient
                  # TODO: verify that the subject contains PATCH?
                  gitam = subprocess.Popen(['git', 'am', '--3way', '--signoff', '--whitespace=nowarn'],
                                           stdin=subprocess.PIPE)
                  gitam.communicate(mail)
                  retcode = gitam.wait()
                  if retcode:
                        raise subprocess.CalledProcessError(retcode, 'git')

                  server.add_flags(msgid, imapclient.SEEN)
                  server.remove_flags(msgid, imapclient.FLAGGED)
                  server.delete_messages(msgid)

            server.close_folder()
            server.logout()

def wipe_sysroot():
      subprocess.check_call(["wipe-sysroot"])

def build(targets):
      subprocess.check_call(["bitbake"] + targets)

def buildhistory():
      subprocess.check_call(["buildhistory-diff"])


def main():
      import argparse

      args = argparse.ArgumentParser(description="Applyotron")
      args.add_argument("-l", "--list", action="store_true", help="List patches found, but don't build or apply")
      group = args.add_mutually_exclusive_group(required=True)
      group.add_argument("-c", "--clipboard", action="store_true", help="Take patch from clipboard")
      group.add_argument("-f", "--file", action="append", help="Take patch from file")
      group.add_argument("-r", "--revisions", action="append", help="Cherry-pick revision range")
      group.add_argument("-m", "--mail", action="store_true", help="Take patches from GMail")
      args.add_argument("target", nargs="*", help="targets to build")
      args = args.parse_args()

      if args.clipboard:
            patch = ClipboardPatch()
      elif args.file:
            patch = FilePatch(args.file)
      elif args.revisions:
            patch = RevisionsPatch(args.revisions)
      elif args.mail:
            patch = GMailPatch()
      else:
            print "No patch source selected"
            sys.exit(os.EX_USAGE)

      patches = list(patch.enumerate())
      if patches:
            print "Applying the following %d patches:" % (len(patches))
            for p in patches:
                print " %s" % p
      else:
            print "No patches found to apply."
            sys.exit(os.EX_NOINPUT)

      if args.list:
            # And we're done
            sys.exit(os.EX_OK)

      if args.target:
            # TODO Exception handling. If I control-C applyotron the
            # childs keep on running. This is bad.
            targets = args.target
            build(targets)
            patch.apply()
            wipe_sysroot()
            build(targets)
            buildhistory()
      else:
            patch.apply()


if __name__ == "__main__":
      main()
