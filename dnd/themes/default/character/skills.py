"""Character skills panel."""
from pyhtml import div, h4
from dnd.html.bootstrap import (
    Style, a_button, b_button, b_label, panel, tooltip,
    async_form, b_input, b_table, b_tr, collapse)
from dnd.html.tools import add_class, sanitise_id

def _learned_skill_panel(character, editing_privileges, skill: str):
    order = ['name', 'value']
    rows = []
    if character['skills'][skill]['skill_check'] is not None:
        rows.append(b_tr(
            order,
            name=tooltip(
                "Skill check:",
                title=character['skills'][skill]['skill_check_text']),
            value=character['skills'][skill]['skill_check_value']))
    trigger = a_button(
        skill.capitalize(), url="#", style=Style.LINK, block=True)
    return panel(
        [h4(class_="panel-title")(trigger)],
        [
            b_table(*rows),
            div(character['skills'][skill]['description'], _safe=True)],
        trigger=trigger,
        accordion_id="skill-accordion")

def learned_skills(character: dict, editing_privileges: bool):
    """Display all the skills the character has learned."""
    return [_learned_skill_panel(
        character,
        editing_privileges,
        skill) for skill in character['skills']]

def _skill_checkbox(character, skill):
    order = ['name', 'value']
    rows = []
    if skill['skill_check'] is not None:
        rows.append(b_tr(
            order,
            name="Skill check:",
            value=" + ".join([
                str(item) for item in skill['skill_check']])))

    info_button = b_button('?', style=Style.INFO)
    add_class(info_button, "btn-xs")
    info_well = div(
        class_="well",
        id_=f"skill-info-{sanitise_id(skill['name'].lower())}")(
            b_table(*rows), skill['description'], _safe=True)
    collapse(info_well, info_button, "skills-form-item-accordion")

    label = b_input(
        type_="checkbox",
        name=skill['name'].lower(),
        label_=skill['name'],
        after_label=info_button,
        checked=True if skill['name'].lower() in character['skills'] else False)
    return (label, info_well)

def _skill_group_panel(character: dict, skills: dict, skill_group: set):
    trigger = a_button(
        skill_group.capitalize(), url="#", style=Style.LINK, block=True)
    return panel(
        [h4(class_="panel-title")(trigger)],
        [
            item for skill in skills
            if skills[skill]['group'] == skill_group
            for item in _skill_checkbox(character, skills[skill])],
        trigger=trigger,
        accordion_id="skills-form-accordion")

def skills_panel(character: dict, editing_privileges: bool, skills: dict, skill_groups: set) -> div:
    """
    Skills panel for character page

    Parameters
    ----------
    character
        character data
    editing_privileges
        does current user have editing privileges for this character
    skills
        all the available skills
    """
    trigger = a_button("Skills", url="#", style=Style.LINK, block=True)
    edit_button = ''
    edit_form = ''
    if editing_privileges:
        edit_button = b_button("Edit", block=True)
        edit_form = div(class_="well", id_="skills-form")(async_form(
            "skills-form",
            f"/api/{character['_id']}/skill/",
            div(class_="panel-group", id_="skills-form-accordion")(
                *[_skill_group_panel(
                    character,
                    skills,
                    skill_group) for skill_group in skill_groups])))
        collapse(edit_form, edit_button, accordion_id="edit-accordion")
    style = Style.DEFAULT
    if character['unspent_skill_slots'] < 0:
        style = Style.DANGER
    return panel(
        [h4(class_="panel-title")(trigger)],
        [
            div(class_="panel-group", id_="skill-accordion")(
                *learned_skills(character, editing_privileges)),
            edit_button,
            edit_form],
        [
            "Unspent skill slots:",
            b_label(
                character['unspent_skill_slots'],
                style=style,
                id_="skill-slots")],
        trigger=trigger)
