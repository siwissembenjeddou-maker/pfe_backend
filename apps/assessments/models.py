from django.db import models
from apps.children.models import Child
from apps.users.models import User


class Assessment(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending Review'),
        ('confirmed', 'Confirmed by Psychologist'),
        ('corrected', 'Corrected by Psychologist'),
    ]
    SEVERITY_CHOICES = [
        ('mild',     'Mild'),
        ('moderate', 'Moderate'),
        ('severe',   'Severe'),
    ]

    child               = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='assessments')
    activity_type       = models.CharField(max_length=100)
    audio_file          = models.FileField(upload_to='audio/', null=True, blank=True)
    audio_transcription = models.TextField()

    autism_score              = models.FloatField()
    severity_level            = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    dimension_scores          = models.JSONField(default=dict)
    ai_analysis               = models.TextField(blank=True)
    key_observations          = models.JSONField(default=list)
    immediate_recommendations = models.JSONField(default=list)

    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by      = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_assessments')
    psychologist_note = models.TextField(blank=True)
    corrected_score  = models.FloatField(null=True, blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.child.name} – {self.activity_type} – {self.autism_score}'

    @property
    def effective_score(self):
        return self.corrected_score if self.corrected_score is not None else self.autism_score