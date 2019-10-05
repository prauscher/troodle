from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.utils.timezone import now
from django.db.models import Q

from .. import decorators
from .. import models
from .. import utils


@decorators.class_decorator(decorators.board_admin_view)
class CreateTaskView(CreateView):
    model = models.Task
    fields = ['label', 'description']

    def form_valid(self, form):
        form.instance.board = self.kwargs['board']
        return super().form_valid(form)

    def get_success_url(self):
        return self.kwargs['board'].get_admin_url()


@decorators.class_decorator([decorators.board_admin_view, decorators.task_view])
class EditTaskView(UpdateView):
    model = models.Task
    fields = ['label', 'description']

    def get_object(self):
        return self.kwargs['task']

    def get_success_url(self):
        return self.kwargs['task'].board.get_admin_url()


@decorators.class_decorator([decorators.board_admin_view, decorators.task_view])
class DeleteTaskView(DeleteView):
    model = models.Task

    def get_object(self):
        return self.kwargs['task']

    def get_success_url(self):
        return self.kwargs['task'].board.get_admin_url()


@decorators.class_decorator([decorators.board_admin_view, decorators.task_view])
class ResetTaskView(DeleteView):
    model = models.Task
    template_name = 'tasker/task_confirm_reset.html'

    def get_object(self):
        return self.kwargs['task']

    def delete(self, request, *args, **kwargs):
        self.get_object().reserved_by = ''
        self.get_object().reserved_until = now()
        self.get_object().save()

        for handling in self.get_object().handlings.all():
            handling.delete()

        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return self.kwargs['task'].board.get_admin_url()


@decorators.class_decorator([decorators.require_name, decorators.board_view, decorators.task_view])
class TaskView(DetailView):
    model = models.Task

    def get_object(self):
        self.kwargs['task'].fill_nick(self.kwargs['nick'])
        return self.kwargs['task']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


@decorators.class_decorator([decorators.require_name, decorators.board_view])
class TaskListView(ListView):
    paginate_by = 10

    def dispatch(self, *args, **kwargs):
        self.filters = {
            'unlocked': ('Unlocked', Q(reserved_until__lt=now())),
            'reserved': ('Reserved for me', Q(reserved_until__gte=now(), reserved_by=self.kwargs['nick'])),
        }
        return super().dispatch(*args, **kwargs)

    def get_active_filters(self):
        filter_ids = self.request.GET.get("filters", "").split(",")
        return [_id for _id, _filter in self.filters.items() if _id in filter_ids]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['board'] = self.kwargs['board']
        context['filters'] = {_id: _filter[0] for _id, _filter in self.filters.items()}
        context['active_filters'] = self.get_active_filters()

        # fill nick_status value
        for object in context['object_list']:
            object.fill_nick(self.kwargs['nick'])

        return context

    def get_queryset(self):
        queryset = models.Task.objects.all()

        for filter_id in self.get_active_filters():
            label, filter = self.filters[filter_id]
            queryset = queryset.filter(filter)

        return queryset


@decorators.require_name
@decorators.board_view
@decorators.task_view
@decorators.require_action('lock')
def lock_task(request, task, nick):
    task.lock(nick)

    return redirect(utils.get_redirect_url(request, default=task.get_frontend_url()))


@decorators.require_name
@decorators.board_view
@decorators.task_view
@decorators.require_action('unlock')
def unlock_task(request, task, nick):
    task.unlock()

    return redirect(utils.get_redirect_url(request, default=task.get_frontend_url()))
