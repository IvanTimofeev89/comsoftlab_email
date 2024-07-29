import json

from channels.generic.websocket import WebsocketConsumer

from .email_handler import EmailHandler


class MailboxConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            self.close()
        else:
            self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        email_handler = EmailHandler(self.user, self.user.email, self.user.email_password)
        emails = email_handler.fetch_emails()
        for email_data in emails:
            self.send(text_data=json.dumps(email_data))
