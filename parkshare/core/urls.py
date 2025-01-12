from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.parking_space_list, name='parking_space_list'),
    path('add/', views.add_parking_space, name='add_parking_space'),
    path('book/<int:pk>/', views.book_parking_space, name='book_parking_space'),
]