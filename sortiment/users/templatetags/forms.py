from django import template

register = template.Library()


@register.inclusion_tag("form/field.html")
def field(field):
    return {"field": field}
