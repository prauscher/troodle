from datetime import datetime
import random

from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.db.models import Q

from .. import models
from .. import decorators


class CreateBoardView(CreateView):
    model = models.Board
    fields = ['label']

    def get_success_url(self):
        return self.get_admin_url()


@decorators.class_decorator(decorators.board_admin_view)
class BoardAdminView(DetailView):
    model = models.Board
    template_name = 'tasker/board_admin.html'

    def get_object(self):
        return self.kwargs['board']


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
    def form_valid(self, form):
        form.instance.cloned_from = self.kwargs['board']

        # form_valid issues save-command, needed for later copys
        return_value = super().form_valid(form)

        # copy tasks
        for task in form.instance.cloned_from.tasks.all():
            task.pk = None
            task.board = form.instance
            # TODO reset reserved_until
            task.save()

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
