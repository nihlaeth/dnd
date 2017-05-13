"""Character skills panel."""
from pyhtml import div, h4
from dnd.html.bootstrap import Style, a_button, b_label, panel
from dnd.html.tools import add_class

def skills_panel(character: dict, editing_privileges: bool, skills: dict) -> div:
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
    style = Style.DEFAULT
    if character['unspent_skill_slots'] < 0:
        style = Style.DANGER
    return panel(
        [h4(class_="panel-title")(trigger)],
        [],
        [
            "Unspent skill slots:",
            b_label(
                character['unspent_skill_slots'],
                style=style,
                id_="skill-slots")],
        trigger=trigger)
