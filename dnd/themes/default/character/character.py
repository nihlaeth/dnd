"""Character page."""
from pyhtml import div, br, span
from dnd.themes.default.base import base
from dnd.themes.default.character.actions import actions
from dnd.html.bootstrap import (
    Style, b_button, badge, collapse, async_form, grid)

def character_(characters, editing_privileges, character):
    """Character page."""
    edit_name_button = b_button(
        "Edit", style=Style.INFO) if editing_privileges else ''
    edit_name_form = div(id_="edit-name-form")(
        async_form(
            form_name="edit-name",
            action=f"/api/{character['_id']}/name/",
            submit_button="Edit",
            inputs=[{
                'label': ['Name:'],
                'type': "input",
                'id': "character-name",
                'name': "name",
                'value': character['name']}],
            inline=True)) if editing_privileges else ''
    collapse(edit_name_form, edit_name_button)
    return base(
        characters,
        character['name'],
        body_title=[
            span(id_="name-value")(character['name']),
            span(id_="alive")(badge("R.I.P.") if character['hp'] < -9 else ''),
            edit_name_button],
        content=[
            edit_name_form,
            br(),
            div(id_="edit-accordion")(grid(
                {'width': 4, 'content': [actions(character)]},
                {'width': 4, 'content': []},
                {'width': 4, 'content': []}))])
