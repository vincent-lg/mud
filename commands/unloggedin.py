"""
A login menu using EvMenu.

Contribution - Vincent-lg 2016

This module defines a simple login system, similar to the one
defined in 'menu_login.py".  This present menu system, however,
uses EvMenu (hence the name).  This module contains the
functions (nodes) of the menu, with the CmdSet and
UnloggedCommand called when a user logs in.  In other words,
instead of using the 'connect' or 'create' commands once on the
login screen, players have to navigate through a simple menu
asking them to enter their username (then password), or to type
'new' to create one.  You may want to update your login screen
if you use this system.

When you'll reload the server, new sessions will connect to the
new login system, where they will be able to:

* Enter their username, assuming they have an existing player.
* Enter 'NEW' to create a new player.

The top-level functions in this file are menu nodes (as
described in EvMenu).  Each one of these functions is
responsible for prompting the user with a specific information
(username, password and so on).  At the bottom of the file are
defined the CmdSet for Unlogging users, which adds a new command
(defined below) that is called just after a new session has been
created, in order to create the menu.  See the specific
documentation on functions (nodes) to see what each one should
do.

"""

from random import choice
import re
from textwrap import dedent

from django.conf import settings

from evennia import Command, CmdSet
from evennia import logger
from evennia import managers
from evennia import ObjectDB
from evennia.server.models import ServerConfig
from evennia import syscmdkeys
from evennia.utils.evmenu import EvMenu
from evennia.utils.utils import random_string_from_module

from services import email
from typeclasses.scripts import WrongPassword

## Constantses

RE_VALID_USERNAME = re.compile(r"^[a-z]{3,}$", re.I)
LEN_PASSWD = 6
CONNECTION_SCREEN_MODULE = settings.CONNECTION_SCREEN_MODULE

## Menu notes (top-level functions)

def start(caller):
    """The user should enter his/her username or NEW to create one.

    This node is called at the very beginning of the menu, when
    a session has been created OR if an error occurs further
    down the menu tree.  From there, users can either enter a
    username (if this username exists) or type NEW (capitalized
    or not) to create a new player.

    """
    text = random_string_from_module(CONNECTION_SCREEN_MODULE)
    text += "\n\nEnter your username or |yNEW|n to create one."
    options = (
        {
            "key": "new",
            "desc": "Create a new character.",
            "goto": "create_account",
        },
        {
            "key": "_default",
            "desc": "Login to a valid username.",
            "goto": "username",
        },
    )
    return text, options

def username(caller, input):
    """Check that the username leads to an existing player.

    Check that the specified username exists.  If the username doesn't
    exist, display an error message and ask the user to either
    enter 'b' to go back, or to try again.
    If it does exist, move to the next node (enter password).

    """
    input = input.strip()
    player = managers.players.get_player_from_name(input)
    if player is None:
        text = dedent("""
            |rThe username {} doesn't exist yet.  Have you created it?|n
                Type |yb|n to go back to the previous menu.
                Or try another name.
        """.strip("\n")).format(input)
        options = (
            {
                "key": "b",
                "desc": "Back to the previous menu.",
                "goto": "start",
            },
            {
                "key": "_default",
                "desc": "Try again.",
                "goto": "username",
            },
        )
    else:
        caller.ndb._menutree.player = player
        locked = player.db._locked
        if locked:
            text = "Please wait..."
            scripts = player.scripts.get("wrong_password")
            if scripts:
                script = scripts[0]
                script.db.session = caller
            else:
                print "Cannot retrieve the 'wrong_password' script."
        else:
            text = "Enter the password for the {} account.".format(
                    player.name)

        # Disables echo for the password
        caller.msg(echo=False)
        options = (
            {
                "key": "_default",
                "desc": "Enter your account's password.",
                "goto": "password",
            },
        )

    return text, options

