from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.edit import FormView

from .. import auth
from .. import forms
from .. import decorators
from .. import utils


@decorators.class_decorator(decorators.board_view)
class EnterNickView(auth.AuthBoardMixin, FormView):
    form_class = forms.EnterNickForm
    template_name = 'tasker/enter_nick.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['board'] = self.kwargs['board']
        return context

    def form_valid(self, form):
        auth.login(self.request, self.kwargs['board'], form.cleaned_data['nick'])
        return super().form_valid(form)

    def get_success_url(self):
        return utils.get_redirect_url(self.request, default=reverse('start'))


@decorators.board_view
@decorators.require_name
def reset_nick(request, board, participant):
    auth.logout(request, board)

    return redirect(utils.get_redirect_url(request, default=reverse('start')))
