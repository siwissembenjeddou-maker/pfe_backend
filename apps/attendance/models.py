from django.db import models
from apps.children.models import Child
from apps.users.models import User


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('late',    'Late'),
        ('absent',  'Absent'),
    ]

    child       = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='attendances')
    date        = models.DateField()
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recorded_attendances')
    notes       = models.TextField(blank=True)

    class Meta:
        ordering = ['-date', '-id']
        unique_together = ['child', 'date']

    def __str__(self):
        return f'{self.child.name} – {self.date} – {self.status}'
