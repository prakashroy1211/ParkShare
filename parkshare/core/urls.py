from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings  # ✅ Import settings
from django.conf.urls.static import static 
from . import views
from .views import view_reservations, user_profile 
from core.views import add_parking_space, edit_parking_space, delete_parking_space, owner_dashboard, parking_space_list
from django.conf.urls.static import static

app_name = 'core'  # Ensure this matches reverse('core:user_dashboard')

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='user_login'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),  # Correct URL pattern for user dashboard
    path('register/', views.register, name='register'),
    path('reservations/', view_reservations, name='view_reservations'),
    
    path('parking-space-list/', parking_space_list, name='parking_space_list'),
    path('logout/', views.user_logout, name='logout'),  # Logout route
    path('add-parking-space/', add_parking_space, name='add_parking_space'),
    
    path('edit-parking-space/<int:id>/', edit_parking_space, name='edit_parking_space'),  # ✅ Change `pk` to `id`
    path('delete-parking-space/<int:id>/', delete_parking_space, name='delete_parking_space'),
    path('profile/', user_profile, name='profile'),
    path('owner-dashboard/', owner_dashboard, name='owner_dashboard'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
