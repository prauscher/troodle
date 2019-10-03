from django.shortcuts import redirect
from django.core import signing
from django.urls import reverse
from django.utils.http import urlencode

from . import models


def class_decorator(decorators):
    if not isinstance(decorators, list):
        decorators = [decorators]

    def decorator(Cls):
        class Wrapper(Cls):
            def as_view(*args, **kwargs):
                view = Cls.as_view(*args, **kwargs)
                for decorator in decorators:
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
            pass
        else:
            return func(board=board, *args, **kwargs)

    return wrapper


def board_admin_view(func):
    def wrapper(*args, board_hash=None, **kwargs):
        try:
            board = models.Board.get_by_hash(board_hash)
        except signing.BadSignature:
            pass
        except models.Board.DoesNotExist:
            pass
        else:
            return func(board=board, *args, **kwargs)

    return wrapper


# should be used with board(_admin)_view only: @task_view \n @board(_admin)_view
def task_view(func):
    def wrapper(*args, board=None, task_id=None, **kwargs):
        try:
            task = models.Task.objects.get(pk=task_id)
            print(board, task.board)
            if board != task.board:
                raise ValueError
        except models.Task.DoesNotExist:
            pass
        except ValueError:
            pass
        else:
            return func(task=task, *args, **kwargs)

    return wrapper
