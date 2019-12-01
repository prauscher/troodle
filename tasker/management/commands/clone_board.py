from django.core.management.base import BaseCommand
from django.utils.timezone import now

from tasker.models import Board, Task


class Command(BaseCommand):
    help = ''

    def add_arguments(self, parser):
        parser.add_argument('board_id', type=int)
        parser.add_argument('label')
        parser.add_argument('--admin-mail')

    def handle(self, board_id, label, admin_mail, *args, **kwargs):
        board = Board.objects.get(pk=board_id)
        cloned = Board(label=label,
                       admin_mail=admin_mail,
                       cloned_from=board)
        cloned.save()

        for task in board.tasks.all():
            Task(board=cloned,
                 label=task.label,
                 description=task.description,
                 reserved_until=now(),
                 cloned_from=task).save()

        print("Done: {} / {}".format(cloned.get_admin_url(), cloned.get_frontend_url()))

