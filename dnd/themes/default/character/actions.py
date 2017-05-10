"""Character actions panel."""
from pyhtml import div, h4
from dnd.html.bootstrap import Style, a_button, b_button, async_button, panel
from dnd.html.tools import add_class

def actions(character: dict) -> div:
    """
    Actions panel for character page

    Buttons that automate series of small changes that occur frequently.

    Parameters
    ----------
    character
        character data
    """
    trigger = a_button("Actions", url="#", style=Style.LINK, block=True)
    rest_button = b_button("Rest", style=Style.SUCCESS, action="submit")
    add_class(rest_button, "btn-xs")
    return panel(
        [h4(class_="panel-title")(trigger)],
        [
            div(id_="action-errors"),
            async_button(
                form_name="rest",
                action=f"/api/{character['_id']}/rest/",
                error_id="action-errors",
                submit_button=rest_button)],
        [],
        trigger=trigger)
