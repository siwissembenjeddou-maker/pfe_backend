from rest_framework import serializers
from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    child_name = serializers.CharField(source='child.name', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'child', 'child_name', 'date', 'status', 'recorded_by', 'notes']
        read_only_fields = ['recorded_by']

