from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import CustomUserCreationForm
from django.contrib.auth import login
from django.shortcuts import redirect, render

# Create your views here.
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('hello')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required(login_url='login')
def hello(request):
    return render(request, 'email/hello.html')