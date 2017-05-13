"""Bootstrap elements."""
from types import GeneratorType
from typing import Optional, Union
from enum import Enum
import uuid
from pyhtml import (
    Tag,
    table, tr, thead, th, tbody, td,
    ul, ol, li,
    span, div, nav,
    a, button,
    form, input_, label, select, option,
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
        url: str="#",
        style: Style=Style.DEFAULT,
        block: bool=False,
        id_: str=None) -> a:
    """Bootstrap button style a."""
    tag = a(class_=f"btn", href=url, role="button")(*content)
    if style.value is not None:
        add_class(tag, f"btn-{style.value}")
    if block:
        add_class(tag, "btn-block")
    if id_ is not None:
        tag.attributes['id_'] = id_
    return tag

def b_button(
        *content,
        style: Style=Style.DEFAULT,
        type_: str="button",
        id_: str=None) -> button:
    """Bootstrap button."""
    tag = button(class_=f"btn", type_=type_)(*content)
    if style.value is not None:
        add_class(tag, f"btn-{style.value}")
    if id_ is not None:
        tag.attributes['id_'] = id_
    return tag

def b_label(
        *content,
        style: Style=Style.DEFAULT,
        id_: Optional[str]=None) -> span:
    """Bootstrap label."""
    tag = span(class_=f"label label-{style.value}")(*content)
    if id_ is not None:
        tag.attributes['id_'] = id_
    return tag

def badge(*content, id_: str=None) -> span:
    """Bootstrap badge."""
    tag = span(class_="badge")(*content)
    if id_ is not None:
        tag.attributes['id_'] = id_
    return tag

def tooltip(*content, title) -> a:
    """Bootstrap tooltip."""
    return a(data_toggle="tooltip", href="#", title=title)(*content)

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

def collapse(
        collapsible: Union[Tag, str],
        trigger: Optional[Tag]=None,
        accordion_id: Optional[str]=None) -> None:
    """Have one element collapse the other."""
    if isinstance(collapsible, Tag):
        add_class(collapsible, "collapse")
        if 'id_' not in collapsible.attributes:
            collapsible.attributes['id_'] = uuid.uuid4().hex
        collapsible = collapsible.attributes['id_']
    if trigger is not None:
        trigger.attributes.update({
            "data-toggle": "collapse",
            "data-target": f"#{collapsible}"})
        if accordion_id is not None:
            trigger.attributes['data-parent'] = f"#{accordion_id}"

def _checkable(label_, after_label, selected, horizontal, **attributes):
    if label_ is None:
        raise AttributeError(
            "label_ is a required attribute for radio and checkbox inputs")
    if selected is not None:
        attributes['selected'] = selected
    form_input = input_(**attributes)
    input_label = div(class_=attributes['type_'])(
        label(form_input, *label_), *after_label)
    if horizontal is not None:
        input_label = div(
            class_="col-sm-offset-{} col-sm-{}".format(*horizontal))(
                input_label)
    return div(class_="form-group")(input_label)

def _label(id_, label_, horizontal):
    if label_ is None:
        return ''
    if id_ is None:
        raise AttributeError(
            "id_ is a required attribute if label_ is specified")
    if isinstance(label_, (GeneratorType, list, tuple)):
        input_label = label(for_=id_)(*label_)
    else:
        input_label = label(for_=id_)(label_)
    if horizontal is not None and input_label != '':
        add_class(
            input_label,
            "control-label col-sm-{}".format(horizontal[0]))
    return input_label

def _select(selected, options, **attributes):
    content = []
    for key in options:
        if isinstance(options[key], (GeneratorType, list, tuple)):
            options[key] = [options[key]]
        if selected == key:
            content.append(option(
                value=key,
                selected="true")(*options[key]))
        else:
            content.append(option(value=key)(*options[key]))
    return select(**attributes)(*content)

