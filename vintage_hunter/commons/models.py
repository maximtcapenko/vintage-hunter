import uuid

from django.db import models

class Base(models.Model):
    class Meta:
        abstract = True
        ordering = ['-created_at']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
