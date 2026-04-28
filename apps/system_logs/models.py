from django.db import models
from apps.users.models import User


class SystemLog(models.Model):
    event    = models.CharField(max_length=200)
    user     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.event} – {self.user} – {self.timestamp}'