def b_input(
        type_: str,
        name: str,
        id_: str=None,
        label_: Optional[Union[list, Tag, str, int, float]]=None,
        after_label: Union[list, Tag, str, int, float]=None,
        selected: Optional[str]=None,
        options: Optional[dict]=None,
        horizontal: Optional[list]=None,
        **attributes) -> Union[div, input_]:
    """
    Form input.

    This currently supports any input except textareas.

    Parameters
    ----------
    type
        type of input (ex: number, radio, select)
    name
        name of the input field (you need this if you want to do anything
        with the data)
    id_: optional
        id of the input field, required if label_ is specified, defaults to None
    label_: optional
        content of the label, defaults to None
    after_label: optional
        any content you want to place after the closing tag of the label,
        defaults to None
    selected: optional,
        used for select, radio and checkbox type inputs. select expects a string
        matching the key of the option, radio and checkboxes expect a Boolean,
        defaults to None
    options: optional,
        keyvalue pairs used for select content, defaults to None
    horizontal: optional
        is form horizontal? if None: no, otherwise supply list of
        small column widths for label and input ex: [2, 10], defaults to None

    Keyword Arguments
    -----------------
    **attributes:
        any HTML attribute you want assigned to the input

    Raises
    ------
    AttributeError:
        if label_ is missing for a radio or checkbox type input,
        or if id_ is missing when label_ is specified.
    """
    attributes['type_'] = type_
    attributes['name'] = name
    if id_ is not None:
        attributes['id_'] = id_

    if type_ == "hidden":
        return input_(**attributes)

    if after_label is None:
        after_label = []
    if not isinstance(after_label, (GeneratorType, list, tuple)):
        after_label = [after_label]

    if type_ in ['radio', 'checkbox']:
        return _checkable(
            label_, after_label, selected, **attributes)

    input_label = _label(id_, label_, horizontal)

    if type_ == "select":
        form_input = _select(selected, options, **attributes)
    else:
        form_input = input_(**attributes)
    add_class(form_input, "form-control")
    if horizontal is not None:
        form_input = div(class_=f"col-sm-{horizontal[1]}")(
            form_input)
        if input_label == '':
            add_class(form_input, f"col-sm-offset-{horizontal[0]}")

    return div(class_="form-group")(input_label, *after_label, form_input)

def async_form(
        form_name: str,
        action: str,
        *content,
        submit_button: Union[str, button]="Submit",
        method: str="POST",
        inline: bool=False,
        horizontal: Optional[list]=None,
        error_id: Optional[str]=None) -> form:
    """
    Asynchronous form.

    Parameters
    ----------
    form_name
        unique name used to generate ids inside the form
    action
        URL to send the data to
    *content
        everything you want inside your form (use `b_input` to generate)

    Keyword Arguments
    -----------------
    submit_button: optional
        either the text to use on the submit button, or in actual button,
        defaults to Submit
    method: optional
        submit method, defaults to POST
    inline: optional
        is form inline? defaults to False
    horizontal: optional
        is form horizontal? if None: no, otherwise supply list of
        small column widths for label and input (ex: `[2, 10]`), defaults to None
    error_id: optional
        id of the tag you want to use to store errors. if left empty, for will
        have an internal field for this purpose, defaults to None
    """
    id_base = sanitise_id(form_name)

    error_field = ''
    if error_id is None:
        error_id = f"{id_base}-errors"
        error_field = div(id_=error_id)

    if isinstance(submit_button, str):
        submit_button = b_button(submit_button, type_="submit")
    if horizontal is not None:
        submit_button = div(class_="form-group")(
            div(class_="col-sm-offset-{} col-sm-{}".format(*horizontal))(
                submit_button))
    tag = form(
        data_async="true",
        data_target=f"#{error_id}",
        action=action,
        method=method)(error_field, *content, submit_button)
    if inline:
        add_class(tag, "form-inline")
    if horizontal is not None:
        add_class(tag, "form-horizontal")
    return tag

def async_button(
        form_name: str,
        action: str,
        error_id: str,
        submit_button: Union[str, button]="Submit",
        hidden_data: Optional[dict]=None) -> form:
    """
    Button that works in the background.

    This is actually an asynchronous form with exclusively hidden input
    and only a single button as visible element.

    Parameters
    ----------
    form_name
        TODO
    action
        TODO
    error_id
        TODO
    submit_button: optional
        TODO, defaults to "Submit"
    hidden_data: optional
        dictionary with keyvalue pairs that are included in the form
        defaults to None

    Examples
    --------
    ..doctest::

        >>> TODO
    """
    if hidden_data is None:
        hidden_data = {}
    return async_form(
        form_name=form_name,
        action=action,
        *[b_input(
            type_='hidden',
            name=name,
            value=hidden_data[name]) for name in hidden_data],
        submit_button=submit_button,
        error_id=error_id,
        inline=True)

