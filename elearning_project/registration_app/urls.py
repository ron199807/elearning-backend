from django.urls import path
from .views import RegisterView, LoginView, LogoutView, CustomLoginView, home, user_profile

urlpatterns = [
    path('', home, name='home'),  # Root URL
    path('register/', RegisterView.as_view(), name='register'),  # /api/register/
    path('login/', LoginView.as_view(), name='login'),           # /api/login/
    path('logout/', LogoutView.as_view(), name='logout'),        # /api/logout/
    path('accounts/login/', CustomLoginView.as_view(), name='custom-login'),  # /api/accounts/login/
    path('user/profile/', user_profile, name='user-profile'),  # /api/user/profile/
]