def password(caller, input):
    """Ask the user to enter the password to this player.

    This is assuming the user exists (see 'create_username' and
    'create_password').  This node "loops" if needed:  if the
    user specifies a wrong password, offers the user to try
    again or to go back by entering 'b'.
    If the password is correct, then login.

    """
    menutree = caller.ndb._menutree
    caller.msg(echo=True)
    input = input.strip()
    text = ""
    options = (
        {
            "key": "_default",
            "desc": "Enter your password.",
            "goto": "choose_character",
        },
    )

    # Check the password and login if correct
    if not hasattr(menutree, "player"):
        text = dedent("""
            |rSomething went wrong!  The player was not remembered
            from last step!|n
            Press RETURN to continue.
        """.strip("\n"))
        # Redirects to the first node
        options = (
            {
                "key": "_default",
                "desc": "Press RETURN to continue.",
                "goto": "start",
            },
        )
    else:
        player = menutree.player
        if player.db._locked:
            text = "Please wait, you cannot enter your password yet."
            return text, options

        caller.msg(echo=True)
        bans = ServerConfig.objects.conf("server_bans")
        banned = bans and (any(tup[0] == player.name.lower() for tup in bans) \
                or any(tup[2].match(caller.address) for tup in bans if tup[2]))
        if not player.check_password(input):
            caller.msg(echo=False)
            text = dedent("""
                |rIncorrect password.|n
                    Type |yb|n to go back to the login screen.
                    Or wait 3 seconds before trying a new password.
            """.strip("\n"))
            # Loops on the same node
            player.scripts.add(WrongPassword)
            scripts = player.scripts.get("wrong_password")
            if scripts:
                script = scripts[0]
                script.db.session = caller
            else:
                print "Cannot retrieve the 'wrong_password' script."

            options = (
                {
                    "key": "b",
                    "desc": "Go back to the login screen.",
                    "goto": "start",
                },
                {
                    "key": "_default",
                    "desc": "Enter your password again.",
                    "goto": "password",
                },
            )
        elif banned:
            # This is a banned IP or name!
            string = dedent("""
                |rYou have been banned and cannot continue from here.
                If you feel this ban is in error, please email an admin.|x
            """.strip("\n"))
            caller.msg(string)
            caller.sessionhandler.disconnect(
                    caller, "Good bye! Disconnecting...")
        else:
            # Password is correct, we can log into the player.
            caller.ndb._menutree.player = player
            if not player.db.email_address:
                text = _email_address(player)
                options = (
                    {
                        "key": "_default",
                        "desc": "Enter your e-mail address.",
                        "goto": "email_address",
                    },
                )
            elif not player.db.valid:
                text = "Enter your received validation code."
                options = (
                    {
                        "key": "_default",
                        "desc": "Enter your validation code.",
                        "goto": "validate_account",
                    },
                )
            else:
                text = _choose_characters(player)
                options = (
                    {
                        "key": "_default",
                        "desc": "Enter a number.",
                        "goto": "choose_characters",
                    },
                )

    return text, options

def choose_characters(caller, input):
    """Log into one of this player's characters."""
    menutree = caller.ndb._menutree
    text = ""
    options = (
        {
            "key": "_default",
            "desc": "Press RETURN to continue.",
            "goto": "start",
        },
    )

    if not hasattr(menutree, "player"):
        text = dedent("""
            |rSomething went wrong!  The player was not remembered
            from last step!|n
            Press RETURN to continue.
        """.strip("\n"))
        # Redirects to the first node
    else:
        player = menutree.player
        input = input.strip()
        # Search for a valid character
        found = False
        for i, character in enumerate(player.db._playable_characters):
            if input == str(i + 1):
                found = True
                caller.sessionhandler.login(caller, player)
                player.puppet_object(caller, character)
                break

        if not found:
            text = "|rThis character cannot be found. Try again.|n"
            text += "\n" + _choose_characters(player)

    return text, options

def create_account(caller):
    """Create a new account.

    This node simply prompts the user to entere a username.
    The input is redirected to 'create_username'.

    """
    text = "Enter your new account's name."
    options = (
        {
            "key": "_default",
            "desc": "Enter your new username.",
            "goto": "create_username",
        },
    )
    return text, options

