from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()


TIME_FORMATS = [
    (1 * 60 * 60 * 24, _('{} day'), _('{} days')),
    (1 * 60 * 60, _('{} hour'), _('{} hours')),
    (1 * 60, _('{} minute'), _('{} minutes')),
    (1, _('{} second'), _('{} seconds')),
]


@register.filter("timedelta", is_safe=False)
def timedelta_filter(value):
    remaining_seconds = value.total_seconds()
    parts = []
    remaining_parts = 2
    for seconds, singular, plural in TIME_FORMATS:
        if remaining_seconds >= seconds and remaining_parts > 0:
            remaining_parts = remaining_parts - 1
            count = int(remaining_seconds / seconds)
            if count == 0:
                pass
            elif count == 1:
                parts.append(singular.format(count))
            else:
                parts.append(plural.format(count))
            remaining_seconds = remaining_seconds - (count * seconds)

    return " ".join(parts)
