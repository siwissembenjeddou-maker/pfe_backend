from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/',         admin.site.urls),
    path('auth/',          include('apps.users.urls')),
    path('children/',      include('apps.children.urls')),
    path('assessments/',   include('apps.assessments.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('messages/',      include('apps.messaging.urls')),
    path('schedules/',     include('apps.schedules.urls')),
    path('reports/',       include('apps.reports.urls')),
    path('users/',         include('apps.users.admin_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)