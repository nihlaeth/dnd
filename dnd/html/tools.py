"""Tools for HTML generation."""
import re
from types import GeneratorType

def add_class(tag, class_):
    """Ensure class is present in tag."""
    if 'class_' not in tag.attributes:
        tag.attributes['class_'] = class_
    else:
        classes = tag.attributes['class_'].split()
        if class_ not in classes:
            classes.append(class_)
            tag.attributes['class_'] = " ".join(classes)
    return tag

def remove_class(tag, class_):
    """Ensure class is absent in tag."""
    if 'class_' in tag.attributes:
        classes = tag.attributes['class_'].split()
        if class_ in classes:
            del classes[classes.index(class_)]
            tag.attributes['class_'] = " ".join(classes)
    return tag

def sanitise_id(text):
    """Make any string with at least one valid character a valid HTML id."""
    return "-".join(re.findall("[a-zA-Z0-9\\-_]*", text))

def is_sequence(item):
    """Test if item is a sequence but not a string."""
    return not isinstance(item, str) and isinstance(item, (GeneratorType, list, tuple))