def create_username(caller, input):
    """Prompt to enter a valid username (one that doesnt exist).

    'input' contains the new username.  If it exists, prompt
    the username to retry or go back to the login screen.

    """
    menutree = caller.ndb._menutree
    input = input.strip()
    player = managers.players.get_player_from_name(input)
    options = (
        {
            "key": "_default",
            "desc": "Enter your new account's password.",
            "goto": "create_password",
        },
    )

    # If a player with that name exists, a new one will not be created
    if player:
        text = dedent("""
            |rThe account {} already exists.|n
                Type |yb|n to go back to the login screen.
                Or enter another username to create.
        """.strip("\n")).format(input)
        # Loops on the same node
        options = (
            {
                "key": "b",
                "desc": "Go back to the login screen.",
                "goto": "start",
            },
            {
                "key": "_default",
                "desc": "Enter another username.",
                "goto": "create_username",
            },
        )
    elif not RE_VALID_USERNAME.search(input):
        text = dedent("""
            |rThis username isn't valid.|n
            Only letters are accepted, without special characters.
            The username must be at least 3 characters long.
                Type |yb|n to go back to the login screen.
                Or enter another username to be created.
        """.strip("\n"))
        options = (
            {
                "key": "b",
                "desc": "Go back to the login screen.",
                "goto": "start",
            },
            {
                "key": "_default",
                "desc": "Enter another username.",
                "goto": "create_username",
            },
        )
    else:
        menutree.playername = input
        # Disables echo for entering password
        caller.msg(echo=False)
        # Redirects to the creation of a password
        text = "Enter this account's new password."
        options = (
            {
                "key": "_default",
                "desc": "Enter this account's new password.",
                "goto": "create_password",
            },
        )

    return text, options

