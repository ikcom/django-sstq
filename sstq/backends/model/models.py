import uuid
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import gettext_lazy as _


class Queue(models.Model):
    name = models.CharField(
        primary_key=True,
        verbose_name=_("Name"),
        max_length=80,
    )


class Task(models.Model):
    class Status(models.IntegerChoices):
        AVAILABLE = 0, _("Available")
        RUNNING = 1, _("Running")
        FAILED = 2, _("Failed")
        DONE = 3, _("Done")

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("UUID"),
    )
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=255,
        db_index=True,
        blank=False,
        null=False,
    )
    queue = models.ForeignKey(
        to=Queue,
        verbose_name=_("Queue"),
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="tasks",
    )
    kwargs = models.JSONField[dict[str, Any]](
        verbose_name=_("Keyword arguments"), default=dict, encoder=DjangoJSONEncoder
    )
    result = models.JSONField[dict[str, Any]](
        verbose_name=_("Result"), default=dict, encoder=DjangoJSONEncoder
    )
    status = models.IntegerField(
        verbose_name=_("Status"),
        blank=False,
        null=False,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    traceback = models.TextField(
        verbose_name=_("Traceback"),
        blank=True,
        null=True,
    )
    queue_time = models.DateTimeField(
        verbose_name=_("Queue Time"),
        auto_now_add=True,
    )

    class Meta:
        ordering = ("-queue_time",)
