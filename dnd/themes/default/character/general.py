"""Character general panel."""
from pyhtml import div, h4, form
from dnd.html.tools import sanitise_id, add_class
from dnd.html.bootstrap import (
    Style, collapse,
    a_button, b_button, b_label, badge, tooltip,
    panel, b_table, b_tr, async_form, b_input, b_list)

def _race_input(character: dict, race: dict) -> dict:
    info_button = b_button('?', style=Style.INFO)
    add_class(info_button, "btn-xs")
    info_well = div(
        class_="well",
        id_=f"race-info-{sanitise_id(race['name'])}")(
            race['description'], _safe=True)
    collapse(info_well, info_button)
    return (
        b_input(
            type_="radio",
            name="race",
            label_=race['name'],
            after_label=info_button,
            value=race['name'],
            checked=True if race['name'] == character['race']['name'] else False),
        info_well)

def _race(character, editing_privileges, order, races):
    value = character['race']['name']
    if editing_privileges:
        value = a_button(value, url="#", id_="race-value")
    info_button = b_button('?', style=Style.INFO)

    display = b_tr(
        order,
        name='Race:',
        value=div(class_="btn-group")(value, info_button))

    info_row = b_tr(
        order,
        name=div(class_="well", id_="inner-race-info")(
            character['race']['description'], _safe=True),
        id_="race-info")
    collapse(info_row, info_button)

    if not editing_privileges:
        return (display, info_row)

    edit_race = b_tr(
        order,
        name=async_form(
            "race-form",
            f"/api/{character['_id']}/race/",
            *[item for race in races for item in _race_input(
                character, races[race])]),
        id_="race-form")
    collapse(edit_race, value, accordion_id="edit-accordion")

    return (display, info_row, edit_race)

def _experience(character, editing_privileges, order):
    value = character['xp']
    if editing_privileges:
        value = a_button(value, url="#", id_="xp-value")
    display = b_tr(
        order,
        name='Experience:',
        value=value)
    if not editing_privileges:
        return (display,)

    edit_experience = b_tr(
        order,
        name=async_form(
            "xp-form",
            f"/api/{character['_id']}/xp/",
            b_input(
                type_="number",
                name="xp",
                id_="xp",
                label_="Experience:",
                value=character['xp'],
                min_="0"),
            horizontal=[5,5]),
        id_="xp-form")
    collapse(edit_experience, value, accordion_id="edit-accordion")

    return (display, edit_experience)

def class_form(character, classes):
    """Form for selecting class per level."""
    return async_form(
        "class-form",
        f"/api/{character['_id']}/class/",
        *[b_input(
            type_="select",
            name=str(level),
            id_=f"level-{level}",
            options={class_: [class_.capitalize()] for class_ in classes},
            selected=character['classes'][level - 1]) for level in range(
                1, character['level'] + 1)],
        horizontal=[1, 6])

def _class(character, editing_privileges, order, classes):
    # couple buttons and rows for class information collapsibles
    info_rows = []
    info_buttons = {}
    for class_ in classes:
        info_rows.append(b_tr(
            order,
            id_=f"{class_}-info-table",
            name=div(class_="well")(
                classes[class_]['description'], _safe=True)))
        info_buttons[class_] = b_button("?", style=Style.INFO)
        add_class(info_buttons[class_], "btn-xs")
        collapse(
            info_rows[-1],
            info_buttons[class_],
            accordion_id="class-group")

    value = b_list(*[{'content': [
        class_.capitalize(),
        b_label(character[class_]),
        info_buttons[class_]]} for class_ in classes if character[class_] > 0])

    if editing_privileges:
        value = a_button(value, url="#", id_="class-value", block=True)

    edit_form = b_tr(
        order,
        id_="class-form",
        name=div(class_="class-form-content")(class_form(character, classes)))
    collapse(edit_form, value, accordion_id="edit-accordion")
    display = b_tr(
        order,
        name='Class:',
        value=div(class_="btn-group")(value))

    return (display, *info_rows, edit_form)

def _general_table(character, editing_privileges, *, races, classes):
    order = ['name', 'value']
    return b_table(
        *_race(character, editing_privileges, order, races),
        b_tr(
            order,
            name="Level:",
            value=div(id_="level-value")(character['level'])),
        *_experience(character, editing_privileges, order),
        *_class(character, editing_privileges, order, classes))

def _ability_edit_form(character, ability) -> form:
    return async_form(
        f"{ability}-form",
        f"/api/{character['_id']}/ability/{ability}/",
        b_input(
            type_='number',
            name=f"base-{ability}",
            id_=f"base-{ability}",
            label_=tooltip(
                "Base:",
                title="base score that your roll at character creation"),
            value=character[f'{ability}_base'],
            min_=0),
        b_input(
            type_='number',
            name=f"level-{ability}",
            id_=f"level-{ability}",
            label_=tooltip(
                "Attribute points:",
                title="you get to alter one attribute by one point every four levels"),
            value=character[f'{ability}_level'],
            min_=-25,
            max_=25),
        b_input(
            type_='number',
            name=f"temp-{ability}",
            id_=f"temp-{ability}",
            label_=tooltip(
                "Temporary:",
                title="temporary changes from spell effects"),
            value=character[f'{ability}_temp'],
            min_=-25,
            max_=25),
        horizontal=[5, 5])

def _ability_row(character, editing_privileges, ability):
    order = ['ability', 'value', 'modifier']
    style = Style.BASIC
    if character[f'{ability}_temp'] < 0:
        style = Style.DANGER
    elif character[f'{ability}_temp'] > 0:
        style = Style.SUCCESS

    value = character[ability]
    if editing_privileges:
        value = b_button(
            value, id_=f"{ability}-value")
    display = b_tr(
        order,
        id_=f"{ability}-row",
        style=style,
        ability=ability.capitalize(),
        value=value,
        modifier=badge(
            character[f'{ability}_modifier'], id_=f"{ability}-modifier"))
    if not editing_privileges:
        return (display,)
    edit_form = b_tr(
        order,
        ability=_ability_edit_form(character, ability),
        id_=f'{ability}-form')
    collapse(
        edit_form,
        value,
        accordion_id="edit-accordion")
    return (display, edit_form)

def _abilities_table(character, editing_privileges, abilities):
    return b_table(
        *[row for ability in abilities for row in _ability_row(
            character,
            editing_privileges,
            ability)])

def general(
        character: dict,
        editing_privileges: bool,
        *,
        abilities: list,
        classes: dict,
        races: dict) -> div:
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
            _general_table(
                character,
                editing_privileges,
                races=races,
                classes=classes),
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
