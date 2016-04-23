"""
This module contains the 'choose_characters' node menu.

"""

from textwrap import dedent

def choose_characters(caller, input):
    """Log into one of this player's characters."""
    text = ""
    options = (
        {
            "key": "_default",
            "desc": "Press RETURN to continue.",
            "goto": "start",
        },
    )

    player = caller.db._player
    input = input.strip()

    # Search for a valid character
    found = False
    for i, character in enumerate(player.db._playable_characters):
        if input == str(i + 1):
            found = True
            caller.attributes.remove("_player")
            caller.sessionhandler.login(caller, player)
            player.puppet_object(caller, character)
            break

    if not found:
        text = "|rThis character cannot be found.  Try again.|n"
        text += "\n" + text_choose_characters(player)
        options = options_choose_characters(player)

    return text, options

## Generic functions

def text_choose_characters(player):
    """Display the menu to choose a character."""
    text = "Enter a valid number to log into that character.\n"
    characters = player.db._playable_characters
    if len(characters):
        for i, character in enumerate(characters):
            text += "\n  |y{}|n - Log into {}.".format(str(i + 1),
                    character.name)
    else:
        text += "\n  No character has been created in this account yet."

    text += "\n"
    if len(characters) < 5:
        text += "\n  |yC|n to create a new character."

    if len(characters) > 0:
        text += "\n  |yD|n to delete one of your characters."

    return text

def options_choose_characters(player):
    """Return the options for choosing a character.

    The first options must be the characters name (5 are allowed
    by player).  The other nodes must be reached through letters:
    C to create, D to delete.

    """
    options = list()
    characters = player.db._playable_characters
    if len(characters) < 5:
        options.append(        {
                "key": "c",
                "desc": "Create a new character.",
                "goto": "create_character",
        })

    if len(characters) > 0:
        options.append(        {
                "key": "d",
                "desc": "Delete an existing character.",
                "goto": "delete_character",
        })

    options.append(        {
            "key": "_default",
            "desc": "Login to an existing character.",
            "goto": "choose_characters",
    })
    return tuple(options)
