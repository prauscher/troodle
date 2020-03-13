#!/usr/bin/env python3

from . import models


def participants(request):
    if 'participant' in request.session:
        participant = models.Participant.objects.get(id=request.session['participant'])
        return {'participant': participant}

    return {}
