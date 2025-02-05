# registration_app/urls.py
from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    CustomLoginView,
    home,
)

urlpatterns = [
    path('', home, name='home'),  # Root URL
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('accounts/login/', CustomLoginView.as_view(), name='custom-login'),  # For Django's built-in login
]