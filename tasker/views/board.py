from datetime import datetime
import random

from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.db.models import Q

from .tasks import TaskListBase
from .. import utils
from .. import models
from .. import decorators


class CreateBoardView(CreateView):
    model = models.Board
    fields = ['label', 'admin_mail']

    def form_valid(self, form):
        # super().form_valid saves the object needed to create links
        return_value = super().form_valid(form)

        try:
            self.object.send_admin_mail(self.request)
        except ValueError:
            # expected iff user entered no admin mail
            pass

        return return_value

    def get_success_url(self):
        return utils.get_redirect_url(self.request, default=self.object.get_admin_url())


@decorators.class_decorator(decorators.board_view)
class BoardSendAdminLinkView(TemplateView):
    template_name = 'tasker/board_adminlinksent.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['board'] = self.kwargs['board']

        try:
            self.kwargs['board'].send_admin_mail(self.request)
        except ValueError as e:
            context['error'] = e.args[0]

        return context


@decorators.class_decorator(decorators.board_admin_view)
class BoardAdminView(TaskListBase):
    template_name = 'tasker/board_admin.html'


@decorators.class_decorator(decorators.board_view)
class BoardSummaryView(TemplateView):
    template_name = 'tasker/board_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['board'] = self.kwargs['board']

        context['tasks_done_simple'] = []
        context['tasks_done_complex'] = []
        context['tasks_not_done'] = []

        tasks = self.kwargs['board'].tasks.all()

        for task in tasks:
            if task.done:
                handlings = task.handlings.all()
                if len(handlings) == 0:
                    context['tasks_done_simple'].append((task, None))
                if len(handlings) == 1 and not handlings[0].tasker_comments.exists() and not handlings[0].tasker_attachments.exists():
                    context['tasks_done_simple'].append((task, handlings[0]))
                else:
                    context['tasks_done_complex'].append(task)
            else:
                context['tasks_not_done'].append((task, task.get_current_handling().all()))

        return context


@decorators.class_decorator([decorators.require_name, decorators.board_view])
class BoardView(DetailView):
    model = models.Board

    def get_object(self):
        return self.kwargs['board']

    def find_random_task(self):
        open_tasks = self.get_object().tasks \
            .filter(done=False) \
            .exclude(requires__done=False)

        q_reserved = Q(reserved_until__gte=now())
        q_reserved_by_me = Q(reserved_until__gte=now(), reserved_by=self.kwargs['nick'])
        q_current_handling = Q(handlings__isnull=False, handlings__end__isnull=True)
        q_my_current_handling = Q(handlings__isnull=False, handlings__end__isnull=True, handlings__editor=self.kwargs['nick'])

        filters = [
            # my open tasks
            open_tasks.filter(q_my_current_handling | q_reserved_by_me),
            # tasks without reservation, excluding those with current handling
            open_tasks.filter(~q_reserved & ~q_current_handling),
            # tasks without reservation but current handling by others
            open_tasks.filter(~q_reserved & q_current_handling & ~q_my_current_handling),
        ]

        for filter in filters:
            if filter:
                nr = random.randint(0, filter.count() - 1)
                return filter[nr]

        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # TODO transaction

        context['random_task'] = self.find_random_task()
        if context['random_task']:
            if not context['random_task'].is_locked_for(self.kwargs['nick']):
                assert context['random_task'].action_allowed('lock', self.kwargs['nick']), "Tried to lock task but locking is not allowed for this nick"
                context['random_task'].lock(self.kwargs['nick'])
            context['random_task'].fill_nick(self.kwargs['nick'])

        return context


@decorators.class_decorator(decorators.board_admin_view)
class EditBoardView(UpdateView):
    model = models.Board
    fields = ['label']

    def get_object(self):
        return self.kwargs['board']

    def get_success_url(self):
        return utils.get_redirect_url(self.request, default=self.object.get_admin_url())


@decorators.class_decorator(decorators.board_admin_view)
class DeleteBoardView(DeleteView):
    model = models.Board
    success_url = reverse_lazy('start')

    def get_object(self):
        return self.kwargs['board']
