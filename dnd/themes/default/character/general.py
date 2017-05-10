"""Character general panel."""
import copy
from pyhtml import div, h4, form
from dnd.html.bootstrap import (
    Style, collapse,
    a_button, b_button, b_label, badge, tooltip,
    panel, b_table, async_form)

def _general_table(character):
    pass

def _ability_edit_form(character, ability) -> form:
    common = {'type': 'number', 'min': -25, 'max': 25}
    base = copy.copy(common)
    base.update({
        'label': [tooltip(
            "Base:",
            title="base score that your roll at character creation")],
        'min': 0,
        'name': f"base-{ability}",
        'id': f"base-{ability}",
        'value': character[f'{ability}_base']})
    level = copy.copy(common)
    level.update({
        'label': [tooltip(
            "Attribute points:",
            title="you get to alter one attribute by one point every four levels")],
        'name': f"level-{ability}",
        'id': f"level-{ability}",
        'value': character[f'{ability}_level']})
    temporary = copy.copy(common)
    temporary.update({
        'label': [tooltip(
            "Temporary:",
            title="temporary changes from spell effects")],
        'name': f"temp-{ability}",
        'id': f"temp-{ability}",
        'value': character[f'{ability}_temp']})
    return async_form(
        form_name=f"{ability}-form",
        action=f"/api/{character['_id']}/ability/{ability}/",
        inputs=[base, level, temporary],
        horizontal=[5, 5])

def _ability_row(character, editing_privileges, ability):
    display = {
        '_id': f"{ability}-row",
        'ability': [ability.capitalize()],
        'value': [character[ability]],
        'modifier': [badge(
            character[f'{ability}_modifier'], id_=f"{ability}-modifier")]}
    if character[f'{ability}_temp'] < 0:
        display['_style'] = Style.DANGER
    elif character[f'{ability}_temp'] > 0:
        display['_style'] = Style.SUCCESS
    if not editing_privileges:
        return (display,)
    display['value'][0] = b_button(
        display['value'][0], id_=f"{ability}-value")
    collapse(
        f'{ability}-form',
        display['value'][0],
        accordion_id="edit-accordion")
    edit_form = {
        'ability': [_ability_edit_form(character, ability)],
        '_id': f'{ability}-form',
        '_collapse': True}
    return (display, edit_form)

def _abilities_table(character, editing_privileges, abilities):
    return b_table(
        ['ability', 'value', 'modifier'],
        header_visibility=False,
        body=[row for ability in abilities for row in _ability_row(
            character,
            editing_privileges,
            ability)])

def general(character: dict, editing_privileges: bool, abilities: list) -> div:
    """
    General panel for character page

    General information about character not directly related
    to any other panel.

    Parameters
    ----------
    character
        character data
    abilities
        list of all the different abilities
    """
    trigger = a_button("General", url="#", style=Style.LINK, block=True)
    return panel(
        [h4(class_="panel-title")(trigger)],
        [
            _general_table(character),
            h4("Abilities"),
            _abilities_table(character, editing_privileges, abilities)],
        [
            "Unspent ability points:",
            b_label(
                character['unspent_ability_points'],
                style=Style.DANGER if character['unspent_ability_points'] < 0 else Style.DEFAULT,
                id_="ability-points")
        ],
        trigger=trigger)
