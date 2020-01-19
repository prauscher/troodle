from datetime import timedelta

from django.db import models
from django.urls import reverse
from django.core.signing import Signer
from django.core.mail import EmailMessage
from django.utils.timezone import now
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _
from autoslug import AutoSlugField

BOARD_ADMIN_SIGNER = Signer(salt='board_admin')
ADMIN_MAIL_DELAY = timedelta(days=1)


class Board(models.Model):
    slug = AutoSlugField(_('slug'), populate_from='label', unique=True)
    label = models.CharField(_('label'), max_length=100)
    admin_id = models.CharField(_('admin id'), unique=True, max_length=30, help_text=_('id used to authenticate for admin interface'))
    admin_mail = models.EmailField(_('admin mail'), blank=True, null=True, help_text=_("Your Mailadress. Will only be used to send you mails with links to frontend and backend."))
    last_admin_mail_sent = models.DateTimeField(_('last time a mail to the admin was sent'), blank=True, null=True)
    cloned_from = models.ForeignKey('self', on_delete=models.CASCADE, related_name='clones', verbose_name=_('cloned from'), blank=True, null=True)
    created = models.DateTimeField(_('created'), auto_now_add=True)

    # used for django-admin
    def get_absolute_url(self):
        return self.get_admin_url()

    def get_admin_url(self):
        return reverse('board_admin', kwargs={'board_hash': self.generate_hash()})

    def get_frontend_url(self):
        return reverse('show_board', kwargs={'board_slug': self.slug})

    def generate_hash(self):
        return BOARD_ADMIN_SIGNER.sign(self.admin_id)

    @classmethod
    def get_by_hash(cls, board_hash):
        board_id = BOARD_ADMIN_SIGNER.unsign(board_hash)
        return cls.objects.get(admin_id=board_id)

    def send_admin_mail(self, request):
        # TODO use different exceptions
        if not self.admin_mail:
            raise ValueError(_("No Admin mail stored"))

        if self.last_admin_mail_sent and now() < self.last_admin_mail_sent + ADMIN_MAIL_DELAY:
            raise ValueError(_("Last admin mail has been sent too recently."))

        body = get_template("board_mail.txt").render({
            'label': self.label,
            'admin_link': request.build_absolute_uri(self.get_admin_url()),
            'frontend_link': request.build_absolute_uri(self.get_frontend_url()),
        })
        message = EmailMessage(to=[self.admin_mail], subject=_("Your Troodle-Board {label}").format(label=self.label), body=body)
        message.send()

        # reset counter
        self.last_admin_mail_sent = now()
        self.save()

    def __str__(self):
        return self.label

    def save(self):
        super().save()

        # check after saving to have pk initialized
        if not self.admin_id:
            self.admin_id = self.pk
            super().save()

    class Meta:
        ordering = ['created']
        verbose_name = _('Board')
        verbose_name_plural = _('Boards')


class Task(models.Model):
    OPEN = 'o'
    LOCKED = 'l'
    BLOCKED = 'b'
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

    slug = AutoSlugField(_('slug'), populate_from='label', unique_with=['board'])
    label = models.CharField(_('label'), max_length=100)
    board = models.ForeignKey('Board', on_delete=models.CASCADE, related_name='tasks', verbose_name=_('Board'))
    description = models.TextField(_('description'))
    done = models.BooleanField(_('done'), default=False)
    reserved_by = models.CharField(_('reserved by'), max_length=30, blank=True, null=True)
    reserved_until = models.DateTimeField(_('reserved until'), default=now)
    cloned_from = models.ForeignKey('self', on_delete=models.CASCADE, related_name='clones', verbose_name=_('cloned from'), blank=True, null=True)
    requires = models.ManyToManyField('self', symmetrical=False, related_name='required_by', verbose_name=_('requires'), blank=True)

    def __str__(self):
        return _("{board}: {label}").format(board=self.board, label=self.label)

    def get_frontend_url(self):
        return reverse('show_task', kwargs={'board_slug': self.board.slug, 'task_id': self.id})

    def get_nick_status(self, nick):
        try:
            self.get_current_handling(nick)
            return Task.PROCESSING
        except Handling.DoesNotExist:
            if self.done:
                return Task.DONE
            if self.is_blocked():
                return Task.BLOCKED
            if self.is_locked_for(nick):
                return Task.RESERVED
            if self.is_unlocked():
                return Task.OPEN
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

    def get_current_handling(self, nick=None):
        query = self.handlings.filter(end__isnull=True)
        if nick:
            return query.get(editor=nick)
        return query

    def get_total_duration(self):
        time = timedelta()
        for handling in self.handlings.filter(end__isnull=False):
            time = time + handling.get_duration()
        return time

    def get_blocking_tasks(self):
        return self.requires.filter(done=False)

    def is_blocked(self):
        return self.get_blocking_tasks().count() > 0

    def is_locked(self):
        return not self.is_unlocked()

    def is_unlocked(self):
        return now() > self.reserved_until

    def is_locked_for(self, nick):
        return self.reserved_by == nick and self.is_locked()

    def unlock(self):
        self.reserved_until = now()
        self.save()

    def lock(self, nick, duration=None):
        # TODO refresh value, add transaction
        if self.is_locked() and not self.is_locked_for(nick):
            raise ValueError(_('Task is already locked'))

        if duration is None:
            duration = timedelta(seconds=30)

        self.reserved_by = nick
        self.reserved_until = now() + duration
        self.save()

    class Meta:
        ordering = ['board']
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')


class Handling(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='handlings', verbose_name=_('Task'))
    editor = models.CharField(_('editor'), max_length=30)
    start = models.DateTimeField(_('start'), default=now)
    end = models.DateTimeField(_('end'), blank=True, null=True)
    success = models.BooleanField(_('successfully'), blank=True, null=True)

    def get_duration(self):
        return self.end - self.start

    def __str__(self):
        # TODO add start / end if existing
        return _("{task} ({editor})").format(task=self.task, editor=self.editor)

    class Meta:
        ordering = ['task', 'start']
        verbose_name = _('Handling')
        verbose_name_plural = _('Handlings')
        constraints = [
            models.UniqueConstraint(fields=['task', 'editor', 'start'], name='unique_start'),
            models.UniqueConstraint(fields=['task', 'editor', 'end'], name='unique_end'),
            # TODO constraint that end > start
            # TODO success and end can only be null together
        ]


class Note(models.Model):
    handling = models.ForeignKey('Handling', on_delete=models.CASCADE, related_name='%(app_label)s_%(class)ss', verbose_name=_('Notes'))
    posted = models.DateTimeField(_('posted'), auto_now_add=True)

    def __str__(self):
        return _("{type} at {posted:%Y-%m-%d %H:%I:%S} at {handling}").format(type=self.__class__.__name__, posted=self.posted, handling=self.handling)

    class Meta:
        ordering = ['handling', 'posted']
        abstract = True
        verbose_name = _('Note')
        verbose_name_plural = _('Notes')


class Comment(Note):
    text = models.TextField(_('text'))

    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')


class Attachment(Note):
    file = models.FileField(_('file'), upload_to="attachments/")

    class Meta:
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')
