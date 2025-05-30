from django import template

register = template.Library()

@register.filter
def split_by_comma(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [item.strip() for item in str(value).split(',') if item.strip()] 