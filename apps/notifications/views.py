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
        try:
            recipient = User.objects.get(pk=recipient_id)
        except User.DoesNotExist:
            return Response({'error': 'Recipient not found'}, status=404)

        n = Notification.objects.create(
            recipient=recipient, title=title, message=message, type=ntype)
        return Response(NotificationSerializer(n).data)