# core/views.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CustomUserSerializer
from django.contrib.auth import authenticate, login, logout
import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import CustomUser, ParkingLot
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.middleware.csrf import get_token
from django.utils import timezone
from django.contrib.sessions.backends.db import SessionStore

logger = logging.getLogger(__name__)

# Custom middleware to handle tab-specific session cookies
def tab_specific_session_middleware(get_response):
    def middleware(request):
        # Get the tab_id from the query parameter
        tab_id = request.GET.get('tab_id', 'default')
        session_cookie_name = f"sessionid_{tab_id}"

        # Log the initial state
        logger.info(f"Middleware processing for tab {tab_id}, cookies: {request.COOKIES}")

        # Use the tab-specific session cookie if it exists
        if session_cookie_name in request.COOKIES:
            session_key = request.COOKIES[session_cookie_name]
            logger.info(f"Loading session for tab {tab_id} with session_key: {session_key}")
            request.session = SessionStore(session_key=session_key)
        else:
            logger.info(f"No session cookie found for tab {tab_id}, creating new session")
            request.session = SessionStore()
            request.session.create()
            session_key = request.session.session_key
            logger.info(f"Created new session for tab {tab_id}, session_key: {session_key}")

        # Process the request
        response = get_response(request)

        # Save the session and set the custom session cookie
        try:
            if hasattr(request, 'session') and request.session.session_key:
                response.set_cookie(
                    session_cookie_name,
                    request.session.session_key,
                    httponly=True,
                    samesite='Lax',
                    expires=timezone.now() + timezone.timedelta(days=1)
                )
                logger.info(f"Set cookie {session_cookie_name} with session_key: {request.session.session_key}")
        except Exception as e:
            logger.error(f"Error setting session cookie for tab {tab_id}: {str(e)}", exc_info=True)

        return response
    return middleware