def b_tr(
        order: list,
        style:Style=Style.BASIC,
        id_: Optional[str]=None,
        **cells) -> tr:
    """
    Single table row.

    Feed this to `b_table`.

    Parameters
    ----------
    order
        list with column names in order they appear in the table
    style: optional
        contextual style for row, defaults to Style.BASIC
    id_: optional
        value for ID attribute, defaults to None
    collapsible: optional
        whether this role should be collapsible, defaults to False

    Keyword Arguments
    -----------------
    **cells: Union[Sequence, str, int, float]
        contents of the columns defined in `order`
    """
    contents = []
    for column in order:
        if column in cells:
            if isinstance(cells[column], (GeneratorType, list, tuple)):
                contents.append(td(*cells[column]))
            else:
                contents.append(td(cells[column]))
            continue
        if not contents:
            contents.append(td())
            continue
        if 'colspan' in contents[-1].attributes:
            contents[-1].attributes['colspan'] += 1
        else:
            contents[-1].attributes['colspan'] = 2
    tag = tr(*contents)
    if style.value is not None:
        add_class(tag, style.value)
    if id_ is not None:
        tag.attributes['id_'] = id_
    return tag

def b_table(
        *rows: tr,
        header: Optional[list]=None,
        condensed: bool=False,
        bordered: bool=False,
        striped: bool=False,
        hover: bool=False,
        responsive: bool=False) -> Union[div, table]:
    """
    Bootstrap table.

    Parameters
    ----------
    *rows
        table content, generate with `b_tr`

    Keyword Arguments
    -----------------
    header: optional
        list with header contents (can be list, str, int or float), defaults to None
    condensed: optional
        cut margins in half, defaults to False
    bordered: optional
        display borders, defaults to False
    striped: optional
        alternate white background and grey background for rows, defaults to False
    hover: optional
        highlight row when mouse hovers over it, defaults to False
    responsive: optional
        add horizontal scrolling for small screens, defaults to False
    """
    table_head = ''
    if header is not None:
        header_content = []
        for cell in header:
            if isinstance(cell, (GeneratorType, list, tuple)):
                header_content.append(th(*cell))
            else:
                header_content.append(th(cell))
        table_head = thead(tr(*header_content))
    tag = table(class_="table")(table_head, tbody(*rows))

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

def grid(*columns) -> div:
    """
    Bootstrap grid row.

    Example
    =======
    grid(
        {'width': 4, 'content': []},
        {'width': 5, 'content': [b("Hello")]},
        {'width': 3, 'content': [i("world")]})

    """
    cells = []
    for column in columns:
        cells.append(
            div(class_=f"col-sm-{column['width']}")(*column['content']))
    return div(class_="row")(*cells)

def panel(
        header: Optional[list]=None,
        body: Optional[Union[list, ul, ol]]=None,
        footer: Optional[list]=None,
        style: Style=Style.DEFAULT,
        trigger: Optional[Tag]=None,
        accordion_id: Optional[str]=None) -> div:
    """
    Bootstrap panel generation.

    Parameters
    ----------
    header: optional
        Contents of header block, defaults to None
    body: optional
        Contents of body block, defaults to None
    footer: optional
        Contents of footer block, defaults to None
    style: optional
        context class of panel, defaults to Style.DEFAULT
    trigger: optional
        make panel collapsible by this trigger. User is responsible
        for placing trigger, preferably in the header though. Defaults to None
    accordion_id: optional
        TODO, defaults to None

    Raises
    ------
    TODO

    Returns
    -------
    TODO

    Examples
    --------
    ..doctest::

        >>> TODO
    """
    panel_content = []
    if header is not None:
        panel_content.append(div(class_="panel-heading")(*header))
    panel_body = []
    if body is not None:
        if isinstance(body, (ul, ol)):
            panel_body.append(body)
        else:
            panel_body.append(div(class_="panel-body")(*body))
    if footer is not None:
        panel_body.append(div(class_="panel-footer")(*footer))
    if trigger is not None:
        panel_content.append(div(class_="panel-collapse")(*panel_body))
        collapse(panel_content[-1], trigger, accordion_id)
    else:
        panel_content.extend(panel_body)

    tag = div(class_="panel")(*panel_content)
    if style.value is not None:
        add_class(tag, f"panel-{style.value}")
    return tag

def b_list(*items, type_: str="ul"):
    """
    TODO

    TODO

    Parameters
    ----------
    *items: TODO
        TODO

    Keyword Arguments
    -----------------
    type_: optional
        currently unsupported, defaults to "ul"

    Raises
    ------
    TODO

    Returns
    -------
    TODO

    Examples
    --------
    ..doctest::

        >>> TODO
    """
    list_items = [li(class_="list-group-item")(*item['content']) for item in items]
    return ul(class_="list-group")(*list_items)
