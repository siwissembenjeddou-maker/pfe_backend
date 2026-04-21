from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.name', read_only=True)

    class Meta:
        model  = Message
        fields = ['id', 'conversation', 'sender', 'sender_name', 'content', 'is_read', 'created_at']
        read_only_fields = ['sender', 'conversation']


class ConversationSerializer(serializers.ModelSerializer):
    last_message    = serializers.SerializerMethodField()
    unread_count    = serializers.SerializerMethodField()
    other_user_name = serializers.SerializerMethodField()

    class Meta:
        model  = Conversation
        fields = ['id', 'participants', 'other_user_name', 'last_message', 'unread_count', 'updated_at']

    def get_last_message(self, obj):
        msg = obj.messages.last()
        return MessageSerializer(msg).data if msg else None

    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()

    def get_other_user_name(self, obj):
        user  = self.context['request'].user
        other = obj.participants.exclude(id=user.id).first()
        return other.name if other else ''