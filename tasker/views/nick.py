from django.urls import reverse
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View
from django.views.generic.edit import FormView

from . import ActionView
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


@decorators.class_decorator([decorators.board_view, decorators.require_name])
class ResetNickView(auth.AuthBoardMixin, ActionView):
    default_pattern_name = 'start'

    def action(self, *args, **kwargs):
        auth.logout(self.request, self.kwargs['board'])


@method_decorator(csrf_exempt, name='dispatch')
class StoreWebPushView(View):
    def post(self, request, *args, **kwargs):
        subscription_info = request.POST['subscription']

        # Store subscription_info if nick gets entered later
        request.session['subscription_info'] = subscription_info

        # apply subscription_info to all known participants
        for participant in auth.get_all_participants(request):
            if participant.subscription_info != subscription_info:
                participant.subscription_info = subscription_info
                participant.save()
        return JsonResponse({"success": True})
