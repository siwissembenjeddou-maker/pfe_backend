from rest_framework import serializers
from .models import SystemLog


class SystemLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = SystemLog
        fields = ['id', 'event', 'user', 'user_name', 'metadata', 'timestamp']

