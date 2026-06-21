import re

from django.template import Library

register = Library()


@register.filter
def brief_source(source):
    return re.split(r"[:|p–]", source)[0].strip()


@register.filter
def distance_miles(value):
    if value is None:
        return ""
    return f"{value.mi:.1f} mi"
