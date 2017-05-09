"""Bootstrap elements."""
from enum import Enum
from pyhtml import (
    table, tr, thead, td,
    ol, ul, li,
    span, div
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
