from django.urls import path
from .views import ChildReportView, SystemStatsView

urlpatterns = [
    path('child/<int:child_id>/', ChildReportView.as_view(), name='child-report'),
    path('stats/',                SystemStatsView.as_view(), name='system-stats'),
]