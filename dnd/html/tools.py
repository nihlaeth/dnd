"""Tools for HTML generation."""
import re

def add_class(tag, class_):
    """Ensure class is present in tag."""
    if 'class' not in tag.attributes:
        tag.attributes['class'] = class_
    else:
        classes = tag.attributes['class'].split()
        if class_ not in classes:
            classes.append(class_)
            tag.attributes['class'] = " ".join(classes)
    return tag

def remove_class(tag, class_):
    """Ensure class is absent in tag."""
    if 'class' in tag.attributes:
        classes = tag.attributes['class'].split()
        if class_ in classes:
            del classes[classes.index(class_)]
            tag.attributes['class'] = " ".join(classes)
    return tag

def sanitise_id(text):
    """Make any string with at least one valid character a valid HTML id."""
    return "-".join(re.findall("[a-zA-Z0-9\\-_]*", text))
