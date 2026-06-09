import re

from django.template import Library

register = Library()


@register.filter
def brief_source(source):
    return re.split(r"[:|p–]", source)[0].strip()
