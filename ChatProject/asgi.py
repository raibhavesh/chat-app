"""
ASGI config for ChatProject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.layers import get_channel_layer  # To use the channel layer
from ChatApp import routing  # Ensure this is importing the correct routing
from channels_redis.core import RedisChannelLayer  # Import RedisChannelLayer if using Redis

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChatProject.settings')

# Set up the Channel Layer
channel_layer = RedisChannelLayer(
    # Your Redis configuration, you can also add specific settings here if needed
    hosts=[('127.0.0.1', 6379)],  # This is the default Redis setup, change as needed
)

# This line gets the standard Django ASGI application
django_asgi_app = get_asgi_application()

# This line sets up the ASGI application for both HTTP and WebSocket protocols
application = ProtocolTypeRouter({
    "http": django_asgi_app,  # Standard HTTP requests handled by Django
    "websocket": AuthMiddlewareStack(  # WebSocket connections are handled by Channels
        URLRouter(
            routing.websocket_urlpatterns  # Make sure `websocket_urlpatterns` is properly defined in `routing.py`
        )
    ),
    # Optionally, you can add other protocols like "mqtt", "custom" here.
})

# Make sure to initialize the channel layer if needed in other parts of your app
application.channel_layer = channel_layer
