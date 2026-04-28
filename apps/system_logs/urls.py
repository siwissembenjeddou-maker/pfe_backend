from django.urls import path
from .views import SystemLogListView

urlpatterns = [
    path('', SystemLogListView.as_view(), name='system-log-list'),
]

