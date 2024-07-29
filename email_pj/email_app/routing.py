from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path("ws/mailbox/", consumers.MailboxConsumer.as_asgi()),
]
