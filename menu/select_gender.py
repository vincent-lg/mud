"""
This module contains the 'select_gender' menu node.

"""

from textwrap import dedent

def select_gender(caller, input):
    """Prompt the new character for his/her gender."""
    gender = input.strip().lower()
    if gender not in "mf":
        text = dedent("""
            The police officer scratches his head thoughtfully.
                'Sorry, I didn't catch that.'
                Enter |yF|n for female or |yM|n for male.
        """.strip("\n"))
        options = (
            {
                "key": "_default",
                "desc": "Select this character's gender.",
                "goto": "select_gender",
            },
        )
    else:
        female = True if gender == "f" else False
        title = "ma'am" if female else "sir"
        caller.db._female = female

        text = dedent("""
            The police officer nods and scribbles on his pad.
                'Thank you {title}.  We're almost done.  I just need to know
                your age.'
                Enter your character's age.
        """.strip("\n")).format(title=title)
        options = (
            {
                "key": "_default",
                "desc": "Enter your character's age.",
                "goto": "select_age",
            },
        )

    return text, options
