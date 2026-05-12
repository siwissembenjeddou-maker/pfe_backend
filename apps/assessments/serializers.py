from rest_framework import serializers
from .models import Assessment


class AssessmentSerializer(serializers.ModelSerializer):
    child_name   = serializers.CharField(source='child.name', read_only=True)
    parent_id    = serializers.CharField(source='child.parent_id', read_only=True)
    parent_name  = serializers.CharField(source='child.parent.name', read_only=True)

    class Meta:
        model  = Assessment
        fields = [
            'id', 'child', 'child_name', 'parent_id', 'parent_name',
            'activity_type',
            'audio_transcription', 'autism_score', 'severity_level',
            'dimension_scores', 'ai_analysis', 'key_observations',
            'immediate_recommendations', 'status', 'psychologist_note',
            'corrected_score', 'created_at', 'reviewed_at',
        ]
        read_only_fields = [
            'autism_score', 'severity_level', 'dimension_scores',
            'ai_analysis', 'key_observations', 'immediate_recommendations',
            'status', 'reviewed_at',
        ]


class ReviewSerializer(serializers.Serializer):
    status          = serializers.ChoiceField(choices=['confirmed', 'corrected'])
    note            = serializers.CharField(required=False, allow_blank=True)
    corrected_score = serializers.FloatField(required=False, min_value=0, max_value=10)