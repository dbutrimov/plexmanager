import os

from django import template

register = template.Library()


@register.filter
def filename(path):
    return os.path.basename(path)


@register.filter
def dirname(path):
    return os.path.dirname(path)


@register.filter
def validate(movie):
    return movie['path'] == movie['valid_path']
