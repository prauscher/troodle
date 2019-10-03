from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.utils.http import is_safe_url
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView

from . import forms
from . import models
from . import decorators


def start(request):
    return render(request, 'tasker/start.html')


class EnterNickView(FormView):
    form_class = forms.EnterNickForm
    template_name = 'tasker/enter_nick.html'

    def form_valid(self, form):
        self.request.session['nick'] = form.cleaned_data['nick']
        return super().form_valid(form)

    def get_success_url(self):
        redirect_to = self.request.GET.get('next', reverse('start'))
        url_is_safe = is_safe_url(redirect_to, [])
        return redirect_to if url_is_safe else reverse('start')


@decorators.require_name
def reset_nick(request, nick):
    del request.session['nick']

    redirect_to = self.request.GET.get('next', reverse('start'))
    url_is_safe = is_safe_url(redirect_to, [])
    return redirect(redirect_to if url_is_safe else reverse('start'))


class CreateBoardView(CreateView):
    model = models.Board
    fields = ['label']

    def get_success_url(self):
        return reverse('board_admin', kwargs={'board_hash': self.object.generate_hash()})


@decorators.class_decorator(decorators.board_admin_view)
class BoardAdminView(DetailView):
    model = models.Board
    template_name = 'tasker/board_admin.html'

    def get_object(self):
        return self.kwargs['board']


@decorators.class_decorator([decorators.board_view, decorators.require_name])
class BoardView(DetailView):
    model = models.Board

    def get_object(self):
        return self.kwargs['board']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TODO add random (waiting: no active handling, not locked) task and lock it before rendering
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
        return reverse('board_admin', kwargs={'board_hash': self.object.generate_hash()})


@decorators.class_decorator([decorators.task_view, decorators.board_view, decorators.require_name])
class TaskView(DetailView):
    model = models.Task

    def get_object(self):
        return self.kwargs['task']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


def tmp(request, **kwargs):
    return HttpResponse("hello")
