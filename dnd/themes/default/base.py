"""Base template."""
from typing import Optional

from pyhtml import (
    html, head, title, meta, link, script, style, body,
    h1, div
)

from dnd.html.tools import add_class, sanitise_id
from dnd.html.bootstrap import fluid_container, navigation

def base(
        characters: list,
        page_title: str,
        body_title: Optional[list]=None,
        content: Optional[list]=None) -> html:
    """Base for every authenticated page."""
    # head
    custom_style = [
        ".btn{",
        "    white-space: normal !important;",
        "    word-wrap: break-word;",
        "    word-break: normal;",
        "}",
        ".text-left{",
        "    text-align: left !important;",
        "}"]
    header = head(
        title("DnD | {}".format(page_title)),
        meta(charset="utf-8"),
        meta(name="viewport", content_="width=device-width, initial-scale=1"),
        link(rel="stylesheet", href="/static/css/bootstrap.min.css"),
        script(src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"),
        script(src="/static/bootstrap.min.js"),
        script(src="/static/accordion.js"),
        script(src="/static/async-form.js"),
        style(*custom_style))

    # body
    if body_title is None:
        body_title = [page_title]
    if content is None:
        content = []
    left_menu = [
        [
            "Characters",
            [
                [character["name"], "/{}/{}/".format(
                    character['_id'], character.name)]
                for character in characters if character['hp'] > -10
            ]
        ]
    ]
    right_menu = [[
        "Account",
        [
            ["Change e-mail", "/auth/change-email/"],
            ["Change password", "/auth/change-password/"],
            ["Log out", "/auth/logout/"]]]]
    page_body = body(fluid_container(
        navigation(
            title="DnD",
            title_link="/",
            menu=left_menu,
            menu_right=right_menu),
        div(class_="page-header")(h1(*body_title)),
        *content))
    return html(header, page_body)
