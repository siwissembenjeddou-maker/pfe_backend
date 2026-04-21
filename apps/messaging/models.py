from django.db import models
from apps.users.models import User


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        names = ', '.join(p.name for p in self.participants.all())
        return f'Conversation({names})'

    @classmethod
    def get_or_create_between(cls, user1, user2):
        convs = cls.objects.filter(participants=user1).filter(participants=user2).distinct()
        if convs.exists():
            return convs.first(), False
        conv = cls.objects.create()
        conv.participants.add(user1, user2)
        return conv, True


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content      = models.TextField()
    is_read      = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.name}: {self.content[:40]}'