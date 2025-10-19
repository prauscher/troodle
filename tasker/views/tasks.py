from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponseRedirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from . import TaskActionBaseView
from .. import auth
from .. import decorators
from .. import models
from .. import utils


class DurationField(forms.CharField):
    UNITS = [
        (timedelta(days=7), _("week"), _("weeks"), ["w"]),
        (timedelta(days=1), _("day"), _("days"), ["d"]),
        (timedelta(hours=1), _("hour"), _("hours"), ["h"]),
        (timedelta(minutes=1), _("minute"), _("minutes"), ["m"]),
        (timedelta(seconds=1), _("second"), _("seconds"), ["s"]),
    ]

    def _tokenize(self, value):
        current_token = ""
        delimiters = "., "
        while value or current_token:
            char = value[0:1]

            if char in delimiters or char == "" or current_token.isnumeric() != char.isnumeric():
                if current_token:
                    yield current_token
                current_token = ""

            if char not in delimiters:
                current_token += char

            # next iteration step
            value = value[1:]

    def to_python(self, value):
        if not value.strip():
            return None

        units = {}
        for unit_value, singular, plural, other_units in self.UNITS:
            units[singular] = unit_value
            units[plural] = unit_value
            for unit in other_units:
                units[unit] = unit_value

        tokens = list(self._tokenize(value))
        duration = timedelta(seconds=0)
        while tokens:
            count = tokens.pop(0)
            if count.isnumeric() and not tokens:
                unit = timedelta(seconds=1)
            elif count.isnumeric() and tokens[0] in units:
                unit = units[tokens.pop(0)]
            else:
                raise ValidationError(_("Invalid format for duration, valid example: 3 weeks 2 days"))

            duration += int(count) * unit

        return duration

    def prepare_value(self, value):
        if not value or not isinstance(value, timedelta):
            return value

        parts = []
        for duration, singular, plural, _ in self.UNITS:
            count = value // duration
            if count > 1:
                parts.append(f"{count} {plural}")
            elif count == 1:
                parts.append(f"{count} {singluar}")
            value -= count * duration
        return ", ".join(parts)


class TaskForm(forms.ModelForm):
    repeat_after = DurationField(label=models.Task._meta.get_field("repeat_after").verbose_name,
                                 required=False,
                                 help_text=models.Task._meta.get_field("repeat_after").help_text)

    class Meta:
        model = models.Task
        fields = ['label', 'description', 'requires', 'priority', 'repeat_after']

    def __init__(self, *args, board, instance, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)
        self.fields['requires'].queryset = models.Task.objects.filter(board=board)
        if instance:
            self.fields['requires'].queryset = self.fields['requires'].queryset.exclude(pk=instance.pk)


class QuickDoneForm(forms.Form):
    editor = forms.CharField(label=_('Nickname'), min_length=3, max_length=30)
    duration = forms.DurationField(label=_('Duration'))

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data['duration'] < timedelta(0):
            self.add_error('duration', _("Duration must be positive"))

        return cleaned_data


@decorators.class_decorator(decorators.board_admin_view)
class CreateTaskView(auth.AuthBoardMixin, CreateView):
    form_class = TaskForm
    template_name = "tasker/task_form.html"

    def form_valid(self, form):
        form.instance.board = self.kwargs['board']
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['board'] = self.kwargs['board']
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['board'] = self.kwargs['board']
        return kwargs

    def get_success_url(self):
        return utils.get_redirect_url(self.request, default=self.kwargs['board'].get_admin_url())


class EditTaskBaseView(auth.AuthBoardMixin, UpdateView):
    def get_object(self):
        return self.kwargs['task']

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['board'] = self.kwargs['task'].board
        return context

    def get_success_url(self):
        return utils.get_redirect_url(self.request, default=self.kwargs['task'].board.get_admin_url())


@decorators.class_decorator([decorators.board_admin_view, decorators.task_view])
class EditTaskView(EditTaskBaseView):
    form_class = TaskForm
    template_name = "tasker/task_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['board'] = self.kwargs['task'].board
        return kwargs


@decorators.class_decorator([decorators.board_admin_view, decorators.task_view])
class DeleteTaskView(auth.AuthBoardMixin, DeleteView):
    model = models.Task

    def get_object(self):
        return self.kwargs['task']

    def get_success_url(self):
        return utils.get_redirect_url(self.request, default=self.kwargs['task'].board.get_admin_url())


@decorators.class_decorator([decorators.board_admin_view, decorators.task_view])
class SetLockTaskView(EditTaskBaseView):
    model = models.Task
    fields = ['reserved_by', 'reserved_until']
    template_name = 'tasker/task_set_lock.html'


