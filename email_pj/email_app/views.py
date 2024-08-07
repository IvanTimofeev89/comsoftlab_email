from datetime import datetime

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .email_handler import EmailHandler
from .forms import CustomUserCreationForm
from .models import Email


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("mailbox")
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {"form": form})


@login_required(login_url="/login/")
def mailbox(request):
    email = request.user.email
    password = request.user.email_password

    existing_email_ids = Email.objects.filter(user=request.user).values_list("email_uid", flat=True)

    email_handler = EmailHandler(
        user=request.user,
        email=email,
        email_password=password,
        existing_email_ids=existing_email_ids,
    )

    email_handler.fetch_emails()
    user_emails = Email.objects.filter(user=request.user).order_by("-receipt_date")
    for email in user_emails:
        if email.sending_date:
            email.sending_date_iso = datetime.fromtimestamp(email.sending_date).isoformat()
        if email.receipt_date:
            email.receipt_date_iso = datetime.fromtimestamp(email.receipt_date).isoformat()

    return render(request, "email/mailbox.html", {"user_emails": user_emails})
