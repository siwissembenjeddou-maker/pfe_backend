import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import apps.messaging.routing as messaging_routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autisense.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(messaging_routing.websocket_urlpatterns)
    ),
})