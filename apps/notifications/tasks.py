from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def notify_psychologists(assessment_id: int):
    from apps.assessments.models import Assessment
    from apps.users.models import User
    from .models import Notification

    try:
        assessment    = Assessment.objects.select_related('child').get(pk=assessment_id)
        psychologists = User.objects.filter(role='psychologist', is_active=True)

        notifications = [
            Notification(
                recipient=psych,
                title='New Assessment Pending Review',
                message=(
                    f'A new assessment for {assessment.child.name} '
                    f'({assessment.activity_type}) has been submitted. '
                    f'AI Score: {assessment.autism_score:.1f}/10 '
                    f'({assessment.severity_level}). Please review.'
                ),
                type='assessment_result',
            )
            for psych in psychologists
        ]
        Notification.objects.bulk_create(notifications)
        logger.info(f'Notified {len(notifications)} psychologists for assessment {assessment_id}')
    except Exception as e:
        logger.error(f'notify_psychologists failed: {e}')


@shared_task
def notify_parent_of_review(assessment_id: int):
    from apps.assessments.models import Assessment
    from .models import Notification

    try:
        assessment = Assessment.objects.select_related('child__parent').get(pk=assessment_id)
        parent     = assessment.child.parent
        score      = assessment.corrected_score or assessment.autism_score

        Notification.objects.create(
            recipient=parent,
            title='Assessment Review Complete',
            message=(
                f'The assessment for {assessment.child.name} has been reviewed. '
                f'Final Score: {score:.1f}/10 ({assessment.severity_level}). '
                f'{"Note: " + assessment.psychologist_note if assessment.psychologist_note else ""}'
            ),
            type='review_complete',
        )
        logger.info(f'Notified parent {parent.id} of review for assessment {assessment_id}')
    except Exception as e:
        logger.error(f'notify_parent_of_review failed: {e}')