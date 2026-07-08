import uuid
from django.db import models
from django.conf import settings

class Stack(models.Model):
    class Status(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        STARTING = 'STARTING', 'Starting'
        RUNNING = 'RUNNING', 'Running'
        STOPPED = 'STOPPED', 'Stopped'
        FAILED = 'FAILED', 'Failed'
        REMOVING = 'REMOVING', 'Removing'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    host = models.ForeignKey(
        'hosts.Host', 
        on_delete=models.CASCADE, 
        related_name='stacks'
    )
    compose_file = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.CREATED
    )
    error_message = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_stacks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('name', 'host')

    def __str__(self):
        return f"{self.name} [{self.status}] on {self.host.alias}"
