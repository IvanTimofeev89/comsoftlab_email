import imaplib
import email
from email.header import decode_header
from .models import Email, EmailAttachment
from datetime import datetime
from email.utils import parsedate_to_datetime
import base64
import quopri
from asgiref.sync import sync_to_async
import re
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile

class EmailHandler:
    def __init__(self, user, email, email_password, existing_email_ids):
        self.user = user
        self.email = email
        self.email_password = email_password
        self.existing_email_ids = existing_email_ids
    @property
    def domain(self):
        return self.email.split('@')[1]

    def fetch_emails(self):
        if self.domain == 'gmail.com':
            return self.fetch_gmail_emails()
        if self.domain == 'mail.ru':
            return self.fetch_mailru_emails()
        return []

    def get_letter_text_from_html(self, body):
        body = body.replace("<div><div>", "<div>").replace("</div></div>", "</div>")
        try:
            soup = BeautifulSoup(body, "html.parser")
            paragraphs = soup.find_all("div")
            text = ""
            for paragraph in paragraphs:
                text += paragraph.text + "\n"
            return text.replace("\xa0", " ")
        except Exception:
            return False

    def letter_type(self, part):
        if part["Content-Transfer-Encoding"] in (None, "7bit", "8bit", "binary"):
            return part.get_payload()
        elif part["Content-Transfer-Encoding"] == "base64":
            encoding = part.get_content_charset()
            return base64.b64decode(part.get_payload()).decode(encoding)
        elif part["Content-Transfer-Encoding"] == "quoted-printable":
            encoding = part.get_content_charset()
            return quopri.decodestring(part.get_payload()).decode(encoding)
        else:  # all possible types: quoted-printable, base64, 7bit, 8bit, and binary
            return part.get_payload()

    def get_letter_text(self, msg):
        if msg.is_multipart():
            for part in msg.walk():
                count = 0
                if part.get_content_maintype() == "text" and count == 0:
                    extract_part = self.letter_type(part)
                    if part.get_content_subtype() == "html":
                        letter_text = self.get_letter_text_from_html(extract_part)
                    else:
                        letter_text = extract_part.rstrip().lstrip()
                    count += 1
                    return (
                        letter_text.replace("<", "").replace(">", "").replace("\xa0", " ")
                    )
        else:
            count = 0
            if msg.get_content_maintype() == "text" and count == 0:
                extract_part = self.letter_type(msg)
                if msg.get_content_subtype() == "html":
                    letter_text = self.get_letter_text_from_html(extract_part)
                else:
                    letter_text = extract_part
                count += 1
                return letter_text.replace("<", "").replace(">", "").replace("\xa0", " ")

    def get_attachments(self, msg):
        attachments = []
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                filename = part.get_filename()
                if filename:
                    decoded_header = decode_header(filename)
                    filename, charset = decoded_header[0]
                    if isinstance(filename, bytes):
                        filename = filename.decode(charset)
                    file_content = part.get_payload(decode=True)
                    attachments.append((filename, file_content))
        return attachments

    def save_email(self, email_data):
        email_instance = Email.objects.create(
            binary_id=email_data['binary_id'],
            user=self.user,
            topic=email_data['topic'],
            sending_date=email_data['sending_date'],
            receipt_date=email_data['receipt_date'],
            content=email_data['content']
        )

        for filename, file_content in email_data['files']:
            attachment = EmailAttachment(
                email=email_instance,
                name=filename
            )
            attachment.file.save(filename, ContentFile(file_content))
            attachment.save()

    def fetch_mailru_emails(self):
        imap = imaplib.IMAP4_SSL("imap.mail.ru")
        imap.login(self.email, self.email_password)
        imap.select('INBOX')

        result, data = imap.uid('search', None, "ALL")
        email_ids = data[0].split()

        existing_ids = list(map(int, self.existing_email_ids))

        emails_to_upload = [index for index in email_ids if int(index) not in existing_ids]

        emails = []

        for email_id in emails_to_upload:
            result, msg_data = imap.uid('fetch', email_id, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            subject = msg.get("Subject", None)
            if subject:
                subject, encoding = decode_header(subject)[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")

            body = self.get_letter_text(msg)
            files = self.get_attachments(msg)
            epoch_time = int(parsedate_to_datetime(msg["Date"]).timestamp())

            email_data = {
                'binary_id': email_id,
                'topic': subject if subject else "n/a",
                'sending_date': epoch_time,
                'receipt_date': epoch_time,
                'content': body,
                'files': files
            }
            emails.append(email_data)
            self.save_email(email_data)


