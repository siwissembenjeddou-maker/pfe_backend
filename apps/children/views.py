from rest_framework import generics
from .models import Child
from .serializers import ChildSerializer


class ChildListCreateView(generics.ListCreateAPIView):
    serializer_class = ChildSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'parent':
            return Child.objects.filter(parent=user).prefetch_related('assessments')
        qs        = Child.objects.all().prefetch_related('assessments')
        parent_id = self.request.query_params.get('parent_id')
        if parent_id:
            qs = qs.filter(parent_id=parent_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(parent=self.request.user)


class ChildDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChildSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'parent':
            return Child.objects.filter(parent=user)
        return Child.objects.all()