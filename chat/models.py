"""Chat related models"""
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django_extra_tools.db.models import timestampable

from .manager import MessageManager


@python_2_unicode_compatible
class Room(timestampable.CreatedMixin, models.Model):
    """A class describing a chat room"""
    name = models.CharField(max_length=255, null=False, blank=False,
                            db_index=True, verbose_name=_('Room name'))
    users = models.ManyToManyField(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),  # Django 1.4 hack
        blank=False, related_name='chat_rooms', verbose_name=_('Room users'))

    class Meta(object):
        verbose_name = _('Room')
        verbose_name_plural = _('Rooms')

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'chat.models.Room[pk={}]'.format(self.pk)


@python_2_unicode_compatible
class Message(timestampable.CreatedAtMixin, models.Model):
    """A class describing a chat message"""
    room = models.ForeignKey('chat.Room', null=False, blank=False,
                             on_delete=models.CASCADE, related_name='messages',
                             verbose_name=_('Room'))
    sender = models.ForeignKey(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),  # Django 1.4 hack
        null=False, blank=False,
        verbose_name=_('Message author'))
    message = models.TextField(verbose_name=_('Message'))

    objects = MessageManager()

    class Meta(object):
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')

    def __str__(self):
        return self.message

    def __repr__(self):
        return 'chat.models.Message[pk={}]'.format(self.pk)


class MessageDelivery(models.Model):
    """A class describing a message delivery status"""
    message = models.ForeignKey('chat.Message', null=False, blank=False,
                                on_delete=models.CASCADE,
                                related_name='deliveries',
                                verbose_name=_('Message'))
    receiver = models.ForeignKey(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),  # Django 1.4 hack
        null=False, blank=False, verbose_name=_('Message receiver'))
    delivered_at = models.DateTimeField(null=True, blank=True,
                                        verbose_name=_('Message delivery date'))

    class Meta(object):
        verbose_name = _('Message delivery')
        verbose_name_plural = _('Messages delivery')

    def __repr__(self):
        return 'chat.models.MessageDelivery[pk={}]'.format(self.pk)


@receiver(post_save, sender=Message)
def set_delivery_status(instance, created, **kwargs):
    """post save signal to fill delivery status to false"""
    if created:
        users = instance.room.users.exclude(pk=instance.sender.pk)
        MessageDelivery.objects.bulk_create([
            MessageDelivery(message=instance, receiver=user)
            for user in users
        ])
