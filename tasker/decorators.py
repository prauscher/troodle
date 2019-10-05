from django.core.exceptions import MultipleObjectsReturned
from django.shortcuts import redirect
from django.core import signing
from django.urls import reverse
from django.utils.http import urlencode
from django.http import Http404

from . import models


def class_decorator(decorators):
    if not isinstance(decorators, list):
        decorators = [decorators]

    def decorator(Cls):
        class Wrapper(Cls):
            def as_view(*args, **kwargs):
                view = Cls.as_view(*args, **kwargs)
                for decorator in reversed(decorators):
                    view = decorator(view)
                return view

        return Wrapper

    return decorator


def require_name(func):
    def wrapper(request, *args, **kwargs):
        if 'nick' not in request.session:
            return redirect(reverse('enter_nick') + "?" + urlencode({'next': request.get_full_path()}))

        return func(request, nick=request.session['nick'], *args, **kwargs)

    return wrapper


def board_view(func):
    def wrapper(*args, board_slug=None, **kwargs):
        try:
            board = models.Board.objects.get(slug=board_slug)
        except models.Board.DoesNotExist:
            raise Http404
        else:
            return func(board=board, *args, **kwargs)

    return wrapper


def board_admin_view(func):
    def wrapper(*args, board_hash=None, **kwargs):
        try:
            board = models.Board.get_by_hash(board_hash)
        except (signing.BadSignature, models.Board.DoesNotExist):
            raise Http404
        else:
            return func(board=board, *args, **kwargs)

    return wrapper


# must be used with board(_admin)_view only: @task_view \n @board(_admin)_view
def task_view(func):
    def wrapper(*args, board=None, task_id=None, **kwargs):
        try:
            task = board.tasks.get(pk=task_id)
        except (models.Task.DoesNotExist, ValueError):
            raise Http404
        else:
            return func(task=task, *args, **kwargs)

    return wrapper


# must be used with task_view and require_name
def require_action(action, redirect_target=None):
    def decorator(func):
        def wrapper(*args, task, nick, **kwargs):
            if not task.action_allowed(action, nick):
                if redirect_target:
                    return redirect(reverse(redirect_target, kwargs={'board_slug': task.board.slug, 'task_id': task.id}) + "?" + urlencode({'next': request.get_full_path()}))

                raise Http404

            return func(task=task, nick=nick, *args, **kwargs)

        return wrapper

    return decorator
