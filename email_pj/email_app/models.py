from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email_password = models.CharField(max_length=30)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions '
                   'granted to each of their groups.'),
        verbose_name=('groups'),
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
        help_text=('Specific permissions for this user.'),
        verbose_name=('user permissions'),
    )

class Email(models.Model):
    binary_id = models.BinaryField(blank=True, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='emails')
    topic = models.CharField(max_length=255, blank=True)
    sending_date = models.BigIntegerField(blank=True, null=True)
    receipt_date = models.BigIntegerField(blank=True, null=True, db_index=True)
    content = models.TextField()


class EmailAttachment(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='email_files', blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
