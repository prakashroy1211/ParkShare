from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'  # Namespace your app

urlpatterns = [
    path('', views.home, name='home'),
     path('login/', views.user_login, name='user_login'),  # Ensure this matches the reverse call
    path('register/', views.register, name='register'),
    path('add-parking-space/', views.add_parking_space, name='add_parking_space'),
    path('parking-space-list/', views.parking_space_list, name='parking_space_list'),
    path('book-parking-space/<int:pk>/', views.book_parking_space, name='book_parking_space'),
    path('search/', views.search_parking_spaces, name='search'),
    path('role-selection/', views.role_selection, name='role_selection'),
    path('add-parking-slot/', views.add_parking_slot, name='add_parking_slot'),
]
