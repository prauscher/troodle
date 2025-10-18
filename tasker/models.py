from datetime import timedelta
import json
from pywebpush import webpush, WebPushException

from django.db import models
from django.conf import settings
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


class Participant(models.Model):
    board = models.ForeignKey('Board', on_delete=models.CASCADE, related_name='participants', verbose_name=_('Board'))
    nick = models.CharField(_('Nick'), max_length=50)
    subscription_info = models.TextField(blank=True, null=True)

    def send_push(self, data):
        if self.subscription_info:
            try:
                webpush(
                    json.loads(self.subscription_info),
                    json.dumps(data),
                    vapid_private_key=settings.WEB_PUSH_KEYS[1],
                    vapid_claims={'sub': settings.WEB_PUSH_KEYS[2]})
            except WebPushException:
                # Purge subscription_info, once it failed
                self.subscription_info = None
                self.save()

    def __str__(self):
        return "{} ({})".format(self.nick, self.board)

    class Meta:
        verbose_name = _('Participant')
        verbose_name_plural = _('Participants')
        constraints = [
            models.UniqueConstraint(fields=['board', 'nick'], name='unique_nick'),
        ]


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
    hide_until = models.DateTimeField(_('hide until'), blank=True, null=True)
    repeat_after = models.DurationField(_('repeat after'), blank=True, null=True, help_text=_('Never fully close this task, but automatically make it re-appear once the given duration passed after closing it.'))
    priority = models.IntegerField(_('priority'), default=100, help_text=_('Priority of this task: Tasks with higher priority will be shown before those with lower priority.'))
    reserved_by = models.ForeignKey('Participant', on_delete=models.SET_NULL, blank=True, null=True)
    reserved_until = models.DateTimeField(_('reserved until'), default=now)
    cloned_from = models.ForeignKey('self', on_delete=models.CASCADE, related_name='clones', verbose_name=_('cloned from'), blank=True, null=True)
    requires = models.ManyToManyField('self', symmetrical=False, related_name='required_by', verbose_name=_('requires'), blank=True, help_text=_("Tasks which have to be done before this task can be started."))

    def __str__(self):
        return _("{board}: {label}").format(board=self.board, label=self.label)

    def get_frontend_url(self):
        return reverse('show_task', kwargs={'board_slug': self.board.slug, 'task_id': self.id})

    def action_allowed(self, action, participant):
        return action in self.get_allowed_actions(participant)

    def get_allowed_actions(self, participant):
        participant_status = self.get_participant_status(participant)
        return [action for action, states in Task.ACTIONS.items() if participant_status in states]

    def get_participant_status(self, participant):
        try:
            self.get_current_handling(participant)
            return Task.PROCESSING
        except Handling.DoesNotExist:
            if self.is_done():
                return Task.DONE
            if self.is_blocked():
                return Task.BLOCKED
            if self.is_locked_for(participant):
                return Task.RESERVED
            if self.is_unlocked():
                return Task.OPEN
            return Task.LOCKED

    def get_current_handling(self, participant=None):
        query = self.handlings.filter(end__isnull=True)
        if participant:
            return query.get(editor=participant)
        return query

    def get_total_duration(self):
        time = timedelta()
        for handling in self.handlings.filter(end__isnull=False):
            time = time + handling.get_duration()
        return time

    def get_blocking_tasks(self):
        # filter only undone tasks from self.requires
        # undone must have done=False and hide_until either None or in the future
        return self.requires.filter(models.Q(done=False) & ~models.Q(hide_until__gt=now()))

    def is_done(self):
        return self.done or (self.hide_until is not None and self.hide_until > now())

    def is_blocked(self):
        return self.get_blocking_tasks().count() > 0

    def is_repeating(self):
        return self.repeat_after is not None

    def is_processing(self, participant):
        try:
            self.get_current_handling(participant)
            return True
        except Handling.DoesNotExist:
            return False

    def is_locked(self):
        return not self.is_unlocked()

    def is_unlocked(self):
        return now() > self.reserved_until

    def is_locked_for(self, participant):
        return self.reserved_by == participant and self.is_locked()

    def mark_done(self):
        if self.is_repeating():
            self.hide_until = now() + self.repeat_after
        else:
            self.done = True
        self.save()

    def unlock(self):
        self.reserved_until = now()
        self.save()

    def lock(self, participant, duration=None):
        # TODO refresh value, add transaction
        if self.is_locked() and not self.is_locked_for(participant):
            raise ValueError(_('Task is already locked'))

        if duration is None:
            duration = timedelta(seconds=30)

        self.reserved_by = participant
        self.reserved_until = now() + duration
        self.save()

    def send_push(self, data, ignore_participant=None, include_finished=False):
        participants = set([handling.editor for handling in self.handlings.all() if (include_finished or handling.end is None) and handling.editor != ignore_participant])
        for participant in participants:
            participant.send_push(data)

    class Meta:
        ordering = ['board']
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')


class Handling(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='handlings', verbose_name=_('Task'))
    editor = models.ForeignKey('Participant', on_delete=models.CASCADE)
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
