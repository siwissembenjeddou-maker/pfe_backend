from django.db import models
from apps.users.models import User


class Notification(models.Model):
    TYPE_CHOICES = [
        ('assessment_result',  'Assessment Result'),
        ('review_complete',     'Review Complete'),
        ('message',            'Message'),
        ('reminder',           'Reminder'),
        ('psychologist_report','Psychologist Report'),
        ('child_added',        'Child Added'),
        ('system',             'System'),
    ]

    recipient  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    type       = models.CharField(max_length=30, choices=TYPE_CHOICES, default='system')
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.recipient.name}: {self.title}'