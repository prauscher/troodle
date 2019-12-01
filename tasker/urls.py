from django.urls import path
from django.views.generic import TemplateView

from .views import nick, board, tasks, handlings, attachments

urlpatterns = [
    path('', TemplateView.as_view(template_name='meta/start.html'), name='start'),
    path('meta/learn-more', TemplateView.as_view(template_name='meta/learn-more.html'), name='learn_more'),
    path('meta/imprint', TemplateView.as_view(template_name='meta/imprint.html'), name='imprint'),

    path('nick/enter', nick.EnterNickView.as_view(), name='enter_nick'),
    path('nick/reset', nick.reset_nick, name='reset_nick'),

    path('create_board/', board.CreateBoardView.as_view(), name='create_board'),

    path('board/<str:board_hash>/admin', board.BoardAdminView.as_view(), name='board_admin'),
    path('board/<str:board_hash>/edit', board.EditBoardView.as_view(), name='edit_board'),
    path('board/<str:board_hash>/delete', board.DeleteBoardView.as_view(), name='delete_board'),
    path('board/<str:board_hash>/create_task', tasks.CreateTaskView.as_view(), name='create_task'),
    path('board/<str:board_hash>/tasks/<int:task_id>/reset', tasks.ResetTaskView.as_view(), name='reset_task'),
    path('board/<str:board_hash>/tasks/<int:task_id>/edit', tasks.EditTaskView.as_view(), name='edit_task'),
    path('board/<str:board_hash>/tasks/<int:task_id>/delete', tasks.DeleteTaskView.as_view(), name='delete_task'),

    path('board/<slug:board_slug>', board.BoardView.as_view(), name='show_board'),
    path('board/<slug:board_slug>/summary', board.BoardSummaryView.as_view(), name='board_summary'),
    path('board/<slug:board_slug>/tasks', tasks.TaskListView.as_view(), name='list_tasks'),
    path('board/<slug:board_slug>/request_link', board.BoardSendAdminLinkView.as_view(), name='request_board_link'),

    path('board/<slug:board_slug>/task/<int:task_id>', tasks.TaskView.as_view(), name='show_task'),
    path('board/<slug:board_slug>/task/<int:task_id>/start', handlings.start_task, name='create_handling'),
    path('board/<slug:board_slug>/task/<int:task_id>/comment', handlings.comment_task, name='comment_task'),
    path('board/<slug:board_slug>/task/<int:task_id>/abort', handlings.abort_task, name='abort_handling'),
    path('board/<slug:board_slug>/task/<int:task_id>/complete', handlings.complete_task, name='complete_handling'),
    path('board/<slug:board_slug>/task/<int:task_id>/lock', tasks.lock_task, name='lock_task'),
    path('board/<slug:board_slug>/task/<int:task_id>/unlock', tasks.unlock_task, name='unlock_task'),
    path('board/<slug:board_slug>/task/<int:task_id>/attachment/<int:attachment_id>/preview', attachments.preview, name='preview_attachment'),
    path('board/<slug:board_slug>/task/<int:task_id>/attachment/<int:attachment_id>/fetch', attachments.fetch, name='fetch_attachment'),
]
