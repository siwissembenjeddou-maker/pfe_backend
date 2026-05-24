import random
import string
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin',        'Admin'),
        ('parent',       'Parent'),
        ('psychologist', 'Psychologist'),
        ('educator',     'Educator'),
    ]

    email      = models.EmailField(unique=True)
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='parent')
    avatar_url = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone      = models.CharField(max_length=20, blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username', 'role']

    def __str__(self):
        return f'{self.get_full_name()} ({self.role})'

    @property
    def name(self):
        return self.get_full_name() or self.username


class PasswordResetCode(models.Model):
    """One-time 6-digit OTP code for password reset via email."""
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_codes')
    code       = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used       = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.pk:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at

    @classmethod
    def generate_code(cls):
        return ''.join(random.choices(string.digits, k=6))

    def __str__(self):
        return f'{self.user.email} – {self.code} (used={self.used})'