from django.http import Http404

from . import FileView
from .. import decorators
from .. import models


try:
    from preview_generator.manager import PreviewManager

    preview_manager = PreviewManager('/tmp/preview_cache', create_folder=True)
    def get_preview_path(orig_path):
        return preview_manager.get_jpeg_preview(orig_path)

except ImportError:
    def get_preview_path(orig_path):
        return orig_path


class BaseView(FileView):
    def get_file_name(self, *args, **kwargs):
        attachment = models.Attachment.objects.get(pk=self.kwargs['attachment_id'])
        if attachment.handling.task.id != self.kwargs['task'].id:
            raise Http404
        return attachment.file.path


@decorators.class_decorator([decorators.board_view, decorators.require_name, decorators.task_view])
class PreviewView(BaseView):
    def get_file_name(self, *args, **kwargs):
        return get_preview_path(super().get_file_name(*args, **kwargs))


@decorators.class_decorator([decorators.board_view, decorators.require_name, decorators.task_view])
class FetchView(BaseView):
    pass
