from datetime import datetime
import random

from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.db.models import Q

from .tasks import TaskListBase
from .. import models
from .. import decorators


class CreateBoardView(CreateView):
    model = models.Board
    fields = ['label']

    def get_success_url(self):
        return self.object.get_admin_url()


@decorators.class_decorator(decorators.board_admin_view)
class BoardAdminView(TaskListBase):
    template_name = 'tasker/board_admin.html'


@decorators.class_decorator(decorators.board_view)
class BoardSummaryView(TemplateView):
    template_name = 'tasker/board_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['tasks_done_simple'] = []
        context['tasks_done_complex'] = []
        context['tasks_not_done'] = []

        tasks = self.kwargs['board'].tasks.all()

        for task in tasks:
            if task.is_done():
                handlings = task.handlings.all()
                print(handlings, len(handlings) == 1, handlings[0].tasker_comments.exists())
                if len(handlings) == 1 and not handlings[0].tasker_comments.exists() and not handlings[0].tasker_attachments.exists():
                    assert handlings[0].success, "Task cannot be done if only handling is not done"
                    assert handlings[0].end is not None, "Task cannot be done if only handling is not complete"

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
        open_tasks = self.get_object().tasks.exclude(handlings__success=True)

        q_reserved = Q(reserved_until__gte=now())
        q_reserved_by_me = Q(reserved_until__gte=now(), reserved_by=self.kwargs['nick'])
        q_current_handling = Q(handlings__isnull=False, handlings__end__isnull=True)
        q_my_current_handling = Q(handlings__isnull=False, handlings__end__isnull=True, handlings__editor=self.kwargs['nick'])

        filters = [
            # tasks reserved for me with a current handling for me
            open_tasks.filter(q_reserved_by_me & q_my_current_handling),
            # tasks not reserved for me with a current handling for me
            open_tasks.filter(~q_reserved_by_me & q_my_current_handling),
            # tasks reserved for me without a current handling for me
            open_tasks.filter(q_reserved_by_me & ~q_my_current_handling),
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
                context['random_task'].lock(self.kwargs['nick'])
            context['random_task'].fill_nick(self.kwargs['nick'])

        return context


@decorators.class_decorator(decorators.board_view)
class CloneBoardView(CreateBoardView):
    template_name_suffix = '_form_clone'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['board_blueprint'] = self.kwargs['board']
        return context

    def form_valid(self, form):
        form.instance.cloned_from = self.kwargs['board']

        # form_valid issues save-command, needed for later copys
        return_value = super().form_valid(form)

        # copy tasks
        for task in form.instance.cloned_from.tasks.all():
            models.Task(board=form.instance,
                        label=task.label,
                        description=task.description,
                        reserved_until=now(),
                        cloned_from=task).save()

        return return_value


@decorators.class_decorator(decorators.board_admin_view)
class EditBoardView(UpdateView):
    model = models.Board
    fields = ['label']

    def get_object(self):
        return self.kwargs['board']

    def get_success_url(self):
        return self.object.get_admin_url()


@decorators.class_decorator(decorators.board_admin_view)
class DeleteBoardView(DeleteView):
    model = models.Board
    success_url = reverse_lazy('start')

    def get_object(self):
        return self.kwargs['board']
