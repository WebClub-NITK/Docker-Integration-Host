import uuid
from django.db import models
from django.conf import settings
from hosts.models import Host  

class Network(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name="networks")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    docker_network_id = models.CharField(max_length=64)
    name = models.CharField(max_length=100)
    driver = models.CharField(max_length=50)
    subnet = models.CharField(max_length=50, null=True, blank=True)
    gateway = models.CharField(max_length=50, null=True, blank=True)
    internal = models.BooleanField(default=False)
    attachable = models.BooleanField(default=True)
    labels = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.driver})"
