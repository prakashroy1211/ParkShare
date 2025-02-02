from django.urls import path
from .import views

urlpatterns = [
    # API Endpoints
    path('api/register/', views.RegisterView.as_view(), name='api-register'),  # API for registration
    path('api/login/', views.LoginView.as_view(), name='api-login'),          # API for login

    # Frontend Pages
    path('', views.home_view, name='home'),
    path('signup/', views.signup_view, name='signup'),                        # Signup page
    path('login/', views.login_view, name='login'),                           # Login page
    path('role_selection/', views.role_selection_view, name='role_selection'),
    path('book_parking_space', views.driver_home_view, name='book_parking_space'),
    path('add_parking_space/', views.owner_home_view, name='add_parking_space'),
    path('role-redirect/', views.role_redirect_view, name='role-redirect'),
]