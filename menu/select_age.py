"""
This module contains the 'select_age' menu node.

"""

from textwrap import dedent

from django.conf import settings

from evennia import ObjectDB
from evennia.utils import create

def select_age(caller, input):
    """Prompt the new character for his/her age."""
    age = input.strip()

    try:
        age = int(age)
    except ValueError:
        age = None

    if age is None:
        text = dedent("""
            The police officer scratches his head thoughtfully.
                'Sorry, I didn't quite catch that.'
                Please enter your character's age again.
        """.strip("\n"))
        options = (
            {
                "key": "_default",
                "desc": "Select this character's age.",
                "goto": "select_age",
            },
        )
    else:
        player = caller.db._player
        full_name = caller.db._full_name
        female = caller.db._female
        title = "ma'am" if female else "sir"
        options = (
            {
                "key": "_default",
                "desc": "Enter your character's age.",
                "goto": "select_age",
            },
        )

        # There are invalid choices
        if age < 0:
            text = dedent("""
                The police officer steps back in surprise.
                    'Now, how's that possible?  Probably a mistake he?'
                    Please enter your character's age again.
            """.strip("\n"))
        elif age < 10:
            text = dedent("""
                The police officer gazes at you in surprise.
                    'Shouldn't you be in the backseat?  Okay, I'm sorry,
                    but it's a bit too young to drive, don't you think?'
                    Please enter your character's age again.
            """.strip("\n"))
        elif age < 18:
            text = dedent("""
                The police officer looks you up and down.
                    'Well kid, I don't mean to sound offensive or anything,
                    but you can't drive a car at that age.  As far as I'm
                    concerned, you can lie, but be convincing.'
                    Please enter your character's age again.
            """.strip("\n"))
        else:
            text = dedent("""
                The police officer takes a final note on his pad.
                    'That will do!  Have a good stay with us, {title}.
                The police officer steps back and waves your car through the
                checkpoint.  After a few minute drive, you park in front of
                a large building.  You get off your car, lock the door
                behind you, and walk toward the building, stopping a few feet
                away from the main entrance inside.
            """.strip("\n")).format(title=title)

            # Create the character
            character = create_character(full_name, player)
            character.db.female = female
            character.db.age = age
            del caller.db._player
            del caller.db._full_name
            del caller.db._female

            # Connects on this character
            caller.msg(text)
            caller.sessionhandler.login(caller, player)
            player.puppet_object(caller, character)
            return "", None

    return text, options

def create_character(name, player):
    """Create a new character.

    Args:
        name: the name of the character to be created
        player: the player owning the character.

    Return:
        The newly-created character.

    """
    # Look for default values
    permissions = settings.PERMISSION_PLAYER_DEFAULT
    typeclass = settings.BASE_CHARACTER_TYPECLASS
    home = ObjectDB.objects.get_id(settings.DEFAULT_HOME)

    # Create the character
    character = create.create_object(typeclass, key=name, home=home,
            permissions=permissions)

    # Set playable character list
    player.db._playable_characters.append(character)

    # Allow only the character itself and the player to puppet it.
    character.locks.add("puppet:id(%i) or pid(%i) or perm(Immortals) " \
            "or pperm(Immortals)" % (character.id, player.id))

    # If no description is set, set a default description
    if not character.db.desc:
        character.db.desc = ""

    # We need to set this to have @ic auto-connect to this character.
    player.db._last_puppet = character

    return character