@decorators.class_decorator([decorators.board_admin_view, decorators.task_view])
class QuickDoneTaskView(auth.AuthBoardMixin, FormView):
    form_class = QuickDoneForm
    template_name = 'tasker/task_quickdone.html'

    def form_valid(self, form):
        editor, _ = models.Participant.objects.get_or_create(
            nick=form.cleaned_data['editor'],
            board=self.kwargs['task'].board,
        )
        end = now()

        models.Handling.objects.create(
            task=self.kwargs['task'],
            editor=editor,
            start=end - form.cleaned_data['duration'],
            end=end,
            success=True,
        )

        self.kwargs['task'].mark_done()

        for open_handling in self.kwargs['task'].handlings.filter(end__isnull=True):
            open_handling.end = now()
            open_handling.success = False
            open_handling.save()

        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['task'] = self.kwargs['task']
        return context

    def get_success_url(self):
        return utils.get_redirect_url(self.request, default=self.kwargs['task'].board.get_admin_url())


class ResetTaskForm(forms.Form):
    handling_action = forms.ChoiceField(
        label="",
        choices=[("delete_all", _("delete all handlings")),
                 ("delete_open", _("delete open handlings, leave others")),
                 ("close_open", _("close open handlings"))],
    )


@decorators.class_decorator([decorators.board_admin_view, decorators.task_view])
class ResetTaskView(auth.AuthBoardMixin, FormView):
    model = models.Task
    form_class = ResetTaskForm
    template_name = 'tasker/task_confirm_reset.html'

    def get_object(self):
        return self.kwargs['task']

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['object'] = self.get_object()
        return context

    def form_valid(self, form):
        object = self.get_object()
        object.reserved_by = None
        object.reserved_until = now()
        object.done = False
        object.hide_until = None
        object.save()

        handling_action = form.cleaned_data["handling_action"]

        handlings = object.handlings.all()
        if handling_action == "delete_open" or handling_action == "close_open":
            handlings = handlings.filter(end__isnull=True)

        for handling in handlings:
            if handling_action == "delete_all" or handling_action == "delete_open":
                handling.delete()
            else:
                handling.end = now()
                handling.success = False
                handling.save()

        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return utils.get_redirect_url(self.request, default=self.kwargs['task'].board.get_admin_url())


@decorators.class_decorator([decorators.board_view, decorators.require_name, decorators.task_view])
class TaskView(auth.AuthBoardMixin, DetailView):
    model = models.Task

    def get_object(self):
        return self.kwargs['task']


class TaskListBase(auth.AuthBoardMixin, ListView):
    paginate_by = 20
    search_fields = ['label', 'description', 'handlings__editor__nick', 'handlings__tasker_comments__text']

    def get_filters(self):
        return {
            'locked': (_('Locked'), Q(reserved_until__gte=now())),
            'active': (_('Active'), Q(done=False, handlings__isnull=False, handlings__end__isnull=True)),
            'done': (_('Done'), Q(done=True) | Q(hide_until__gt=now())),
            'blocked': (_('Blocked'), Q(requires__done=False) & ~Q(requires__hide_until__gt=now())),
            'repeating': (_('Repeating'), Q(repeat_after__isnull=False)),
        }

    def dispatch(self, *args, **kwargs):
        # do not cache this in __init__, as self.request won't be set there (which is needed by get_filters)

        # cache filters
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

    def get_search_terms(self):
        return [term for term in self.get_search_term().split(' ') if term]

    def get_search_fields(self):
        return self.search_fields

    def get_search_filter(self):
        # Q(pk=None) is a hacky way to say "always false"
        search_filter = ~Q(pk=None)
        for term in self.get_search_terms():
            term_filter = Q(pk=None)
            for field in self.get_search_fields():
                term_filter = term_filter | Q(**{"{}__icontains".format(field): term})
            search_filter = search_filter & term_filter
        return search_filter

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
            _, search_filter = self.filters[filter_id]
            queryset = queryset.exclude(search_filter)

        for filter_id in self.get_active_filters():
            _, search_filter = self.filters[filter_id]
            queryset = queryset.filter(search_filter)

        queryset = queryset.filter(self.get_search_filter())

        queryset = queryset.distinct()

        return queryset


@decorators.class_decorator([decorators.board_view, decorators.require_name])
class TaskListView(TaskListBase):
    template_name = 'tasker/task_list.html'

    def get_filters(self):
        search_filters = super().get_filters()
        search_filters.update({
            'mine': (_('Mine'), Q(handlings__isnull=False, handlings__editor=self.kwargs['participant']) | Q(reserved_by=self.kwargs['participant'], reserved_until__gte=now())),
        })
        return search_filters


@decorators.class_decorator([decorators.board_view, decorators.require_name, decorators.task_view, decorators.require_action('lock')])
class LockTaskView(TaskActionBaseView):
    def action(self, *args, **kwargs):
        self.kwargs['task'].lock(self.kwargs['participant'])


@decorators.class_decorator([decorators.board_view, decorators.require_name, decorators.task_view])
class UnlockTaskView(TaskActionBaseView):
    def action(self, *args, **kwargs):
        # do nothing if unlock is not needed
        # this will avoid errors if users click unlock too late
        if self.kwargs['task'].is_locked():
            if not self.kwargs['task'].action_allowed('unlock', self.kwargs['participant']):
                raise Http404

            self.kwargs['task'].unlock()
