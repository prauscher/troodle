from django.urls import path
from django.conf import settings
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog

from .views import nick, board, tasks, handlings, attachments

urlpatterns = [
    path('', TemplateView.as_view(template_name='meta/start.html'), name='start'),
    path('meta/learn-more', TemplateView.as_view(template_name='meta/learn-more.html'), name='learn_more'),
    path('meta/imprint', TemplateView.as_view(template_name='meta/imprint.html'), name='imprint'),

    path('board/<slug:board_slug>/enter_nick', nick.EnterNickView.as_view(), name='enter_nick'),
    path('board/<slug:board_slug>/reset_nick', nick.ResetNickView.as_view(), name='reset_nick'),

    path('create_board/', board.CreateBoardView.as_view(), name='create_board'),

    path('board/<str:board_hash>/admin', board.BoardAdminView.as_view(), name='board_admin'),
    path('board/<str:board_hash>/edit', board.EditBoardView.as_view(), name='edit_board'),
    path('board/<str:board_hash>/delete', board.DeleteBoardView.as_view(), name='delete_board'),
    path('board/<str:board_hash>/create_task', tasks.CreateTaskView.as_view(), name='create_task'),
    path('board/<str:board_hash>/tasks/<int:task_id>/quickdone', tasks.QuickDoneTaskView.as_view(), name='quickdone_task'),
    path('board/<str:board_hash>/tasks/<int:task_id>/set_lock', tasks.SetLockTaskView.as_view(), name='set_task_lock'),
    path('board/<str:board_hash>/tasks/<int:task_id>/reset', tasks.ResetTaskView.as_view(), name='reset_task'),
    path('board/<str:board_hash>/tasks/<int:task_id>/edit', tasks.EditTaskView.as_view(), name='edit_task'),
    path('board/<str:board_hash>/tasks/<int:task_id>/delete', tasks.DeleteTaskView.as_view(), name='delete_task'),

    path('board/<slug:board_slug>', board.BoardView.as_view(), name='show_board'),
    path('board/<slug:board_slug>/monitor', board.BoardMonitorView.as_view(), name='board_monitor'),
    path('board/<slug:board_slug>/summary', board.BoardSummaryView.as_view(), name='board_summary'),
    path('board/<slug:board_slug>/tasks', tasks.TaskListView.as_view(), name='list_tasks'),
    path('board/<slug:board_slug>/request_link', board.BoardSendAdminLinkView.as_view(), name='request_board_link'),

    path('board/<slug:board_slug>/task/<int:task_id>', tasks.TaskView.as_view(), name='show_task'),
    path('board/<slug:board_slug>/task/<int:task_id>/start', handlings.StartTaskView.as_view(), name='create_handling'),
    path('board/<slug:board_slug>/task/<int:task_id>/comment', handlings.CommentTaskView.as_view(), name='comment_task'),
    path('board/<slug:board_slug>/task/<int:task_id>/abort', handlings.AbortTaskView.as_view(), name='abort_handling'),
    path('board/<slug:board_slug>/task/<int:task_id>/complete', handlings.CompleteTaskView.as_view(), name='complete_handling'),
    path('board/<slug:board_slug>/task/<int:task_id>/lock', tasks.LockTaskView.as_view(), name='lock_task'),
    path('board/<slug:board_slug>/task/<int:task_id>/unlock', tasks.UnlockTaskView.as_view(), name='unlock_task'),
    path('board/<slug:board_slug>/task/<int:task_id>/attachment/<int:attachment_id>/preview', attachments.PreviewView.as_view(), name='preview_attachment'),
    path('board/<slug:board_slug>/task/<int:task_id>/attachment/<int:attachment_id>/fetch', attachments.FetchView.as_view(), name='fetch_attachment'),

    path('sw.js', TemplateView.as_view(template_name='tasker/sw.js', content_type='text/javascript'), name='jssw'),
    path('app.js', TemplateView.as_view(template_name='tasker/app.js', content_type='text/javascript', extra_context={'push_pubkey': settings.WEB_PUSH_KEYS[0]}), name='jsapp'),
    path('register_webpush', nick.StoreWebPushView.as_view(), name='webpush_register'),
    # TODO add caching
    path('jsi18n.js', JavaScriptCatalog.as_view(), name='jsi18n'),
]
