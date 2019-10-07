from datetime import timedelta

from django.shortcuts import redirect
from django.http import Http404
from django.utils.timezone import now

from .. import decorators
from .. import models
from .. import utils


@decorators.require_name
@decorators.board_view
@decorators.task_view
@decorators.require_action('start', redirect_target='lock_task')
def start_task(request, task, nick):
    task.lock(nick, timedelta(minutes=30))
    models.Handling(task=task, editor=nick).save()
    return redirect(utils.get_redirect_url(request, default=task.get_frontend_url()))


@decorators.require_name
@decorators.board_view
@decorators.task_view
@decorators.require_action('stop')
def stop_task(request, task, nick, success):
    handling = task.get_current_handling(nick)
    handling.end = now()
    handling.success = success
    handling.save()

    if task.is_locked_for(nick):
        task.unlock()

    return redirect(utils.get_redirect_url(request, default=task.board.get_frontend_url()))


def abort_task(*args, **kwargs):
    return stop_task(success=False, *args, **kwargs)


def complete_task(*args, **kwargs):
    return stop_task(success=True, *args, **kwargs)


@decorators.require_name
@decorators.board_view
@decorators.task_view
@decorators.require_action('comment')
def comment_task(request, task, nick):
    handling = task.get_current_handling(nick)

    if request.POST["text"]:
        models.Comment(handling=handling, text=request.POST["text"]).save()

    if "attachment" in request.FILES:
        models.Attachment(handling=handling, file=request.FILES["attachment"]).save()

    return redirect(utils.get_redirect_url(request, default=task.get_frontend_url()))
