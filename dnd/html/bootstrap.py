"""Bootstrap elements."""
from typing import Optional
from enum import Enum
from pyhtml import (
    table, tr, thead, td,
    ul, li,
    span, div, nav,
    a, button,
)

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

def label(*content, style=Style.DEFAULT):
    """Bootstrap label."""
    tag = span(class_="label label-{}".format(style.value))
    if content:
        tag(*content)
    return tag

def badge(*content):
    """Bootstrap badge."""
    tag = span(class_="badge")
    if content:
        tag(*content)
    return tag

def fluid_container(*content):
    """A div tag with class container-fluid."""
    return div(class_="container-fluid")(*content)

def _navigation_item(item):
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
        menu_right: Optional[list]=None):
    """
    A top-fixed collapsible navigation bar.

    The menu arguments expect the following format:
        [
            ["Title", "url"],
            ["Drop-down Title",
                ["Title1", "url"],
                ["Title2", "url"]
            ]
        ]
    """
    if menu is None:
        menu = []
    if menu_right is None:
        menu_right = []
    navigation_header = div(class_="navbar-header")(button(
        type_="button",
        class_="navbar-toggle",
        data_toggle="collapse",
        data_target="#navigation-body")(
            *[span(class_="icon-bar") for _ in range(3)],
            a(class_="navbar-brand", href=title_link)(title)))
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
