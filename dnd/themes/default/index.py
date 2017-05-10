"""Index page."""
from pyhtml import div, h1, br
from dnd.themes.default.base import base
from dnd.html.bootstrap import (
    Style, a_button, b_button, badge, collapse, async_form, b_table)

def index(characters):
    """Index page."""
    content = []
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
    content.append(h1("Characters", add_character_button))
    content.append(add_character_form)
    content.append(br())

    table_body = []
    for character in characters:
        row = {
            "Name": [a_button(
                character['name'],
                url=f"/{character['_id']}/{character['name']}/")],
            "Date created": [character['created_at'].date()]}
        if character['hp'] < -9:
            row['Name'].append(badge("R.I.P."))
        table_body.append(row)
    character_table = b_table(
        header=["Name", "Date created"],
        body=table_body)
    character_table.children[0].attributes['id_'] = "character-table"
    content.append(character_table)

    return base(characters, "Home", content=content)
