
import os

from django.core.asgi import get_asgi_application

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

# Initialize Django first.
django_asgi_app = get_asgi_application()

# Import WebSocket routes after Django initialization.
from notifications.routing import websocket_urlpatterns


application = ProtocolTypeRouter({

    # HTTP requests, including development static files.
    "http": ASGIStaticFilesHandler(
        django_asgi_app
    ),

    # Authenticated WebSocket connections.
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),

})
