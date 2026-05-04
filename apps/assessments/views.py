import logging
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import IsPsychologist, IsParent
from apps.children.models import Child
from .models import Assessment
from .serializers import AssessmentSerializer, ReviewSerializer
from .rag_engine import RAGEngine, transcribe_audio

logger = logging.getLogger(__name__)


class AnalyzeAudioView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, IsParent]

    def post(self, request):
        child_id      = request.data.get('child_id')
        activity_type = request.data.get('activity_type', 'General')
        audio_file    = request.FILES.get('audio')

        if not all([child_id, audio_file]):
            return Response({'error': 'child_id and audio are required'}, status=400)

        try:
            child = Child.objects.get(id=child_id)
        except Child.DoesNotExist:
            return Response({'error': 'Child not found'}, status=404)

        assessment = Assessment(
            child=child, activity_type=activity_type,
            audio_file=audio_file, audio_transcription='',
            autism_score=0, severity_level='mild',
        )
        assessment.save()

        try:
            transcription = transcribe_audio(assessment.audio_file.path)
            assessment.audio_transcription = transcription

            engine = RAGEngine.get_instance()
            result = engine.analyze(
                transcription=transcription,
                child_info={'name': child.name, 'age': child.age, 'gender': child.gender},
                activity_type=activity_type,
            )

            assessment.autism_score              = result['autism_score']
            assessment.severity_level            = result['severity_level']
            assessment.dimension_scores          = result.get('dimension_scores', {})
            assessment.ai_analysis               = result.get('ai_analysis', '')
            assessment.key_observations          = result.get('key_observations', [])
            assessment.immediate_recommendations = result.get('immediate_recommendations', [])
            assessment.save()

            from apps.notifications.tasks import notify_psychologists
            notify_psychologists.delay(assessment.id)

            return Response({**AssessmentSerializer(assessment).data, **result})

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            assessment.delete()
            return Response({'error': str(e)}, status=500)


class AnalyzeTextView(APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        text          = request.data.get('text', '').strip()
        child_id      = request.data.get('child_id')
        activity_type = request.data.get('activity_type', 'General')

        if not text or not child_id:
            return Response({'error': 'text and child_id are required'}, status=400)

        try:
            child = Child.objects.get(id=child_id)
        except Child.DoesNotExist:
            return Response({'error': 'Child not found'}, status=404)

        try:
            engine = RAGEngine.get_instance()
            result = engine.analyze(
                transcription=text,
                child_info={'name': child.name, 'age': child.age, 'gender': child.gender},
                activity_type=activity_type,
            )
            assessment = Assessment.objects.create(
                child=child, activity_type=activity_type,
                audio_transcription=text,
                autism_score=result['autism_score'],
                severity_level=result['severity_level'],
                dimension_scores=result.get('dimension_scores', {}),
                ai_analysis=result.get('ai_analysis', ''),
                key_observations=result.get('key_observations', []),
                immediate_recommendations=result.get('immediate_recommendations', []),
            )
            from apps.notifications.tasks import notify_psychologists
            notify_psychologists.delay(assessment.id)
            return Response({**AssessmentSerializer(assessment).data, **result})

        except Exception as e:
            logger.error(f"Text analysis failed: {e}", exc_info=True)
            return Response({'error': str(e)}, status=500)


class AssessmentListView(generics.ListAPIView):
    serializer_class = AssessmentSerializer

    def get_queryset(self):
        qs   = Assessment.objects.select_related('child')
        user = self.request.user
        if user.role == 'parent':
            qs = qs.filter(child__parent=user)
        child_id = self.request.query_params.get('child_id')
        stat     = self.request.query_params.get('status')
        if child_id: qs = qs.filter(child_id=child_id)
        if stat:     qs = qs.filter(status=stat)
        return qs


class AssessmentDetailView(generics.RetrieveAPIView):
    queryset         = Assessment.objects.all()
    serializer_class = AssessmentSerializer


class ReviewAssessmentView(APIView):
    permission_classes = [IsAuthenticated, IsPsychologist]

    def patch(self, request, pk):
        try:
            assessment = Assessment.objects.get(pk=pk)
        except Assessment.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        serializer = ReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        assessment.status            = data['status']
        assessment.psychologist_note = data.get('note', '')
        assessment.corrected_score   = data.get('corrected_score')
        assessment.reviewed_by       = request.user
        assessment.reviewed_at       = timezone.now()
        assessment.save()

        from apps.notifications.tasks import notify_parent_of_review
        notify_parent_of_review.delay(assessment.id)

        return Response(AssessmentSerializer(assessment).data)