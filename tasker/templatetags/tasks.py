from django import template

register = template.Library()


@register.filter("allowed_actions")
def allowed_actions(value, arg):
    return value.get_allowed_actions(arg)


@register.filter("task_status")
def task_status(value, arg):
    return value.get_participant_status(arg)
