from rest_framework import serializers
from .models import ActivitySchedule


class ActivityScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model        = ActivitySchedule
        fields       = '__all__'
        read_only_fields = ['created_by']