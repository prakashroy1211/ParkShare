# core/urls.py
from django.urls import path
from . import views
from django.http import JsonResponse

urlpatterns = [
    path('admin/health/', views.health_check, name='health_check'),
    
    # API Endpoints
    path('api/register/', views.RegisterView.as_view(), name='api-register'),  # API for registration
    path('api/login/', views.LoginView.as_view(), name='api-login'),          # API for login
    path('api/add-parking-lot/', views.AddParkingLotAPIView.as_view(), name='add_parking_lot_api'),  # API for adding parking lots
    path('api/get-csrf-token/', views.GetCsrfTokenView.as_view(), name='get_csrf_token'),
    path('api/parking-lots/', views.ListParkingLotsAPIView.as_view(), name='list_parking_lots'),
    path('api/list-all-parking-lots/', views.ListAllParkingLotsAPIView.as_view(), name='list_all_parking_lots'),
    path('api/reserve-parking-lot/', views.ReserveParkingLotAPIView.as_view(), name='reserve_parking_lot'),
    path('api/user-reservations/', views.UserReservationsAPIView.as_view(), name='user_reservations'),
    path('api/owner-reservations/', views.OwnerReservationsAPIView.as_view(), name='owner_reservations_api'),
    path('api/edit-parking-lot/', views.EditParkingLotAPIView.as_view(), name='edit_parking_lot_api'),
    path('api/delete-parking-lot/', views.DeleteParkingLotAPIView.as_view(), name='delete_parking_lot_api'),
    
    # Frontend Pages
    path('', views.home_view, name='home'),
    path('signup/', views.signup_view, name='signup'),                        # Signup page
    path('login/', views.login_view, name='login'),                          # Login page
    path('logout/', views.logout_view, name='logout'),
    path('role_selection/', views.role_selection_view, name='role_selection'),
    path('user_dashboard/', views.driver_home_view, name='user_dashboard'),
    path('owner_dashboard/', views.owner_home_view, name='owner_dashboard'),
    path('role-redirect/', views.role_redirect_view, name='role-redirect'),
    path('view-reservations/', views.view_reservations, name='view_reservations'),
    path('owner_reservations/', views.owner_reservations_view, name='owner_reservations'),
]