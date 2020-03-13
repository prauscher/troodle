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


def get_session_key(board):
    return 'participant{}'.format(board.id)


def get_participant(request, board):
    if get_session_key(board) not in request.session:
        raise NotLoggedInException

    participant = models.Participant.objects.get(id=request.session['participant{}'.format(board.id)])
    assert participant.board == board, "Stored Participant has invalid board"

    return participant


def apply_context(request, board, context):
    try:
        context['participant'] = get_participant(request, board)
    except NotLoggedInException:
        pass


def login(request, board, nick):
    participant, created = models.Participant.objects.get_or_create(nick=nick, board=board)
    request.session[get_session_key(board)] = participant.id


def logout(request, board):
    del request.session[get_session_key(board)]
