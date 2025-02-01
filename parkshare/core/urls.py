from django.urls import path
from .views import RegisterView, LoginView, signup_view, login_view, home_view

urlpatterns = [
    # API Endpoints
    path('api/register/', RegisterView.as_view(), name='api-register'),  # API for registration
    path('api/login/', LoginView.as_view(), name='api-login'),          # API for login

    # Frontend Pages
    path('', home_view, name='home'),
    path('signup/', signup_view, name='signup'),                        # Signup page
    path('login/', login_view, name='login'),                           # Login page
]