"""
This module contains the 'create_password' node menu.

"""

from textwrap import dedent

from django.conf import settings

from evennia import logger

from menu.email_address import text_email_address
from menu.password import LEN_PASSWD

def create_password(caller, input):
    """Ask the user to create a password.

    This node creates and validates a new password for this
    account.  It then follows up with ?).

    """
    text = ""
    options = (
        {
            "key": "b",
            "desc": "Go back to the login screen.",
            "goto": "start",
        },
        {
            "key": "_default",
            "desc": "Enter your password.",
            "goto": "create_password",
        },
    )

    caller.msg(echo=True)
    password = input.strip()

    playername = caller.db._playername
    if len(password) < LEN_PASSWD:
        caller.msg(echo=False)

        # The password is too short
        text = dedent("""
            |rYour password must be at least {} characters long.|n
                Type |yb|n to return to the login screen.
                Or enter another password.
        """.strip("\n")).format(LEN_PASSWD)
    else:
        # Creates the new player.
        from evennia.commands.default import unloggedin
        try:
            permissions = settings.PERMISSION_PLAYER_DEFAULT
            typeclass = settings.BASE_CHARACTER_TYPECLASS
            player = unloggedin._create_player(caller, playername,
                    password, permissions)
        except Exception:
            # We are in the middle between logged in and -not, so we have
            # to handle tracebacks ourselves at this point. If we don't, we
            # won't see any errors at all.
            caller.msg(dedent("""
                |rAn error occurred.|n  Please e-mail an admin if
                the problem persists.
                    Type |yb|n to go back to the login screen.
                    Or enter another password.
            """.strip("\n")))
            logger.log_trace()
        else:
            caller.db._player = player
            text = "Your new account was successfully created!"
            text += "\n\n" + text_email_address(player)
            options = (
                {
                    "key": "_default",
                    "desc": "Enter a valid e-mail address.",
                    "goto": "email_address",
                },
            )

    return text, options
