import base64
import email
import imaplib
import quopri
from email.header import decode_header
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup
from django.core.files.base import ContentFile

from .models import Email, EmailAttachment


class EmailHandler:
    def __init__(self, user, email, email_password, existing_email_ids):
        self.user = user
        self.email = email
        self.email_password = email_password
        self.existing_email_ids = existing_email_ids

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
            if encoding is None:
                return part.get_payload()
            return quopri.decodestring(part.get_payload()).decode(encoding)
        else:
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
                        letter_text.replace("<", "")
                        .replace(">", "")
                        .replace("\xa0", " ")
                        .replace("\x00", "")
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
                return (
                    letter_text.replace("<", "")
                    .replace(">", "")
                    .replace("\xa0", " ")
                    .replace("\x00", "")
                )

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

    @property
    def domain(self):
        return self.email.split("@")[1]

    @property
    def imap_server(self):
        match self.domain:
            case "gmail.com":
                return "imap.gmail.com"
            case "mail.ru":
                return "imap.mail.ru"
            case "yandex.ru":
                return "imap.yandex.ru"
            case _:
                raise Exception("Domain not supported")

    def fetch_emails(self):
        imap = imaplib.IMAP4_SSL(self.imap_server)
        imap.login(self.email, self.email_password)
        imap.select("INBOX")

        result, data = imap.uid("search", None, "ALL")
        email_ids = data[0].split()

        existing_ids = list(map(int, self.existing_email_ids))

        emails_to_upload = [index for index in email_ids if int(index) not in existing_ids]

        for email_id in emails_to_upload:
            result, msg_data = imap.uid("fetch", email_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = msg.get("Subject", None)
            if subject:
                subject, encoding = decode_header(subject)[0]
                if encoding in [
                    "unknown-8bit",
                ]:
                    encoding = "utf-8"
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")

            body = self.get_letter_text(msg)
            files = self.get_attachments(msg)

            date = msg["Date"]
            epoch_time = None
            if date:
                epoch_time = int(parsedate_to_datetime(msg["Date"]).timestamp())

            email_data = {
                "email_uid": int(email_id),
                "topic": subject if subject else "n/a",
                "sending_date": epoch_time,
                "receipt_date": epoch_time,
                "content": body,
                "files": files,
            }
            self.save_email(email_data)

    def save_email(self, email_data):
        email_instance = Email.objects.create(
            email_uid=email_data["email_uid"],
            user=self.user,
            topic=email_data["topic"],
            sending_date=email_data["sending_date"],
            receipt_date=email_data["receipt_date"],
            content=email_data["content"],
        )

        for filename, file_content in email_data["files"]:
            attachment = EmailAttachment(email=email_instance, name=filename)
            attachment.file.save(filename, ContentFile(file_content))
            attachment.save()
