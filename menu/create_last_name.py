"""
This module contains the 'create_last_name' menu node.

"""

import re
from textwrap import dedent

from typeclasses.characters import Character

## Constants
RE_VALID_LAST_NAME = re.compile(r"^[a-z -]{2,}$", re.I)

def create_last_name(caller, input):
    """Prompt the new character for his/her last name."""
    input = input.strip()

    last_name = " ".join(word.capitalize() for word in input.split(" "))
    first_name = caller.db._first_name
    full_name = first_name + " " + last_name

    # Gets the characters with the same name
    characters = Character.objects.filter(db_key=full_name)
    if not RE_VALID_LAST_NAME.search(input):
        text = dedent("""
            |rSorry, this last name is not valid.|n
            A correct last name may contain letters (and possibly
            spaces), without special characters.  You can:
                Type |yb|n to go back to the first name selection.
                Or enter this character's last name again.
        """.strip("\n"))
        options = (
            {
                "key": "b",
                "desc": "Go back to the first name selection.",
                "goto": "create_first_name",
            },
            {
                "key": "_default",
                "desc": "Enter another last name.",
                "goto": "create_last_name",
            },
        )
    elif len(characters) > 0:
        text = dedent("""
            |rA character named {} already exists.  You can:
                Type |yb|n to go back to the first name selection.
                Or enter this character's last name again.
        """.strip("\n"))
        options = (
            {
                "key": "b",
                "desc": "Go back to the first name selection.",
                "goto": "create_first_name",
            },
            {
                "key": "_default",
                "desc": "Enter another last name.",
                "goto": "create_last_name",
            },
        )
    else:
        caller.db._full_name = full_name
        del caller.db._first_name

        # Redirects to the gender selection.
        text = dedent("""
            The police officer nods and scribbles on his pad.
                'Nice name, I s'pose.  What gender should I indicate here?'
                Select your gender (|yF|n/|yM|n).
        """.strip("\n"))
        options = (
            {
                "key": "_default",
                "desc": "Enter your gender (F or M).",
                "goto": "select_gender",
            },
        )

    return text, options
