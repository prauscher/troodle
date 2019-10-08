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

    def get_context_data(self):
        context = super().get_context_data()
        context['board'] = self.kwargs['board']
        return context

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


class TaskListBase(ListView):
    paginate_by = 2

    def get_filters(self):
        return {
            'locked': ('Locked', Q(reserved_until__gte=now())),
            'active': ('Active', Q(handlings__isnull=False, handlings__end__isnull=True)),
            'done': ('Done', Q(handlings__isnull=False, handlings__success=True)),
        }

    def dispatch(self, *args, **kwargs):
        self.filters = self.get_filters()
        return super().dispatch(*args, **kwargs)

    def get_active_filters(self):
        filter_ids = self.request.GET.get("filters", "").split(",")
        return [_id for _id, _filter in self.filters.items() if _id in filter_ids]

    def get_active_excludes(self):
        filter_ids = self.request.GET.get("excludes", "").split(",")
        return [_id for _id, _filter in self.filters.items() if _id in filter_ids]

    def get_search_term(self):
        return self.request.GET.get("search", "")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.get_search_term()
        context['board'] = self.kwargs['board']
        context['filters'] = {_id: _filter[0] for _id, _filter in self.filters.items()}
        context['active_filters'] = self.get_active_filters()
        context['active_excludes'] = self.get_active_excludes()

        return context

    def get_queryset(self):
        queryset = self.kwargs['board'].tasks.all()

        for filter_id in self.get_active_excludes():
            label, filter = self.filters[filter_id]
            queryset = queryset.exclude(filter)

        for filter_id in self.get_active_filters():
            label, filter = self.filters[filter_id]
            queryset = queryset.filter(filter)

        search_term = self.get_search_term()
        if search_term:
            queryset = queryset.filter(Q(label__icontains=search_term) | Q(description__icontains=search_term))

        queryset = queryset.distinct()

        return queryset


@decorators.class_decorator([decorators.require_name, decorators.board_view])
class TaskListView(TaskListBase):
    template_name = 'tasker/task_list.html'

    def get_filters(self):
        filters = super().get_filters()
        filters.update({
            'mine': ('Mine', Q(handlings__isnull=False, handlings__editor=self.kwargs['nick']) | Q(reserved_by=self.kwargs['nick'], reserved_until__gte=now())),
        })
        return filters

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # fill nick_status value
        for object in context['object_list']:
            object.fill_nick(self.kwargs['nick'])

        return context


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
