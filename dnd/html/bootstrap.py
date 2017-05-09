"""Bootstrap elements."""
from typing import Optional, Union
from enum import Enum
from pyhtml import (
    table, tr, thead, th, tbody, td,
    ul, li,
    span, div, nav,
    a, button,
    form, input_, label,
)

from dnd.html.tools import add_class, sanitise_id

class Style(Enum):

    """Bootstrap element styles."""

    BASIC = None
    DEFAULT = "default"
    PRIMARY = "primary"
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    LINK = "link"

def alert(*content, style: Style=Style.SUCCESS) -> div:
    """Bootstrap alert."""
    return div(class_=f"alert alert-{style.value} alert-dismissable fade in")(
        a(href="#", class_="close", data_dismiss="alert", aria_label="close")(
            "&times;"),
        *content)

def a_button(
        *content,
        url: str,
        style: Style=Style.DEFAULT) -> a:
    """Bootstrap button style a."""
    tag = a(class_=f"btn", href=url, role="button")(*content)
    if style.value is not None:
        add_class(tag, f"btn-{style.value}")
    return tag

def b_button(
        *content,
        style: Style=Style.DEFAULT,
        action: Optional[str]=None) -> button:
    """Bootstrap button."""
    tag = span(class_=f"btn")(*content)
    if style.value is not None:
        add_class(tag, f"btn-{style.value}")
    if action is not None:
        tag.attributes['action'] = action
    return tag

def b_label(*content, style: Style=Style.DEFAULT) -> span:
    """Bootstrap label."""
    return span(class_=f"label label-{style.value}")(*content)

def badge(*content) -> span:
    """Bootstrap badge."""
    return span(class_="badge")(*content)

def fluid_container(*content) -> div:
    """A div tag with class container-fluid."""
    return div(class_="container-fluid")(*content)

def _navigation_item(item) -> li:
    title, content = item
    if isinstance(content, str):
        return li(a(href=content)(title))
    return li(class_="dropdown")(
        a(class_="dropdown-toggle", data_toggle="dropdown", href="#")(
            title,
            span(class_="caret")),
        ul(class_="dropdown-menu")(
            *[_navigation_item(sub_item) for sub_item in content]))

def navigation(
        title: str,
        title_link: str,
        menu: Optional[list]=None,
        menu_right: Optional[list]=None) -> nav:
    """
    A top-fixed collapsible navigation bar.

    The menu arguments expect the following format:
        [
            ["Title", "url"],
            ["Drop-down Title", [
                ["Title1", "url"],
                ["Title2", "url"]]
            ]
        ]
    """
    if menu is None:
        menu = []
    if menu_right is None:
        menu_right = []
    navigation_header = div(class_="navbar-header")(
        button(
            type_="button",
            class_="navbar-toggle",
            data_toggle="collapse",
            data_target="#navigation-body")(
                *[span(class_="icon-bar") for _ in range(3)]),
        a(class_="navbar-brand", href=title_link)(title))
    navigation_links = []
    for item in menu:
        navigation_links.append(_navigation_item(item))
    navigation_links_right = []
    for item in menu_right:
        navigation_links_right.append(_navigation_item(item))
    navigation_body = div(
        class_="collapse navbar-collapse", id_="navigation-body")(
            ul(class_="nav navbar-nav")(*navigation_links),
            ul(class_="nav navbar-nav navbar-right")(*navigation_links_right))
    return nav(class_="navbar navbar-inverse navbar-fixed-top")(
        fluid_container(
            navigation_header,
            navigation_body))

def collapse(collapsible, trigger=None):
    """Have one element collapse the other."""
    add_class(collapsible, "collapse")
    if trigger is not None:
        trigger.attributes.update({
            "data-toggle": "collapse",
            "data-target": "#{}".format(collapsible.attributes['id_'])})

