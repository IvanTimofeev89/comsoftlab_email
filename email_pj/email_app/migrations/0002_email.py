# Generated by Django 5.0.7 on 2024-07-26 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(max_length=255)),
                ('sending_date', models.DateTimeField()),
                ('receipt_date', models.DateTimeField()),
                ('content', models.TextField()),
                ('files', models.FileField(upload_to='email_files')),
            ],
        ),
    ]