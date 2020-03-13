from datetime import timedelta

from django.utils.timezone import now

from . import TaskActionBaseView
from .. import decorators
from .. import models


@decorators.class_decorator([decorators.board_view, decorators.require_name, decorators.task_view, decorators.require_action('start', redirect_target='lock_task')])
class StartTaskView(TaskActionBaseView):
    def action(self, *args, **kwargs):
        self.kwargs['task'].lock(self.kwargs['participant'], timedelta(minutes=30))
        models.Handling(task=self.kwargs['task'], editor=self.kwargs['participant']).save()


class StopTaskBaseView(TaskActionBaseView):
    def action(self, *args, **kwargs):
        handling = self.kwargs['task'].get_current_handling(self.kwargs['participant'])
        handling.end = now()
        handling.success = self.success
        handling.save()

        if self.success:
            self.kwargs['task'].done = True
            self.kwargs['task'].save()

        if self.kwargs['task'].is_locked_for(self.kwargs['participant']):
            self.kwargs['task'].unlock()


@decorators.class_decorator([decorators.board_view, decorators.require_name, decorators.task_view, decorators.require_action('stop')])
class AbortTaskView(StopTaskBaseView):
    success = False


@decorators.class_decorator([decorators.board_view, decorators.require_name, decorators.task_view, decorators.require_action('stop')])
class CompleteTaskView(StopTaskBaseView):
    success = True


@decorators.class_decorator([decorators.board_view, decorators.require_name, decorators.task_view, decorators.require_action('comment')])
class CommentTaskView(TaskActionBaseView):
    def action(self, *args, **kwargs):
        handling = self.kwargs['task'].get_current_handling(self.kwargs['participant'])

        if "text" in self.request.POST and self.request.POST["text"]:
            models.Comment(handling=handling, text=self.request.POST["text"]).save()

        if "attachment" in self.request.FILES:
            models.Attachment(handling=handling, file=self.request.FILES["attachment"]).save()
