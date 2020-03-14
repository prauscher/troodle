#!/usr/bin/env python3

from . import models


class NotLoggedInException(Exception):
    pass


class AuthBoardMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'board' in self.kwargs:
            apply_context(self.request, self.kwargs['board'], context)
        elif 'task' in self.kwargs:
            apply_context(self.request, self.kwargs['task'].board, context)
        return context


def _prepare_session(request):
    if 'participant' not in request.session:
        request.session['participant'] = {}


def get_participant(request, board):
    _prepare_session(request)
    if str(board.id) not in request.session['participant']:
        raise NotLoggedInException

    participant = models.Participant.objects.get(id=request.session['participant'][str(board.id)])
    assert participant.board == board, "Stored Participant has invalid board"

    return participant


def apply_context(request, board, context):
    try:
        context['participant'] = get_participant(request, board)
    except NotLoggedInException:
        pass


def login(request, board, nick):
    participant, _ = models.Participant.objects.get_or_create(nick=nick, board=board)

    _prepare_session(request)
    request.session['participant'][str(board.id)] = participant.id
    request.session.modified = True


def logout(request, board):
    _prepare_session(request)
    del request.session['participant'][str(board.id)]
    request.session.modified = True
