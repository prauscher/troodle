from django.db import models
from autoslug import AutoSlugField


class Board(models.Model):
    slug = AutoSlugField(populate_from='label', unique=True)
    label = models.CharField(max_length=100)
    cloned_from = models.ForeignKey('self', on_delete=models.CASCADE, related_name='clones', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.label


class Task(models.Model):
    slug = AutoSlugField(populate_from='label', unique_with=['board'])
    label = models.CharField(max_length=100)
    board = models.ForeignKey('Board', on_delete=models.CASCADE, related_name='tasks')
    description = models.TextField()
    reserved_until = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}: {}".format(self.board, self.label)


class Handling(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='handlings')
    editor = models.CharField(max_length=30)
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    success = models.BooleanField()

    def __str__(self):
        # TODO add start / end if existing
        return "{} ({})".format(self.task, self.editor)


class Note(models.Model):
    handling = models.ForeignKey('Handling', on_delete=models.CASCADE, related_name='%(app_label)s_%(class)ss')
    posted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} am {:%Y-%m-%d %H:%I:%S} bei {}".format(self.__class__.__name__, self.posted, self.handling)


    class Meta:
        abstract = True


class Comment(Note):
    text = models.TextField()


class Attachment(Note):
    file = models.FileField(upload_to="attachments/")
