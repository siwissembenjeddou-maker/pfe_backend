from django.db import models
from apps.users.models import User


class ActivitySchedule(models.Model):
    ACTIVITY_TYPES = [
        ('Eating','Eating'), ('Drinking','Drinking'), ('Writing','Writing'),
        ('Playing','Playing'), ('Communicating','Communicating'),
        ('Social Interaction','Social Interaction'),
        ('Repetitive Behaviors','Repetitive Behaviors'),
        ('Sensory Response','Sensory Response'),
        ('Drawing','Drawing'), ('Reading','Reading'), ('Other','Other'),
    ]

    title           = models.CharField(max_length=200)
    description     = models.TextField(blank=True)
    date            = models.DateField()
    time            = models.TimeField()
    activity_type   = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    created_by      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules')
    participant_ids = models.JSONField(default=list)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'time']