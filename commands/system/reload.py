"""Modified @reload command."""

import subprocess

from evennia.commands.default.muxcommand import MuxCommand
from evennia.server.sessionhandler import SESSIONS

class CmdReload(MuxCommand):
    """
    reload the server

    Usage:
      @reload [reason]

    This restarts the server. The Portal is not
    affected. Non-persistent scripts will survive a @reload (use
    @reset to purge) and at_reload() hooks will be called.
    This command also updates the Git repository if possible.
    """
    key = "@reload"
    locks = "cmd:perm(reload) or perm(Immortals)"
    help_category = "System"

    def func(self):
        """
        Reload the system.
        """
        reason = ""
        if self.args:
            reason = "(Reason: %s) " % self.args.rstrip(".")
        # Pull the Git repository
        process = subprocess.Popen("git pull", shell=True,
                stdout=subprocess.PIPE)
        process.wait()
        if process.returncode == 0:
            self.caller.msg("The Git repository has successfully been " \
                    "updated.")
        else:
            self.caller.msg("|rAn error occurred while pulling the Git " \
                    "repository.|n")

        # Restart the server
        SESSIONS.announce_all(" Server restarting %s..." % reason)
        SESSIONS.server.shutdown(mode='reload')
