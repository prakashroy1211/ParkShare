from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from core.views import add_parking_space, parking_space_list
from .views import add_parking_space, edit_parking_space, delete_parking_space, owner_dashboard

app_name = 'core'  # Ensure this matches reverse('core:user_dashboard')

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='user_login'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),  # Correct URL pattern for user dashboard
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('view_reservations/', views.view_reservations, name='view_reservations'),
    path('parking-space-list/', views.parking_space_list, name='parking_space_list'),
    path('logout/', views.user_logout, name='logout'),  # Logout route
    path('add-parking-space/', views.add_parking_space, name='add_parking_space'),
    path('edit-parking-space/<int:id>/', views.edit_parking_space, name='edit_parking_space'),
        path('delete-parking-space/<int:pk>/', views.delete_parking_space, name='delete_parking_space'),
    path('owner-dashboard/', owner_dashboard, name='owner_dashboard'),
]