def create_password(caller, input):
    """Ask the user to create a password.

    This node is at the end of the menu for account creation.  If
    a proper MULTI_SESSION is configured, a character is also
    created with the same name (we try to login into it).

    """
    menutree = caller.ndb._menutree
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

    if not hasattr(menutree, 'playername'):
        text = dedent("""
            |rSomething went wrong!  Playername not remembered
            from previous step!|n
            Press RETURN to go back to the login screen.
        """.strip("\n"))
        # Redirects to the starting node
        options = (
            {
                "key": "_default",
                "desc": "Go back to the login screen.",
                "goto": "start",
            },
        )
    else:
        playername = menutree.playername
        if len(password) < LEN_PASSWD:
            caller.msg(echo=False)
            # The password is too short
            text = dedent("""
                |rYour password must be at least {} characters long.|n
                    Type |yb|n to return to the login screen.
                    Or enter another password.
            """.strip("\n")).format(LEN_PASSWD)
        else:
            # Everything's OK.  Create the new player account and
            # possibly the character, depending on the multisession mode
            from evennia.commands.default import unloggedin
            # We make use of the helper functions from the default set here.
            options = (
                {
                    "key": "_default",
                    "desc": "Go back to the login screen.",
                    "goto": "start",
                },
            )

            try:
                permissions = settings.PERMISSION_PLAYER_DEFAULT
                typeclass = settings.BASE_CHARACTER_TYPECLASS
                new_player = unloggedin._create_player(caller, playername,
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
                text = "Your new account was successfully created!"
                text += "\n\n" + _email_address(player)
                options = {
                    {
                        "key": "_default",
                        "desc": "Enter a valid e-mail address.",
                        "goto": "email_address",
                    },
                }

    return text, options

def email_address(caller, input):
    """Prompt the user to enter a valid email address."""
    menutree = caller.ndb._menutree
    text = ""
    options = (
        {
            "key": "b",
            "desc": "Go back to the login screen.",
            "goto": "start",
        },
        {
            "key": "_default",
            "desc": "Enter a valid e-mail address.",
            "goto": "email_address",
        },
    )

    email_address = input.strip()

    if not hasattr(menutree, 'player'):
        text = dedent("""
            |rSomething went wrong!  The player not remembered
            from previous step!|n
            Press RETURN to go back to the login screen.
        """.strip("\n"))
        # Redirects to the starting node
        options = (
            {
                "key": "_default",
                "desc": "Go back to the login screen.",
                "goto": "start",
            },
        )
    else:
        player = menutree.player
        if not email.is_email_address(email_address):
            # The password is too short
            text = dedent("""
                |rSorry, the specified e-mail address {} cannot be
                accepted as a valid one.|n  You can:
                    Type |yb|n to return to the login screen.
                    Or enter another e-mail address.
            """.strip("\n")).format(email_address)
        else:
            player.db.email_address = email_address
            # Generate the 10-digit number
            numbers = "012345678"
            code = ""
            for i in range(4):
                code += choice(numbers)

            # Sends an e-mail with the code
            subject = "Account validation"
            body = dedent("""
                You have successfully created the account {} on that MUD.

                In order to validate it and begin to play, you need to
                enter the following four-digit code in your MUD client.
                If you have been disconnected, just login again, entering
                your account's name and password, the validation screen
                will be displayed again.

                Four-digit code: {}
            """.strip("\n")).format(player.name, code)
            recipent = email_address
            error = "The account {}'s validation code is {}.".format(
                    player.name, code)
            player.db.valid = False
            player.db.validation_code = code
            email.send("origin@kassie.fr", recipent, subject, body, error)
            text = dedent("""
                An email has been sent to {}.  It contains your validation
                code which you'll need to finish creating your account.
                If you haven't received the validation e-mail after some
                minutes have passed, check your spam folder to see if
                it's inside of it.  If not, you might try to select
                another e-mail address, or contact an administrator.

                From here you can:
                    Type |yb|n to comeback to the e-mail address selection.
                    Enter your received confirmation code.
                """.strip("\n")).format(email_address)
            options = (
                {
                    "key": "b",
                    "desc": "Go back to the e-mail address selection.",
                    "goto": "email_address",
                },
                {
                    "key": "_default",
                    "desc": "Enter your validation code.",
                    "goto": "validate_account",
                },
            )

    return text, options

def validate_account(caller, input):
    """Prompt the user to enter the received validation code."""
    menutree = caller.ndb._menutree
    text = ""
    options = (
        {
            "key": "b",
            "desc": "Go back to the login screen.",
            "goto": "email_address",
        },
        {
            "key": "_default",
            "desc": "Enter the validation code.",
            "goto": "validate_account",
        },
    )

    if not hasattr(menutree, 'player'):
        text = dedent("""
            |rSomething went wrong!  The player not remembered
            from previous step!|n
            Press RETURN to go back to the login screen.
        """.strip("\n"))
        # Redirects to the starting node
        options = (
            {
                "key": "_default",
                "desc": "Go back to the login screen.",
                "goto": "start",
            },
        )
    else:
        player = menutree.player
        if player.db.validation_code != input.strip():
            text = dedent("""
                |rSorry, the specified validation code {} doesn't match
                the one stored for this account.  Is it the code you
                received by e-mail?  You can try to enter it again, or
                enter |yb|n to choose a different e-mail address.
            """.strip("\n")).format(input.strip())
        else:
            player.db.valid = True
            player.attributes.remove("validation_code")
            text = "This account has successfully been validated!"
            text += "\n\n" + _choose_characters(player)
            options = (
                {
                    "key": "_default",
                    "desc": "Login to a valid character.",
                    "goto": "choose_characters",
                },
            )

    return text, options

## Other functions

def _formatter(nodetext, optionstext, caller=None):
    """Do not display the options, only the text.

    This function is used by EvMenu to format the text of nodes.
    Options are not displayed for this menu, where it doesn't often
    make much sense to do so.  Thus, only the node text is displayed.

    """
    return nodetext

def _choose_characters(player):
    """Display the menu to choose a character."""
    text = "Enter a valid number to log into that character.\n"
    characters = player.db._playable_characters
    if characters:
        for i, character in enumerate(characters):
            text += "\n  |y{}|n - Log into {}.".format(str(i + 1),
                    character.name)
    else:
        text += "\n  |gNo character has been created in this account yet.|n"

    return text

def _email_address(player):
    """Return the prompt to enter an e-mail address."""
    text = dedent("""
        Enter a valid e-mail address for the account {}.

        An e-mail confirmation will be sent to this address with a
        four-digit code that you will have to enter to validate this
        account.  This e-mail address will be used only by the staff
        if needed.  You will be able to update this e-mail address if
        desired.

        Your email address :
    """.strip("\n")).format(player.name)
    return text

## Commands and CmdSets

class UnloggedinCmdSet(CmdSet):
    "Cmdset for the unloggedin state"
    key = "DefaultUnloggedin"
    priority = 0

    def at_cmdset_creation(self):
        "Called when cmdset is first created."
        self.add(CmdUnloggedinLook())


class CmdUnloggedinLook(Command):
    """
    An unloggedin version of the look command. This is called by the server
    when the player first connects. It sets up the menu before handing off
    to the menu's own look command.
    """
    key = syscmdkeys.CMD_LOGINSTART
    locks = "cmd:all()"
    arg_regex = r"^$"

    def func(self):
        "Execute the menu"
        menu = EvMenu(self.caller, "commands.unloggedin", startnode="start",
                auto_quit=False, node_formatter=_formatter, cmd_on_exit=None)
