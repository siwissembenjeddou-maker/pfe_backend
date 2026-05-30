from django.db import models

from apps.children.models import Child
from apps.users.models import User


class PsychologistReport(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='psychologist_reports')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_psychologist_reports',
    )

    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'PsychologistReport(child_id={self.child_id}, created_at={self.created_at})'

