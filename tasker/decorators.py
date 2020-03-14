from django.shortcuts import redirect
from django.core import signing
from django.urls import reverse
from django.utils.http import urlencode
from django.http import Http404

from . import models, auth


def class_decorator(decorators):
    if not isinstance(decorators, list):
        decorators = [decorators]

    def decorator(cls):
        orig_as_view = cls.as_view
        def _as_view(*args, **kwargs):
            view = orig_as_view(*args, **kwargs)
            for decorator in reversed(decorators):
                view = decorator(view)
            return view

        cls.as_view = _as_view
        return cls

    return decorator


def _add_latest_board(request, board):
    if 'last_boards' not in request.session:
        request.session['last_boards'] = []

    board_item = [board.slug, board.label]
    request.session['last_boards'] = [board_item] + [item for item in request.session['last_boards'][0:4] if item != board_item]


# Must be used with board_view, but before task_view
def require_name(func):
    def wrapper(request, board, *args, **kwargs):
        if 'nick' in request.GET:
            auth.login(request, board, request.GET['nick'])

        try:
            participant = auth.get_participant(request, board)
        except auth.NotLoggedInException:
            return redirect(reverse('enter_nick', kwargs={'board_slug': board.slug}) + "?" + urlencode({'next': request.get_full_path()}))

        return func(request, participant=participant, board=board, *args, **kwargs)

    return wrapper


def board_view(func):
    def wrapper(request, *args, board_slug=None, **kwargs):
        try:
            board = models.Board.objects.get(slug=board_slug)
        except models.Board.DoesNotExist:
            raise Http404
        else:
            _add_latest_board(request, board)
            return func(request, board=board, *args, **kwargs)

    return wrapper


def board_admin_view(func):
    def wrapper(request, *args, board_hash=None, **kwargs):
        try:
            board = models.Board.get_by_hash(board_hash)
        except (signing.BadSignature, models.Board.DoesNotExist):
            raise Http404
        else:
            _add_latest_board(request, board)
            if 'admin_boards' not in request.session:
                request.session['admin_boards'] = {}
            request.session['admin_boards'][board.slug] = board.generate_hash()
            return func(request, board=board, *args, **kwargs)

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
        def wrapper(request, *args, task, participant, **kwargs):
            if not task.action_allowed(action, participant):
                if redirect_target:
                    return redirect(reverse(redirect_target, kwargs={'board_slug': task.board.slug, 'task_id': task.id}) + "?" + urlencode({'next': request.get_full_path()}))

                raise Http404

            return func(request, task=task, participant=participant, *args, **kwargs)

        return wrapper

    return decorator
