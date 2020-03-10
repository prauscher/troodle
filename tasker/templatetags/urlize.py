from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.html import urlize as urlize_impl

register = template.Library()


# See https://stackoverflow.com/questions/2295725/extending-urlize-in-django
@register.filter(is_safe=True, needs_autoescape=True)
@stringfilter
def urlize_target_blank(value, limit, autoescape=None):
    return mark_safe(urlize_impl(value, trim_url_limit=int(limit), nofollow=True, autoescape=autoescape).replace('<a', '<a target="_blank"'))
