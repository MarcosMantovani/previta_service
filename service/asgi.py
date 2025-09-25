from django.core.asgi import get_asgi_application

asgi_application = get_asgi_application()

import os

import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from authentication.middlewares import TokenAuthMiddlewareStack

from .consumers import AppApplicationDemultiplexer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service.settings")
django.setup()


application = ProtocolTypeRouter({
    "http": asgi_application,
    "websocket": TokenAuthMiddlewareStack(URLRouter(
        [
            re_path(r"^ws/$", AppApplicationDemultiplexer.as_asgi()),
        ]
    ))
})


