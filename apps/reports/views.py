from rest_framework.views import APIView
from rest_framework.response import Response
from apps.children.models import Child
from apps.assessments.models import Assessment
from apps.users.models import User


class ChildReportView(APIView):
    def get(self, request, child_id):
        try:
            child = Child.objects.prefetch_related('assessments').get(pk=child_id)
        except Child.DoesNotExist:
            return Response({'error': 'Child not found'}, status=404)

        assessments = child.assessments.order_by('created_at')
        if not assessments.exists():
            return Response({
                'child_id': child.id, 'child_name': child.name,
                'total_assessments': 0, 'trend': [],
                'current_score': None, 'severity_breakdown': {},
                'psychologist_report': None,
            })

        trend = [
            {
                'date':     a.created_at.strftime('%Y-%m-%d'),
                'score':    a.effective_score,
                'activity': a.activity_type,
                'status':   a.status,
            }
            for a in assessments
        ]

        severity_breakdown = {}
        for a in assessments:
            severity_breakdown[a.severity_level] = severity_breakdown.get(a.severity_level, 0) + 1

        latest = assessments.last()

        # Load latest stored psychologist report (if any)
        psychologist_report = None
        try:
            from apps.reports.models import PsychologistReport
            psychologist_report_obj = (
                PsychologistReport.objects.filter(child=child).select_related('created_by').first()
            )
            psychologist_report = psychologist_report_obj.content if psychologist_report_obj else None
        except Exception:
            psychologist_report = None

        from apps.assessments.rag_engine import RAGEngine
        engine = RAGEngine.get_instance()
        ai_report = engine.generate_child_report(child, list(assessments))

        return Response({
            'child_id':          child.id,
            'child_name':        child.name,
            'child_age':         child.age,
            'total_assessments': assessments.count(),
            'current_score':     latest.effective_score,
            'current_severity':  latest.severity_level,
            'trend':             trend,
            'severity_breakdown':severity_breakdown,
            'average_score':     sum(a.effective_score for a in assessments) / assessments.count(),
            'dimension_averages':_avg_dimensions(assessments),
            'ai_report':         ai_report,
            'psychologist_report': psychologist_report,
        })


def _avg_dimensions(assessments):
    totals, counts = {}, {}
    for a in assessments:
        for k, v in a.dimension_scores.items():
            totals[k] = totals.get(k, 0) + v
            counts[k] = counts.get(k, 0) + 1
    return {k: round(totals[k] / counts[k], 2) for k in totals}


class SystemStatsView(APIView):
    def get(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Forbidden'}, status=403)
        assessments = Assessment.objects.all()
        return Response({
            'total_children':      Child.objects.count(),
            'total_assessments':   assessments.count(),
            'pending_reviews':     assessments.filter(status='pending').count(),
            'total_parents':       User.objects.filter(role='parent').count(),
            'total_psychologists': User.objects.filter(role='psychologist').count(),
            'total_educators':     User.objects.filter(role='educator').count(),
            'severity_breakdown': {
                'mild':     assessments.filter(severity_level='mild').count(),
                'moderate': assessments.filter(severity_level='moderate').count(),
                'severe':   assessments.filter(severity_level='severe').count(),
            },
        })