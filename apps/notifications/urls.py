from django.urls import path
from .views import NotificationListView, MarkReadView, SendNotificationView

urlpatterns = [
    path('',               NotificationListView.as_view(), name='notification-list'),
    path('send',           SendNotificationView.as_view(), name='notification-send'),
    path('<int:pk>/read',  MarkReadView.as_view(),         name='notification-read'),
]