from __future__ import unicode_literals
from collections import OrderedDict

import uuid

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from .validators import validate_address


class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    callback_url = models.URLField()
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class AddressSubscription(Subscription):
    address = models.CharField(
        max_length=34,
        validators=[validate_address]
    )

    def as_dict(self):
        return OrderedDict([
            ('id', self.id),
            ('address', self.address),
            ('callback_url', self.callback_url),
            ('created_time', self.created_time)
        ])


class TxSubscription(Subscription):
    tx_hash = models.CharField(
        max_length=64,
        validators=[RegexValidator(r'^[0-9a-fA-F]{64}$')],
    )
    confirmation_count = models.PositiveIntegerField(
        validators=[MinValueValidator(1, 'confirmation_count should be greater than 1')]
    )

    def as_dict(self):
        return OrderedDict([
            ('id', self.id),
            ('tx_hash', self.tx_hash),
            ('confirmation_count', self.confirmation_count),
            ('callback_url', self.callback_url),
            ('created_time', self.created_time)
        ])


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_time = models.DateTimeField(auto_now_add=True)
    is_notified = models.BooleanField(default=False, editable=False)
    notification_attempts = models.PositiveIntegerField(default=0, editable=False)
    notification_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True


class AddressNotification(Notification):
    subscription = models.ForeignKey('AddressSubscription')
    tx_hash = models.CharField(
        max_length=64,
        validators=[RegexValidator(r'^[0-9a-fA-F]{64}$')],
    )
    class Meta(Notification.Meta):
        ordering = ('created_time',)


class LastSeenBlock(models.Model):
    name = models.CharField(max_length=30)
    block_hash = models.CharField(
        max_length=64,
        validators=[RegexValidator(r'^[0-9a-fA-F]{64}$')],
    )


class TxNotification(Notification):
    subscription = models.ForeignKey('TxSubscription')

