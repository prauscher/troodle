from datetime import datetime, timedelta

from django.db import models
from django.core.signing import Signer
from autoslug import AutoSlugField

board_admin_signer = Signer('board_admin')
task_lock_signer = Signer('task_lock')


class Board(models.Model):
    slug = AutoSlugField(populate_from='label', unique=True)
    label = models.CharField(max_length=100)
    cloned_from = models.ForeignKey('self', on_delete=models.CASCADE, related_name='clones', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

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
    slug = AutoSlugField(populate_from='label', unique_with=['board'])
    label = models.CharField(max_length=100)
    board = models.ForeignKey('Board', on_delete=models.CASCADE, related_name='tasks')
    description = models.TextField()
    reserved_by = models.CharField(max_length=30, blank=True, null=True)
    reserved_until = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}: {}".format(self.board, self.label)

    def is_unlocked(self):
        now = datetime.now()
        return now > self.reserved_until

    def validate_code(self, code):
        id, reserved_until = task_lock_signer.unsign(code)

        if self.id != id:
            raise ValueError

        if self.reserved_until != reserved_until:
            raise ValueError

        if self.is_unlocked():
            raise ValueError

    def lock(self, duration=None):
        if duration is None:
            duration = timedelta(seconds=30)

        # TODO refresh value, add transaction
        self.reserved_until = datetime.now() + duration
        self.save()
        return task_log_signer.sign([self.id, self.reserved_until])

    class Meta:
        ordering = ['board']


class Handling(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='handlings')
    editor = models.CharField(max_length=30)
    start = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(blank=True, null=True)
    success = models.BooleanField()

    def __str__(self):
        # TODO add start / end if existing
        return "{} ({})".format(self.task, self.editor)

    class Meta:
        ordering = ['task', 'start']
        constraints = [
            models.UniqueConstraint(fields=['task', 'editor', 'start'], name='unique_handling'),
            # TODO constraint that end > start
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