def health_check(request):
    return JsonResponse({"status": "ok"})

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        roles = request.data.get("role", [])

        if isinstance(roles, str):
            roles = [roles]
        roles = list(set(roles))

        user = CustomUser.objects.filter(username=username).first()

        if user:
            if not user.check_password(password):
                return Response(
                    {"error": "Incorrect password. You already have an account registered with another role."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            existing_roles = user.role if isinstance(user.role, list) else []
            if any(role in existing_roles for role in roles):
                return Response(
                    {"error": "You already have this role assigned to your account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            new_roles = [role for role in roles if role not in existing_roles]
            user.role = existing_roles + new_roles
            user.save()

            return Response(
                {"message": "Roles updated successfully!", "roles": user.role},
                status=status.HTTP_200_OK,
            )

        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "User created successfully!", "roles": user.role},
                status=status.HTTP_201_CREATED,
            )

        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        logger.info("Received login data: %s", request.data)
        username = request.data.get('username')
        password = request.data.get('password')

        try:
            user = authenticate(request, username=username, password=password)
            logger.info(f"Authentication result for {username}: {user}")

            if user is not None and user.is_authenticated:
                login(request, user)
                tab_id = request.GET.get('tab_id', 'default')
                request.session['user_id'] = user.id
                request.session.save()

                roles = user.role if isinstance(user.role, list) else [user.role]
                valid_roles = [role for role in roles if role in ['driver', 'owner']]

                logger.info(f"Login successful for {username}, roles: {valid_roles}, session_key: {request.session.session_key}")
                return Response({
                    "message": "Login successful!",
                    "roles": valid_roles,
                    "csrf_token": get_token(request),
                    "tab_id": tab_id
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"Invalid credentials for username: {username}")
                return Response({
                    "errors": {"username": ["Invalid username or password."]}
                }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Error during login for {username}: {str(e)}", exc_info=True)
            return Response({
                "errors": {"server": ["An internal server error occurred. Please try again."]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetCsrfTokenView(APIView):
    def get(self, request):
        return Response({
            "csrf_token": get_token(request)
        })

class AddParkingLotAPIView(APIView):
    def post(self, request):
        logger.info(f"Request user: {request.user}, Authenticated: {request.user.is_authenticated}, Roles: {request.user.role}")
        if not request.user.is_authenticated:
            logger.error("User not authenticated")
            return Response({"status": "error", "message": "You must be logged in to add a parking lot."}, status=status.HTTP_401_UNAUTHORIZED)

        tab_id = request.GET.get('tab_id', 'default')
        role_key = f"current_role_{tab_id}"
        user_roles = request.session.get(role_key, request.user.role if isinstance(request.user.role, list) else [request.user.role])
        logger.info(f"User roles from session (tab {tab_id}): {user_roles}")
        if "owner" not in user_roles:
            logger.error("User does not have owner role")
            return Response({"status": "error", "message": "Only users with the 'owner' role can add parking lots."}, status=status.HTTP_403_FORBIDDEN)

        try:
            lot_name = request.POST.get("lot_name")
            vehicle_type = request.POST.get("vehicle_type")
            vehicle_capacity = request.POST.get("vehicle_capacity")
            price_per_hour = request.POST.get("price_per_hour")
            location = request.POST.get("location")
            picture = request.FILES.get("picture")

            if not all([lot_name, vehicle_type, vehicle_capacity, price_per_hour, location]):
                return Response({"status": "error", "message": "All fields are required except picture."}, status=status.HTTP_400_BAD_REQUEST)

            parking_lot = ParkingLot(
                owner=request.user,
                lot_name=lot_name,
                vehicle_type=vehicle_type,
                vehicle_capacity=int(vehicle_capacity),
                price_per_hour=float(price_per_hour),
                location=location,
                picture=picture
            )
            parking_lot.save()

            return Response({
                "status": "success",
                "parking_lot": {
                    "id": parking_lot.id,
                    "lot_name": parking_lot.lot_name,
                    "vehicle_type": parking_lot.vehicle_type,
                    "vehicle_capacity": parking_lot.vehicle_capacity,
                    "price_per_hour": float(parking_lot.price_per_hour),
                    "location": parking_lot.location,
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error adding parking lot: {str(e)}")
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ListParkingLotsAPIView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"status": "error", "message": "You must be logged in to view parking lots."}, status=status.HTTP_401_UNAUTHORIZED)

        tab_id = request.GET.get('tab_id', 'default')
        role_key = f"current_role_{tab_id}"
        user_roles = request.session.get(role_key, request.user.role if isinstance(request.user.role, list) else [request.user.role])
        if "owner" not in user_roles:
            return Response({"status": "error", "message": "Only users with the 'owner' role can view parking lots."}, status=status.HTTP_403_FORBIDDEN)

        try:
            parking_lots = ParkingLot.objects.filter(owner=request.user)
            parking_lot_data = [
                {
                    "id": pl.id,
                    "lot_name": pl.lot_name,
                    "vehicle_type": pl.vehicle_type,
                    "vehicle_capacity": pl.vehicle_capacity,
                    "price_per_hour": float(pl.price_per_hour),
                    "location": pl.location,
                }
                for pl in parking_lots
            ]
            return Response({
                "status": "success",
                "parking_lots": parking_lot_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching parking lots: {str(e)}")
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ListAllParkingLotsAPIView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"status": "error", "message": "You must be logged in to view parking lots."}, status=status.HTTP_401_UNAUTHORIZED)

        tab_id = request.GET.get('tab_id', 'default')
        role_key = f"current_role_{tab_id}"
        user_roles = request.session.get(role_key, request.user.role if isinstance(request.user.role, list) else [request.user.role])
        if "driver" not in user_roles:
            return Response({"status": "error", "message": "Only users with the 'driver' role can view all parking lots."}, status=status.HTTP_403_FORBIDDEN)

        try:
            parking_lots = ParkingLot.objects.all()
            parking_lot_data = [
                {
                    "id": pl.id,
                    "lot_name": pl.lot_name,
                    "vehicle_type": pl.vehicle_type,
                    "vehicle_capacity": pl.vehicle_capacity,
                    "price_per_hour": float(pl.price_per_hour),
                    "location": pl.location,
                }
                for pl in parking_lots
            ]
            return Response({
                "status": "success",
                "parking_lots": parking_lot_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching all parking lots: {str(e)}")
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ReserveParkingLotAPIView(APIView):
    def post(self, request):
        logger.info(f"Reserve request received: {request.data}, user: {request.user}")
        if not request.user.is_authenticated:
            logger.error("User not authenticated")
            return Response({"status": "error", "message": "You must be logged in to reserve a parking lot."}, status=status.HTTP_401_UNAUTHORIZED)

        tab_id = request.GET.get('tab_id', 'default')
        role_key = f"current_role_{tab_id}"
        user_roles = request.session.get(role_key, request.user.role if isinstance(request.user.role, list) else [request.user.role])
        logger.info(f"User roles for tab {tab_id}: {user_roles}")
        if "driver" not in user_roles:
            logger.error("User does not have driver role")
            return Response({"status": "error", "message": "Only users with the 'driver' role can reserve parking lots."}, status=status.HTTP_403_FORBIDDEN)

        try:
            parking_lot_id = request.data.get("parking_lot_id")
            if not parking_lot_id:
                logger.error("Parking lot ID not provided")
                return Response({"status": "error", "message": "Parking lot ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            parking_lot = ParkingLot.objects.get(id=parking_lot_id)
            logger.info(f"Found parking lot: {parking_lot.lot_name}, capacity: {parking_lot.vehicle_capacity}")
            if parking_lot.vehicle_capacity <= 0:
                logger.error("No available slots")
                return Response({"status": "error", "message": "No available slots in this parking lot."}, status=status.HTTP_400_BAD_REQUEST)

            parking_lot.vehicle_capacity -= 1
            parking_lot.save()
            logger.info(f"Reserved parking lot: {parking_lot.lot_name}, new capacity: {parking_lot.vehicle_capacity}")

            return Response({
                "status": "success",
                "message": f"Successfully reserved a slot in {parking_lot.lot_name}.",
                "updated_capacity": parking_lot.vehicle_capacity
            }, status=status.HTTP_200_OK)
        except ParkingLot.DoesNotExist:
            logger.error(f"Parking lot {parking_lot_id} not found")
            return Response({"status": "error", "message": "Parking lot not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error reserving parking lot: {str(e)}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EditParkingLotAPIView(APIView):
    def post(self, request):
        logger.info(f"Edit request received: {request.data}, user: {request.user}")
        if not request.user.is_authenticated:
            logger.error("User not authenticated")
            return Response({"status": "error", "message": "You must be logged in to edit a parking lot."}, status=status.HTTP_401_UNAUTHORIZED)

        tab_id = request.GET.get('tab_id', 'default')
        role_key = f"current_role_{tab_id}"
        user_roles = request.session.get(role_key, request.user.role if isinstance(request.user.role, list) else [request.user.role])
        logger.info(f"User roles for tab {tab_id}: {user_roles}")
        if "owner" not in user_roles:
            logger.error("User does not have owner role")
            return Response({"status": "error", "message": "Only users with the 'owner' role can edit parking lots."}, status=status.HTTP_403_FORBIDDEN)

        parking_lot_id = request.data.get("parking_lot_id")
        if not parking_lot_id:
            logger.error("Parking lot ID not provided")
            return Response({"status": "error", "message": "Parking lot ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            parking_lot = ParkingLot.objects.get(id=parking_lot_id, owner=request.user)
            logger.info(f"Found parking lot: {parking_lot.lot_name}")

            lot_name = request.data.get("lot_name", parking_lot.lot_name)
            vehicle_type = request.data.get("vehicle_type", parking_lot.vehicle_type)
            vehicle_capacity = request.data.get("vehicle_capacity", parking_lot.vehicle_capacity)
            price_per_hour = request.data.get("price_per_hour", parking_lot.price_per_hour)
            location = request.data.get("location", parking_lot.location)
            picture = request.FILES.get("picture", parking_lot.picture)

            parking_lot.lot_name = lot_name
            parking_lot.vehicle_type = vehicle_type
            parking_lot.vehicle_capacity = int(vehicle_capacity)
            parking_lot.price_per_hour = float(price_per_hour)
            parking_lot.location = location
            if picture:
                parking_lot.picture = picture
            parking_lot.save()

            logger.info(f"Updated parking lot: {parking_lot.lot_name}")
            return Response({
                "status": "success",
                "message": f"Successfully updated parking lot {parking_lot.lot_name}.",
                "parking_lot": {
                    "id": parking_lot.id,
                    "lot_name": parking_lot.lot_name,
                    "vehicle_type": parking_lot.vehicle_type,
                    "vehicle_capacity": parking_lot.vehicle_capacity,
                    "price_per_hour": float(parking_lot.price_per_hour),
                    "location": parking_lot.location,
                }
            }, status=status.HTTP_200_OK)
        except ParkingLot.DoesNotExist:
            logger.error(f"Parking lot {parking_lot_id} not found or not owned by user")
            return Response({"status": "error", "message": "Parking lot not found or you do not own it."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error editing parking lot: {str(e)}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteParkingLotAPIView(APIView):
    def post(self, request):
        logger.info(f"Delete request received: {request.data}, user: {request.user}")
        if not request.user.is_authenticated:
            logger.error("User not authenticated")
            return Response({"status": "error", "message": "You must be logged in to delete a parking lot."}, status=status.HTTP_401_UNAUTHORIZED)

        tab_id = request.GET.get('tab_id', 'default')
        role_key = f"current_role_{tab_id}"
        user_roles = request.session.get(role_key, request.user.role if isinstance(request.user.role, list) else [request.user.role])
        logger.info(f"User roles for tab {tab_id}: {user_roles}")
        if "owner" not in user_roles:
            logger.error("User does not have owner role")
            return Response({"status": "error", "message": "Only users with the 'owner' role can delete parking lots."}, status=status.HTTP_403_FORBIDDEN)

        parking_lot_id = request.data.get("parking_lot_id")
        if not parking_lot_id:
            logger.error("Parking lot ID not provided")
            return Response({"status": "error", "message": "Parking lot ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            parking_lot = ParkingLot.objects.get(id=parking_lot_id, owner=request.user)
            logger.info(f"Found parking lot: {parking_lot.lot_name}")
            parking_lot_name = parking_lot.lot_name
            parking_lot.delete()
            logger.info(f"Deleted parking lot: {parking_lot_name}")
            return Response({
                "status": "success",
                "message": f"Successfully deleted parking lot {parking_lot_name}."
            }, status=status.HTTP_200_OK)
        except ParkingLot.DoesNotExist:
            logger.error(f"Parking lot {parking_lot_id} not found or not owned by user")
            return Response({"status": "error", "message": "Parking lot not found or you do not own it."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting parking lot: {str(e)}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def home_view(request):
    return render(request, 'core/home.html')

def signup_view(request):
    return render(request, 'core/signup.html')

def login_view(request):
    return render(request, 'core/login.html')

@require_POST
@csrf_protect
def logout_view(request):
    try:
        if request.user.is_authenticated:
            logger.info(f"Logging out user: {request.user.username}")
        else:
            logger.warning("User not authenticated during logout attempt")
        logout(request)
        tab_id = request.GET.get('tab_id', 'default')
        session_cookie_name = f"sessionid_{tab_id}"
        new_csrf_token = get_token(request)
        logger.info("Logout successful, new CSRF token generated.")
        response = JsonResponse({
            "message": "Logout successful",
            "csrf_token": new_csrf_token,
            "tab_id": tab_id
        })
        response.delete_cookie(session_cookie_name)
        return response
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}", exc_info=True)
        return JsonResponse({
            "message": f"Error during logout: {str(e)}"
        }, status=500)

@login_required
def driver_home_view(request):
    return render(request, 'core/user_dashboard.html')

@login_required
def owner_home_view(request):
    try:
        parking_lots = ParkingLot.objects.filter(owner=request.user)
        return render(request, 'core/owner_dashboard.html', {'parking_lots': parking_lots})
    except Exception as e:
        print(f"Error fetching parking lots: {str(e)}")
        return render(request, 'core/owner_dashboard.html', {'parking_lots': [], 'error': str(e)})

@login_required
def role_selection_view(request):
    return render(request, 'core/role_selection.html')

@login_required
def role_redirect_view(request):
    if request.method == "POST":
        selected_role = request.POST.get("role")
        print(f"Received role: {selected_role}")

        if selected_role:
            tab_id = request.GET.get('tab_id', 'default')
            role_key = f"current_role_{tab_id}"
            request.session[role_key] = [selected_role]
            logger.info(f"Set {role_key} to {selected_role} for session {request.session.session_key}")

        if selected_role == "Driver":
            return redirect("user_dashboard")
        elif selected_role == "Owner":
            return redirect("owner_dashboard")

    return render(request, "core/role_selection.html")