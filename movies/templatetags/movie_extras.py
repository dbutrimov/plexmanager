import os
from datetime import datetime

from django import template

from movies.library import parse_quality

register = template.Library()


@register.filter
def filename(path):
    return os.path.basename(path)


@register.filter
def dirname(path):
    return os.path.dirname(path)


@register.filter
def has_best_path(part):
    return part.path == part.best_path


@register.filter
def quality(part):
    return parse_quality(part.path)


@register.filter
def invalid_count(items):
    return len([item for item in items if not has_best_path(item)])


@register.filter
def unix_date(value, format):
    dt = datetime.utcfromtimestamp(value)
    if not format or len(format) <= 0:
        format = '%c'

    return dt.strftime(format)
