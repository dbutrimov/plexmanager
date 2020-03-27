import os
from datetime import datetime

from django import template

register = template.Library()


@register.filter
def filename(path):
    return os.path.basename(path)


@register.filter
def dirname(path):
    return os.path.dirname(path)


@register.filter
def validate_movie(movie):
    return movie['path'] == movie['valid_path']


@register.filter
def unix_date(value, format):
    dt = datetime.utcfromtimestamp(value)
    if not format or len(format) <= 0:
        format = '%c'

    return dt.strftime(format)
