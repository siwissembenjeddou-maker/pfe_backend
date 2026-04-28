from django.urls import path
from .views import AttendanceListCreateView, AttendanceDetailView

urlpatterns = [
    path('',              AttendanceListCreateView.as_view(), name='attendance-list'),
    path('<int:pk>',      AttendanceDetailView.as_view(),     name='attendance-detail'),
]

