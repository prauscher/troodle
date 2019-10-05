from django.urls import path

from .views import start, nick, board, tasks, handlings

urlpatterns = [
    path('', start.start, name='start'),

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
    path('board/<slug:board_slug>/tasks', tasks.TaskListView.as_view(), name='list_tasks'),
    path('board/<slug:board_slug>/clone', board.CloneBoardView.as_view(), name='clone_board'),

    # show a single task (like board_index, but with a fixed task). options depend on current state
    # always: show label, description and handlings on this task
    # A: task is locked
    # B: task is locked for current user
    # C: current user has active handling
    #  A,  B,  C: 1. 'stop_handling' (success=0/1)
    #  A,  B, ~C: 2. 'create_handling', show countdown till 4
    #  A, ~B,  C: 1
    #  A, ~B, ~C: 3. "task locked until ..."
    # ~A,  B,  C: 1
    # ~A,  B, ~C: 4. 'lock_task'
    # ~A, ~B,  C: 1
    # ~A, ~B, ~C: 4
    #
    #   if  A & ~B & ~C: 3. "task locked until ..."
    # elif  C          : 1. 'stop_handling' (success=0/1)
    # elif ~A          : 4. 'lock_task'
    # elif  A &  B & ~C: 2. 'create_handling', show countdown till 4
    #
    # if task is locked AND unlock code is unknown AND current user has no active handling:
    #     "task locked until ..."
    # elif current user has active handling:
    #     'stop_handling' (success=0/1)
    # elif task is not locked:
    #     'lock_task'
    # elif task is locked AND unlock code is known and AND current user has no active handling:
    #     'create_handling', show countdown till 'lock_task'
    path('board/<slug:board_slug>/task/<int:task_id>', tasks.TaskView.as_view(), name='show_task'),

    # create a new handling-record for given user (and auto-start it), redirect to show_task afterwards
    path('board/<slug:board_slug>/task/<int:task_id>/start', handlings.start_task, name='create_handling'),

    path('board/<slug:board_slug>/task/<int:task_id>/comment', handlings.comment_task, name='comment_task'),

    # assume we have a current handling, set stop time and success based upon parameters, redirect to show_task or show_board
    path('board/<slug:board_slug>/task/<int:task_id>/stop/<int:success>', handlings.stop_task, name='stop_handling'),

    # lock a specific task (if possible) and redirect to show_task
    path('board/<slug:board_slug>/task/<int:task_id>/lock', tasks.lock_task, name='lock_task'),
    path('board/<slug:board_slug>/task/<int:task_id>/unlock', tasks.unlock_task, name='unlock_task'),
]
