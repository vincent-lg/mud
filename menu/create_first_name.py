"""
This module contains the 'create_first_name' menu node.

"""

import re
from textwrap import dedent

## Constants
RE_VALID_FIRST_NAME = re.compile(r"^[a-z -]{2,}$", re.I)

def create_first_name(caller, input):
    """Prompt the new character for his/her first name."""
    input = input.strip()
    if not RE_VALID_FIRST_NAME.search(input):
        text = dedent("""
            |rSorry, this first name is not valid.|n
            A correct first name may contain letters (and possibly
            spaces), without special characters.  You can:
                Type |yb|n to go back to the character selection.
                Or enter this character's first name again.
        """.strip("\n"))
        options = (
            {
                "key": "b",
                "desc": "Go back to the character selection.",
                "goto": "choose_characters",
            },
            {
                "key": "_default",
                "desc": "Enter another first name.",
                "goto": "create_first_name",
            },
        )
    else:
        first_name = " ".join(word.capitalize() for word in input.split(" "))
        caller.db._first_name = first_name

        # Redirects to the creation of the last name
        text = dedent("""
            The police officer startes at you with some wariness:
                'All right, we're getting somewhere.  Would you mind
                giving me a last name now?'
        """.strip("\n"))
        options = (
            {
                "key": "_default",
                "desc": "Enter this character's last name.",
                "goto": "create_last_name",
            },
        )

    return text, options
