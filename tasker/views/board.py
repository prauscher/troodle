import string
import random

from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.db.models import Q

from .tasks import TaskListBase
from .. import auth
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
class BoardSendAdminLinkView(auth.AuthBoardMixin, TemplateView):
    template_name = 'tasker/board_adminlinksent.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['board'] = self.kwargs['board']

        old_admin_id = context['board'].admin_id

        # token does not has to be secure, just unique. hash will be applied afterwards
        new_auth_token = ''.join(random.choice(string.ascii_lowercase) for i in range(5))

        # only save changes if mail has been sent, otherwise we will exclude the admin
        try:
            self.kwargs['board'].admin_id = "{}:{}".format(self.kwargs['board'].id, new_auth_token)
            self.kwargs['board'].send_admin_mail(self.request)
            self.kwargs['board'].save()
        except ValueError as e:
            # restore admin_id to make links in navbar work
            self.kwargs['board'].admin_id = old_admin_id
            context['error'] = e.args[0]

        return context


@decorators.class_decorator(decorators.board_admin_view)
class BoardAdminView(TaskListBase):
    template_name = 'tasker/board_admin.html'


@decorators.class_decorator(decorators.board_view)
class BoardSummaryView(auth.AuthBoardMixin, TemplateView):
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


class BoardBaseView(auth.AuthBoardMixin, DetailView):
    model = models.Board
    lock_random_task = True

    def get_object(self):
        return self.kwargs['board']

    def get_open_tasks(self):
        return self.get_object().tasks \
            .filter(done=False) \
            .exclude(requires__done=False)

    def get_filters(self):
        raise NotImplementedError

    def find_random_task(self):
        filters = self.get_filters()

        for search_filter in filters:
            if search_filter:
                nr = random.randint(0, search_filter.count() - 1)
                return search_filter[nr]

        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['random_task'] = self.find_random_task()
        return context


@decorators.class_decorator([decorators.board_view, decorators.require_name])
class BoardView(BoardBaseView):
    def get_filters(self):
        open_tasks = self.get_open_tasks()

        q_reserved = Q(reserved_until__gte=now())
        q_reserved_by_me = Q(reserved_until__gte=now(), reserved_by=self.kwargs['participant'])
        q_current_handling = Q(handlings__isnull=False, handlings__end__isnull=True)
        q_my_current_handling = Q(handlings__isnull=False, handlings__end__isnull=True, handlings__editor=self.kwargs['participant'])

        return [
            # my open tasks
            open_tasks.filter(q_my_current_handling | q_reserved_by_me),
            # tasks without reservation, excluding those with current handling
            open_tasks.filter(~q_reserved & ~q_current_handling),
            # tasks without reservation but current handling by others
            open_tasks.filter(~q_reserved & q_current_handling & ~q_my_current_handling),
        ]

    def get_context_data(self, **kwargs):
        # TODO transaction
        context = super().get_context_data(**kwargs)
        if context['random_task']:
            perform_locking = True

            # do not lock if globally unset
            if not self.lock_random_task:
                perform_locking = False

            # do not lock if it is already locked
            if perform_locking and context['random_task'].is_locked_for(self.kwargs['participant']):
                perform_locking = False

            # do not lock if we already got a handling
            try:
                if perform_locking:
                    # should raise models.Handling.DoesNotExist
                    context['random_task'].get_current_handling(self.kwargs['participant'])
                    perform_locking = False
            except models.Handling.DoesNotExist:
                pass

            if perform_locking:
                assert context['random_task'].action_allowed('lock', self.kwargs['participant']), "Tried to lock task but locking is not allowed for this nick"
                context['random_task'].lock(self.kwargs['participant'])

        return context


@decorators.class_decorator([decorators.board_view])
class BoardMonitorView(BoardBaseView):
    template_name = "tasker/board_monitor.html"

    def get_filters(self):
        open_tasks = self.get_open_tasks()

        q_reserved = Q(reserved_until__gte=now())
        q_current_handling = Q(handlings__isnull=False, handlings__end__isnull=True)

        return [
            # tasks without reservation, excluding those with current handling
            open_tasks.filter(~q_reserved & ~q_current_handling),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context['random_task']:
            path = reverse('create_handling', kwargs={"board_slug": context['random_task'].board.slug, "task_id": context['random_task'].id})
            context['random_task_url'] = self.request.build_absolute_uri(path)
        return context


@decorators.class_decorator(decorators.board_admin_view)
class EditBoardView(auth.AuthBoardMixin, UpdateView):
    model = models.Board
    fields = ['label']

    def get_object(self):
        return self.kwargs['board']

    def get_success_url(self):
        return utils.get_redirect_url(self.request, default=self.object.get_admin_url())


@decorators.class_decorator(decorators.board_admin_view)
class DeleteBoardView(auth.AuthBoardMixin, DeleteView):
    model = models.Board
    success_url = reverse_lazy('start')

    def get_object(self):
        return self.kwargs['board']
