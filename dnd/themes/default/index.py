"""Index page."""
from pyhtml import div, h1, br
from dnd.themes.default.base import base
from dnd.html.bootstrap import (
    Style, a_button, b_button, badge, collapse, async_form, b_table)

# pylint: disable=invalid-name
def _character_table_row(name, hp, _id, created_at, **_):
    """
    Render a row of the character table.

    The `**unused` lets you call `character_table_row(**character)`.
    Accessing the variables as function arguments instead of via
    `character['id_']` reduces visual noise
    """
    alive_badge = badge("R.I.P.") if hp < -9 else ''
    return {
        "Name": [a_button(name, url=f"/{_id}/{name}/"), alive_badge],
        "Date created": [created_at.date()],
    }

def _character_table(characters):
    table = b_table(
        header=["Name", "Date created"],
        body=[_character_table_row(**character) for character in characters],
    )
    table.children[0].attributes['id_'] = "character-table"
    return table

def index(characters):
    """Index page."""
    # Create a form and a button that collapses it
    add_character_button = b_button("Add", style=Style.INFO)
    add_character_form = div(id_="add-character-form")(
        async_form(
            form_name="add-character",
            action="/api/new-character/",
            submit_button="Create",
            inputs=[{
                'label': ['Name:'],
                'type': "input",
                'id': "character-name",
                'name': "name",
                'placeholder': "Character name"}],
            inline=True))
    collapse(add_character_form, add_character_button)

    content = [
        h1("Characters", add_character_button),
        add_character_form,
        br(),
        _character_table(characters),
    ]
    return base(characters, "Home", content=content)
