from rest_framework import generics
from .models import ActivitySchedule
from .serializers import ActivityScheduleSerializer


class ScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = ActivityScheduleSerializer

    def get_queryset(self):
        qs   = ActivitySchedule.objects.all()
        date = self.request.query_params.get('date')
        if date:
            qs = qs.filter(date=date)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset         = ActivitySchedule.objects.all()
    serializer_class = ActivityScheduleSerializer