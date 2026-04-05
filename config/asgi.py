import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from config.routing import websocket_urlpatterns
from core.jwt_middleware import TokenAuthMiddlewareStack

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': TokenAuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
