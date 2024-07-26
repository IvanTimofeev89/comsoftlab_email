from django.urls import path, include
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView
from email_pj import settings
from . import views


urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    path('register/', views.register, name='register'),
    path('hello/', views.hello, name='hello'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)