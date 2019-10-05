from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.edit import FormView

from .. import forms
from .. import decorators
from .. import utils


class EnterNickView(FormView):
    form_class = forms.EnterNickForm
    template_name = 'tasker/enter_nick.html'

    def form_valid(self, form):
        self.request.session['nick'] = form.cleaned_data['nick']
        return super().form_valid(form)

    def get_success_url(self):
        return utils.get_redirect_url(self.request, default=reverse('start'))


@decorators.require_name
def reset_nick(request, nick):
    del request.session['nick']

    return redirect(utils.get_redirect_url(request, default=reverse('start')))
