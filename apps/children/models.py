from django.db import models
from apps.users.models import User


class Child(models.Model):
    GENDER_CHOICES = [
        ('male',   'Male'),
        ('female', 'Female'),
        ('other',  'Other'),
    ]

    name          = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender        = models.CharField(max_length=10, choices=GENDER_CHOICES)
    parent        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='children')
    profile_image = models.ImageField(upload_to='children/', null=True, blank=True)
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} (parent: {self.parent.name})'

    @property
    def age(self):
        from datetime import date
        today = date.today()
        dob   = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))