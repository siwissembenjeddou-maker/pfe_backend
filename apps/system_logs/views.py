from rest_framework import generics
from apps.core.permissions import IsAdmin
from .models import SystemLog
from .serializers import SystemLogSerializer


class SystemLogListView(generics.ListAPIView):
    serializer_class = SystemLogSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = SystemLog.objects.select_related('user')
        event = self.request.query_params.get('event')
        if event:
            qs = qs.filter(event__icontains=event)
        return qs

