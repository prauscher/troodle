from datetime import timedelta

from django.db import models
from django.urls import reverse
from django.core.signing import Signer
from django.utils.timezone import now
from autoslug import AutoSlugField

board_admin_signer = Signer('board_admin')


class Board(models.Model):
    slug = AutoSlugField(populate_from='label', unique=True)
    label = models.CharField(max_length=100)
    cloned_from = models.ForeignKey('self', on_delete=models.CASCADE, related_name='clones', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return self.get_admin_url()

    def get_admin_url(self):
        return reverse('board_admin', kwargs={'board_hash': self.generate_hash()})

    def get_frontend_url(self):
        return reverse('show_board', kwargs={'board_slug': self.slug})

    def generate_hash(self):
        return board_admin_signer.sign(self.id)

    @classmethod
    def get_by_hash(cls, hash):
        id = board_admin_signer.unsign(hash)
        return cls.objects.get(id=id)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ['created']


class Task(models.Model):
    OPEN = 'o'
    LOCKED = 'l'
    RESERVED = 'r'
    PROCESSING = 'p'
    DONE = 'd'

    ACTIONS = {
        'lock': [OPEN],
        'unlock': [RESERVED],
        'start': [RESERVED],
        'stop': [PROCESSING],
        'comment': [PROCESSING],
    }

    slug = AutoSlugField(populate_from='label', unique_with=['board'])
    label = models.CharField(max_length=100)
    board = models.ForeignKey('Board', on_delete=models.CASCADE, related_name='tasks')
    description = models.TextField()
    reserved_by = models.CharField(max_length=30, blank=True, null=True)
    reserved_until = models.DateTimeField(default=now)

    def __str__(self):
        return "{}: {}".format(self.board, self.label)

    def get_frontend_url(self):
        return reverse('show_task', kwargs={'board_slug': self.board.slug, 'task_id': self.id})

    def get_nick_status(self, nick):
        try:
            self.handlings.get(editor=nick, end__isnull=True)
            return Task.PROCESSING
        except Handling.DoesNotExist:
            if self.handlings.filter(end__isnull=False, success=True).exists():
                return Task.DONE
            elif self.is_locked_for(nick):
                return Task.RESERVED
            elif self.is_unlocked():
                return Task.OPEN
            else:
                return Task.LOCKED

    def fill_nick(self, nick):
        self.nick_status = self.get_nick_status(nick)
        self.allowed_actions = [action for action, status in self.ACTIONS.items() if self.nick_status in status]

    def action_allowed(self, action, nick=None):
        if nick is None:
            if not self.nick_status:
                raise ValueError

            nick_status = self.nick_status
        else:
            nick_status = self.get_nick_status(nick)

        return nick_status in self.ACTIONS[action]

    def get_current_handling(self, nick):
        return self.handlings.get(editor=nick, end=None)

    def is_unlocked(self):
        return now() > self.reserved_until

    def is_locked_for(self, nick):
        return self.reserved_by == nick and not self.is_unlocked()

    def unlock(self):
        self.reserved_until = now()
        self.save()

    def lock(self, nick, duration=None):
        # TODO refresh value, add transaction
        if not self.is_unlocked() and not self.is_locked_for(nick):
            raise ValueError('Task is already locked')

        if duration is None:
            duration = timedelta(seconds=30)

        self.reserved_by = nick
        self.reserved_until = now() + duration
        self.save()

    class Meta:
        ordering = ['board']


class Handling(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='handlings')
    editor = models.CharField(max_length=30)
    start = models.DateTimeField(default=now)
    end = models.DateTimeField(blank=True, null=True)
    success = models.BooleanField(blank=True, null=True)

    def get_duration(self):
        return self.end - self.start

    def __str__(self):
        # TODO add start / end if existing
        return "{} ({})".format(self.task, self.editor)

    class Meta:
        ordering = ['task', 'start']
        constraints = [
            models.UniqueConstraint(fields=['task', 'editor', 'start'], name='unique_start'),
            models.UniqueConstraint(fields=['task', 'editor', 'end'], name='unique_end'),
            # TODO constraint that end > start
            # TODO success and end can only be null together
        ]


class Note(models.Model):
    handling = models.ForeignKey('Handling', on_delete=models.CASCADE, related_name='%(app_label)s_%(class)ss')
    posted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} am {:%Y-%m-%d %H:%I:%S} bei {}".format(self.__class__.__name__, self.posted, self.handling)

    class Meta:
        ordering = ['handling', 'posted']
        abstract = True


class Comment(Note):
    text = models.TextField()


class Attachment(Note):
    file = models.FileField(upload_to="attachments/")
