from rest_framework import serializers
from .models import Child


class ChildSerializer(serializers.ModelSerializer):
    age           = serializers.ReadOnlyField()
    parent_id     = serializers.PrimaryKeyRelatedField(source='parent', read_only=True)
    parent_name   = serializers.CharField(source='parent.name', read_only=True)
    profile_image = serializers.SerializerMethodField()
    assessments   = serializers.SerializerMethodField()

    class Meta:
        model  = Child
        fields = [
            'id', 'name', 'date_of_birth', 'age', 'gender',
            'parent_id', 'parent_name', 'profile_image', 'notes', 'assessments', 'created_at',
        ]

    def get_profile_image(self, obj):
        if obj.profile_image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.profile_image.url) if request else str(obj.profile_image.url)
        return None

    def get_assessments(self, obj):
        from apps.assessments.serializers import AssessmentSerializer
        return AssessmentSerializer(
            obj.assessments.all().order_by('-created_at'), many=True
        ).data