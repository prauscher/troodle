from django.http import Http404, FileResponse

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

@decorators.require_name
@decorators.board_view
@decorators.task_view
def preview(request, task, nick, attachment_id):
    attachment = models.Attachment.objects.get(pk=attachment_id)
    if attachment.handling.task.id != task.id:
        raise Http404

    return FileResponse(open(get_preview_path(attachment.file.path), 'rb'))


@decorators.require_name
@decorators.board_view
@decorators.task_view
def fetch(request, task, nick, attachment_id):
    attachment = models.Attachment.objects.get(pk=attachment_id)
    if attachment.handling.task.id != task.id:
        raise Http404

    return FileResponse(open(attachment.file.path, 'rb'))
