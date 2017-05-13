"""Character page."""
from pyhtml import div, br, span
from dnd.themes.default.base import base
from dnd.themes.default.character.actions import actions_panel
from dnd.themes.default.character.general import general_panel
from dnd.themes.default.character.skills import skills_panel
from dnd.html.bootstrap import (
    Style, b_button, badge, collapse, async_form, b_input, grid)

def character_page(
        characters,
        editing_privileges,
        character,
        *,
        abilities,
        races,
        classes,
        skills):
    """Character page."""
    edit_name_button = b_button(
        "Edit", style=Style.INFO) if editing_privileges else ''
    edit_name_form = div(id_="edit-name-form")(
        async_form(
            "edit-name",
            f"/api/{character['_id']}/name/",
            b_input(
                type_="input",
                name="name",
                id_="character-name",
                label="Name:",
                value=character['name']),
            submit_button="Edit",
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
                {'width': 4, 'content': [div(class_="panel-group")(
                    actions_panel(character),
                    general_panel(
                        character,
                        editing_privileges,
                        abilities=abilities,
                        races=races,
                        classes=classes))]},
                {'width': 4, 'content': [
                    skills_panel(character, editing_privileges, skills),
                ]},
                {'width': 4, 'content': []}))])