def async_form(
        form_name: str,
        action: str,
        submit_text: str="Submit",
        inputs: Optional[list]=None,
        method: str="POST",
        inline: bool=False,
        horizontal: Optional[list]=None) -> form:
    """
    Simple asynchronous form.

    form_name: unique name used to generate ids inside the form
    action: URL to send the data to
    submit_text: text to put on the submit button
    inputs = [
        {
            'label': [contents],
            'type': 'number',
            'id': 'some_number',
            'name': 'some_number'
            ... other input attributes
        },
        ...
    ]
    type, id and name are required.
    method: submit method
    inline: is form inline?
    horizontal: is form horizontal? if None: no, otherwise supply list of
    small column widths for label and input ex: [2, 10]

    no support yet for check buttons, radio buttons, option menus and
    textareas
    """
    id_base = sanitise_id(form_name)
    contents = [div(id_=f"{id_base}-errors")]
    for item in inputs:
        if item['type'] == "hidden":
            contents.append(input_(**item))
            continue
        input_group = []
        if 'label' in item:
            input_group.append(
                label(for_=item['id'])(*item.pop('label')))
            if horizontal is not None:
                add_class(
                    input_group[0],
                    "control-label col-sm-{}".format(horizontal[0]))
        input_group.append(input_(**item))
        add_class(input_group[-1], "form-control")
        if horizontal is not None:
            add_class(input_group[0], "col-sm-{}".format(horizontal[1]))
        contents.append(div(class_="form-group")(*input_group))
    contents.append(b_button(submit_text, action="submit"))
    if horizontal is not None:
        contents[-1] = div(class_="form-group")(
            div(class_="col-sm-offset-{} col-sm-{}".format(*horizontal))(
                contents[-1]))
    tag = form(
        data_async="true",
        data_target=f"#{id_base}-errors",
        action=action,
        method=method)(*contents)
    if inline:
        add_class(tag, "form-inline")
    if horizontal is not None:
        add_class(tag, "form-horizontal")
    return tag

def _table_row(header, row) -> tr:
    cells = []
    for column in header:
        if column in row:
            cells.append(td(*row[column]))
            continue
        if not cells:
            cells.append(td())
            continue
        if 'colspan' in cells[-1].attributes:
            cells[-1].attributes['colspan'] += 1
        else:
            cells[-1].attributes['colspan'] = 2
    tag = tr(*cells)
    if '_style' in row:
        add_class(tag, row['_style'].value)
    if '_collapse' in row:
        collapse(tag)
    if '_id' in row:
        tag.attributes['id_'] = row['_id']
    return tag

def b_table(
        header: list,
        header_visibility: bool=True,
        body: Optional[list]=None,
        condensed: bool=False,
        bordered: bool=False,
        striped: bool=False,
        hover: bool=False,
        responsive: bool=True) -> Union[div, table]:
    """
    Bootstrap table.

    header: list of strings that make up the table header and body
        row indexes
    header_visibility: whether to only use header for body ordering,
        or to also display it
    body:
        body of the table
    condensed: cut margins in half
    bordered: display borders
    striped: alternate white background and grey background for rows
    hover: highlight row when mouse hovers over it
    responsive: add horizontal scrolling for small screens

    Example
    =======
    b_table(
        header=['name', 'value'],
        body=[
            {
                'name': ["mister", i(snuggles)],
                'value': [5],
                '_style': Style.INFO
            },
            {
                'name': ["Marigold"],
                'value': [42],
                '_collapse': True,
                '_id': "secret-name",
            },
        ]
    )
    """
    content = []
    if header_visibility:
        content.append(thead(tr(*[th(text) for text in header])))
    if body is not None:
        content.append(tbody(*[_table_row(header, row) for row in body]))
    tag = table(class_="table")(*content)

    if condensed:
        add_class(tag, "table-condensed")
    if bordered:
        add_class(tag, "table-bordered")
    if striped:
        add_class(tag, "table-striped")
    if hover:
        add_class(tag, "table-hover")
    if responsive:
        tag = div(class_="table-responsive")(tag)
    return tag
