from django import template

register = template.Library()


TIME_FORMATS = [
    (1 * 60 * 60 * 24, '{}d', '{}d'),
    (1 * 60 * 60, '{}h', '{}h'),
    (1 * 60, '{}m', '{}m'),
    (1, '{}s', '{}s'),
]


@register.filter("timedelta", is_safe=False)
def timedelta_filter(value):
    remaining_seconds = value.total_seconds()
    parts = []
    for seconds, singular, plural in TIME_FORMATS:
        if remaining_seconds >= seconds:
            count = int(remaining_seconds / seconds)
            if count == 1:
                parts.append(singular.format(count))
            else:
                parts.append(plural.format(count))
            remaining_seconds = remaining_seconds - (count * seconds)

    return " ".join(parts)
