from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from apps.users.models import User
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class MarkReadView(APIView):
    def patch(self, request, pk):
        try:
            n = Notification.objects.get(pk=pk, recipient=request.user)
            n.is_read = True
            n.save()
            return Response({'success': True})
        except Notification.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)


class SendNotificationView(APIView):
    def post(self, request):
        recipient_id = request.data.get('recipient_id')
        title        = request.data.get('title', '')
        message      = request.data.get('message', '')
        ntype        = request.data.get('type', 'system')

        # Broadcast announcement support
        if recipient_id == 'all' or recipient_id == 'broadcast' or ntype == 'announcement':
            active_users = User.objects.filter(is_active=True)
            if not active_users.exists():
                return Response({'error': 'No active users found'}, status=404)

            created_notifications = Notification.objects.bulk_create([
                Notification(
                    recipient=user,
                    title=title,
                    message=message,
                    type=ntype,
                )
                for user in active_users
            ])
            return Response(NotificationSerializer(created_notifications[0]).data, status=201)

        # Support both integer pk and UUID string
        try:
            recipient = User.objects.get(pk=recipient_id)
        except (User.DoesNotExist, ValueError):
            return Response({'error': 'Recipient not found'}, status=404)

        # Always notify the explicitly provided recipient
        created_notifications = [
            Notification.objects.create(
                recipient=recipient,
                title=title,
                message=message,
                type=ntype,
            )
        ]

        # UX requirement: for psychologist reports, notify psychologists too.
        # Frontend sends type='psychologist_report' from sendChildReport(...).
        if ntype == 'psychologist_report':
            # Add to the RAG database so the engine learns from psychologist's verified/edited reports
            try:
                import logging
                logger = logging.getLogger(__name__)
                from apps.assessments.rag_engine import RAGEngine
                engine = RAGEngine.get_instance()
                engine.add_custom_data([message])
                logger.info("Successfully added psychologist report to RAG database.")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to add report to RAG database: {e}")

            psychologists = User.objects.filter(role='psychologist', is_active=True)
            created_notifications.extend(
                Notification.objects.bulk_create([
                    Notification(
                        recipient=psych,
                        title=title,
                        message=message,
                        type=ntype,
                    )
                    for psych in psychologists
                ])
            )

        # Serializer expects a single instance; return the first created notification payload.
        return Response(NotificationSerializer(created_notifications[0]).data, status=201)

