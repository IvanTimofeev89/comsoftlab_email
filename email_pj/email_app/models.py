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
    topic = models.CharField(max_length=255)
    sending_date = models.DateTimeField()
    receipt_date = models.DateTimeField()
    content = models.TextField()
    files = models.FileField(upload_to='email_files')