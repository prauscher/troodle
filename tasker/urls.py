from django.urls import path

from . import views

urlpatterns = [
    # show greeting
    path('', views.start, name='start'),

    # show form and handle creation. redirect to board_admin on success
    path('create_board/', views.CreateBoardView.as_view(), name='create_board'),

    # show admin-page for board with options to modify tasks
    path('board/<str:board_hash>/admin', views.BoardAdminView.as_view(), name='board_admin'),

    # show form to change label
    path('board/<str:board_hash>/edit', views.EditBoardView.as_view(), name='edit_board'),

    # show board-toolbar and load a random task (using random_task_json)
    path('board/<slug:board_slug>', views.BoardView.as_view(), name='show_board'),

    # same as create_board, but clone specified board (including tasks, ignoring handlings)
    path('board/<slug:board_slug>/clone', views.CloneBoardView.as_view(), name='clone_board'),

    path('nick/enter', views.EnterNickView.as_view(), name='enter_nick'),

    path('nick/reset', views.reset_nick, name='reset_nick'),

    # show a single task (like board_index, but with a fixed task). options depend on current state
    # always: show label, description and handlings on this task
    # A: task is locked
    # B: unlock code is known
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
    path('board/<slug:board_slug>/task/<int:task_id>', views.TaskView.as_view(), name='show_task'),

    # create a new handling-record for given user (and auto-start it), redirect to show_task afterwards
    path('board/<slug:board_slug>/task/<int:task_id>/start', views.tmp, name='create_handling'),

    # assume we have a current handling, set stop time and success based upon parameters, redirect to show_task or show_board
    path('board/<slug:board_slug>/task/<int:task_id>/stop/<int:success>', views.tmp, name='stop_handling'),

    # lock a specific task (if possible) and redirect to show_task
    path('board/<slug:board_slug>/task/<int:task_id>/lock', views.tmp, name='lock_task'),

    path('board/<str:board_hash>/delete', views.tmp, name='delete_board'),
    path('board/<str:board_hash>/create_task', views.tmp, name='create_task'),
    path('board/<str:board_hash>/tasks/<int:task_id>/edit', views.tmp, name='edit_task'),
    path('board/<str:board_hash>/tasks/<int:task_id>/delete', views.tmp, name='delete_task'),
]
