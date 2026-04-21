from django.contrib.auth.models import AbstractUser
from django.db import models


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