#!/usr/bin/env python3

from django.views.generic.base import View
from django.http import HttpResponseRedirect, FileResponse
from django.urls import reverse

from .. import utils


class ActionView(View):
    default_pattern_name = None
    default_pattern_kwargs = {}

    def action(self, *args, **kwargs):
        raise NotImplementedError

    def get_default_pattern(self):
        return (self.default_pattern_name, self.default_pattern_kwargs)

    def get_default_url(self):
        return reverse(self.default_pattern_name, kwargs=self.default_pattern_kwargs)

    def get_redirect_url(self):
        return utils.get_redirect_url(self.request, default=self.get_default_url())

    def get(self, request, *args, **kwargs):
        self.action(*args, **kwargs)

        url = self.get_redirect_url()

        return HttpResponseRedirect(url)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class TaskActionBaseView(ActionView):
    def get_default_url(self):
        return self.kwargs['task'].get_frontend_url()


class FileView(View):
    def get_file_name(self, *args, **kwargs):
        raise NotImplementedError

    def get_file(self, *args, **kwargs):
        return open(self.get_file_name(*args, **kwargs), 'rb')

    def get(self, request, *args, **kwargs):
        file = self.get_file(*args, **kwargs)
        return FileResponse(file)
