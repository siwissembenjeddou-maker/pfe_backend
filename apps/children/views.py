from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Child
from .serializers import ChildSerializer
from apps.notifications.tasks import notify_psychologists_child_added


class ChildListCreateView(generics.ListCreateAPIView):
    serializer_class = ChildSerializer
    # All authenticated roles (parent, psychologist, admin, educator) may manage children.
    permission_classes = [IsAuthenticated]

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
        user = self.request.user
        if user.role not in ['parent', 'admin', 'psychologist']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Your role cannot create child profiles.")
        child = serializer.save(parent=user)
        # Notify psychologists that a new child was added
        notify_psychologists_child_added.delay(child.id)


class ChildDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChildSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'parent':
            return Child.objects.filter(parent=user)
        return Child.objects.all()

    def perform_destroy(self, instance):
        user = self.request.user
        if user.role not in ['admin', 'psychologist'] and instance.parent != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to delete this child.")
        instance.delete()