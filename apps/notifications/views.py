from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status
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


class UpdateNotificationView(APIView):
    def patch(self, request, pk):
        data = request.data or {}
        title = data.get('title')
        message = data.get('message')
        ntype = data.get('type')

        # Admin updates announcements sent earlier; allow updating for this recipient only
        try:
            n = Notification.objects.get(pk=pk, recipient=request.user)
        except Notification.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if title is not None:
            n.title = str(title)
        if message is not None:
            n.message = str(message)
        if ntype is not None:
            n.type = str(ntype)

        n.save()
        return Response(NotificationSerializer(n).data, status=status.HTTP_200_OK)


class SendNotificationView(APIView):

    def post(self, request):

        recipient_id = request.data.get('recipient_id')
        title = request.data.get('title', '')
        message = request.data.get('message', '')
        ntype = request.data.get('type', 'system')
        child_id = request.data.get('child_id')

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
            return Response(
                NotificationSerializer(created_notifications[0]).data,
                status=status.HTTP_201_CREATED,
            )


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
            # Persist under child profile so the psychologist can load it later from the report tab.
            if child_id is not None:
                try:
                    from apps.reports.models import PsychologistReport
                    from apps.children.models import Child

                    child_obj = Child.objects.get(pk=child_id)
                    psychologist_report, _ = PsychologistReport.objects.update_or_create(
                        child=child_obj,
                        defaults={
                            'created_by': request.user if request.user.is_authenticated else None,
                            'content': message,
                        },
                    )
                except Exception:
                    # Don't block sending notifications if persistence fails.
                    pass

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







        # Serializer expects a single instance; return the first created notification payload.
        return Response(NotificationSerializer(created_notifications[0]).data, status=201)


