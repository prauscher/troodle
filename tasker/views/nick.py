from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.edit import FormView

from .. import models
from .. import forms
from .. import decorators
from .. import utils


@decorators.class_decorator(decorators.board_view)
class EnterNickView(FormView):
    form_class = forms.EnterNickForm
    template_name = 'tasker/enter_nick.html'

    def form_valid(self, form):
        participant, created = models.Participant.objects.get_or_create(nick=form.cleaned_data['nick'], board=self.kwargs['board'])
        self.request.session['participant'] = participant.id
        return super().form_valid(form)

    def get_success_url(self):
        return utils.get_redirect_url(self.request, default=reverse('start'))


def reset_nick(request):
    del request.session['participant']

    return redirect(utils.get_redirect_url(request, default=reverse('start')))
