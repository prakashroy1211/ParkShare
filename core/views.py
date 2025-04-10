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
from .models import CustomUser, ParkingLot, Reservation
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.middleware.csrf import get_token
from django.utils import timezone
from django.contrib.sessions.backends.db import SessionStore
from django.db.models import Count
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

logger = logging.getLogger(__name__)

def tab_specific_session_middleware(get_response):
    def middleware(request):
        tab_id = request.GET.get('tab_id', 'default')
        session_cookie_name = f"sessionid_{tab_id}"
        csrf_cookie_name = f"csrftoken_{tab_id}"

        if session_cookie_name in request.COOKIES:
            session_key = request.COOKIES[session_cookie_name]
            request.session = SessionStore(session_key=session_key)
            logger.info(f"Loaded session for tab {tab_id}: {session_key}")
        else:
            request.session = SessionStore()
            request.session.create()
            logger.info(f"Created session for tab {tab_id}: {request.session.session_key}")

        response = get_response(request)

        if hasattr(request, 'session') and request.session.session_key:
            response.set_cookie(
                session_cookie_name,
                request.session.session_key,
                httponly=True,
                samesite='Lax',
                expires=timezone.now() + timezone.timedelta(days=1)
            )
            csrf_token = get_token(request)
            if len(csrf_token) != 64:
                logger.error(f"Generated CSRF token length invalid: {len(csrf_token)}, Token: {csrf_token}")
            response.set_cookie(
                csrf_cookie_name,
                csrf_token,
                httponly=False,
                samesite='Lax',
                expires=timezone.now() + timezone.timedelta(days=1)
            )
            logger.info(f"Set cookies: {session_cookie_name}={request.session.session_key}, {csrf_cookie_name}={csrf_token}, Length: {len(csrf_token)}")
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
                valid_roles = [role for role in roles if role in ['driver', 'owner', 'admin']]
                
                # Set role in session
                role_key = f"current_role_{tab_id}"
                if user.is_superuser:
                    request.session[role_key] = ['admin']  # Admin takes precedence
                else:
                    request.session[role_key] = valid_roles

                logger.info(f"Login successful for {username}, roles: {valid_roles}, session_key: {request.session.session_key}")
                redirect_url = None
                if user.is_superuser:
                    redirect_url = f"/admin_dashboard/?tab_id={tab_id}"
                elif len(valid_roles) == 1:
                    if valid_roles[0] == 'driver':
                        redirect_url = f"/user_dashboard/?tab_id={tab_id}"
                    elif valid_roles[0] == 'owner':
                        redirect_url = f"/owner_dashboard/?tab_id={tab_id}"
                
                return Response({
                    "message": "Login successful!",
                    "roles": valid_roles,
                    "csrf_token": get_token(request),
                    "tab_id": tab_id,
                    "redirect_url": redirect_url
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
            return Response({"status": "error", "message": "You must be logged in to add a parking lot."}, status=status.HTTP_401_UNAUTHORIZED)

        tab_id = request.GET.get('tab_id', 'default')
        role_key = f"current_role_{tab_id}"
        user_roles = request.session.get(role_key, request.user.role if isinstance(request.user.role, list) else [request.user.role])
        if "owner" not in user_roles:
            return Response({"status": "error", "message": "Only users with the 'owner' role can add parking lots."}, status=status.HTTP_403_FORBIDDEN)

        try:
            lot_name = request.POST.get("lot_name")
            vehicle_type = request.POST.get("vehicle_type")
            vehicle_capacity = request.POST.get("vehicle_capacity")
            price_per_hour = request.POST.get("price_per_hour")
            location_name = request.POST.get("location_name")
            latitude = request.POST.get("latitude")
            longitude = request.POST.get("longitude")
            picture = request.FILES.get("picture")

            if not all([lot_name, vehicle_type, vehicle_capacity, price_per_hour, location_name, latitude, longitude]):
                return Response({"status": "error", "message": "All fields are required except picture."}, status=status.HTTP_400_BAD_REQUEST)

            parking_lot = ParkingLot(
                owner=request.user,
                lot_name=lot_name,
                vehicle_type=vehicle_type,
                vehicle_capacity=int(vehicle_capacity),
                price_per_hour=float(price_per_hour),
                location_name=location_name,
                latitude=float(latitude),
                longitude=float(longitude),
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
                    "location_name": parking_lot.location_name,
                    "latitude": float(parking_lot.latitude),
                    "longitude": float(parking_lot.longitude),
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error adding parking lot: {str(e)}")
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ListAllParkingLotsAPIView(APIView):
    def get(self, request):
        try:
            parking_lots = ParkingLot.objects.all()
            parking_lot_data = [
                {
                    "id": pl.id,
                    "lot_name": pl.lot_name,
                    "location_name": pl.location_name,
                    "vehicle_type": pl.vehicle_type,
                    "vehicle_capacity": pl.vehicle_capacity,
                    "price_per_hour": float(pl.price_per_hour),
                    "latitude": float(pl.latitude) if pl.latitude else None,
                    "longitude": float(pl.longitude) if pl.longitude else None,
                }
                for pl in parking_lots
            ]
            return Response({"status": "success", "parking_lots": parking_lot_data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching all parking lots: {str(e)}")
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
class EditParkingLotAPIView(APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"status": "error", "message": "You must be logged in to edit a parking lot."}, status=status.HTTP_401_UNAUTHORIZED)

        tab_id = request.GET.get('tab_id', 'default')
        role_key = f"current_role_{tab_id}"
        user_roles = request.session.get(role_key, request.user.role if isinstance(request.user.role, list) else [request.user.role])
        if "owner" not in user_roles:
            return Response({"status": "error", "message": "Only users with the 'owner' role can edit parking lots."}, status=status.HTTP_403_FORBIDDEN)

        parking_lot_id = request.data.get("parking_lot_id")
        if not parking_lot_id:
            return Response({"status": "error", "message": "Parking lot ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            parking_lot = ParkingLot.objects.get(id=parking_lot_id, owner=request.user)
            
            lot_name = request.data.get("lot_name", parking_lot.lot_name)
            vehicle_type = request.data.get("vehicle_type", parking_lot.vehicle_type)
            vehicle_capacity = request.data.get("vehicle_capacity", parking_lot.vehicle_capacity)
            price_per_hour = request.data.get("price_per_hour", parking_lot.price_per_hour)
            location_name = request.data.get("location_name", parking_lot.location_name)
            latitude = request.data.get("latitude", parking_lot.latitude)
            longitude = request.data.get("longitude", parking_lot.longitude)
            picture = request.FILES.get("picture")

            parking_lot.lot_name = lot_name
            parking_lot.vehicle_type = vehicle_type
            parking_lot.vehicle_capacity = int(vehicle_capacity)
            parking_lot.price_per_hour = float(price_per_hour)
            parking_lot.location_name = location_name
            parking_lot.latitude = float(latitude) if latitude else parking_lot.latitude
            parking_lot.longitude = float(longitude) if longitude else parking_lot.longitude
            if picture:
                parking_lot.picture = picture
            parking_lot.save()

            return Response({
                "status": "success",
                "message": f"Successfully updated parking lot {parking_lot.lot_name}.",
                "parking_lot": {
                    "id": parking_lot.id,
                    "lot_name": parking_lot.lot_name,
                    "vehicle_type": parking_lot.vehicle_type,
                    "vehicle_capacity": parking_lot.vehicle_capacity,
                    "price_per_hour": float(parking_lot.price_per_hour),
                    "location_name": parking_lot.location_name,
                    "latitude": float(parking_lot.latitude),
                    "longitude": float(parking_lot.longitude),
                }
            }, status=status.HTTP_200_OK)
        except ParkingLot.DoesNotExist:
            return Response({"status": "error", "message": "Parking lot not found or you do not own it."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error editing parking lot: {str(e)}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Update ListParkingLotsAPIView to include new fields
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
                    "location_name": pl.location_name,
                    "latitude": float(pl.latitude),
                    "longitude": float(pl.longitude),
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

            # Create reservation
            reservation = Reservation.objects.create(
                user=request.user,
                parking_lot=parking_lot,
                status='Active'
            )
            parking_lot.vehicle_capacity -= 1
            parking_lot.save()
            logger.info(f"Reservation created: ID={reservation.id}, User={request.user.username}, Lot={parking_lot.lot_name}")

            return Response({
                "status": "success",
                "message": f"Successfully reserved a slot in {parking_lot.lot_name}.",
                "updated_capacity": parking_lot.vehicle_capacity,
                "reservation_id": reservation.id,
                "reservation": {
                    "id": reservation.id,
                    "lot_name": parking_lot.lot_name,
                    "location_name": parking_lot.location_name,
                    "vehicle_type": parking_lot.vehicle_type,
                    "price_per_hour": float(parking_lot.price_per_hour)
                }
            }, status=status.HTTP_200_OK)
        except ParkingLot.DoesNotExist:
            logger.error(f"Parking lot {parking_lot_id} not found")
            return Response({"status": "error", "message": "Parking lot not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error reserving parking lot: {str(e)}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DownloadReceiptAPIView(APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated attempt to download receipt")
            return Response({"status": "error", "message": "You must be logged in."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            reservation_id = request.data.get('reservation_id')
            hours = int(request.data.get('hours', 1))
            total_price = float(request.data.get('total_price'))

            reservation = Reservation.objects.get(id=reservation_id, user=request.user)
            parking_lot = reservation.parking_lot

            # Create PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph("ParkShare Reservation Receipt", styles['Title']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 12))

            data = [
                ["Field", "Details"],
                ["Reservation ID", str(reservation.id)],
                ["Lot Name", parking_lot.lot_name],
                ["Location", parking_lot.location_name],
                ["Vehicle Type", parking_lot.vehicle_type],
                ["Hours Reserved", str(hours)],
                ["Price per Hour", f"Rs {parking_lot.price_per_hour}"],
                ["Total Price", f"Rs {total_price}"]
            ]
            table = Table(data, colWidths=[150, 250])
            table.setStyle([
                ('BACKGROUND', (0, 0), (-1, 0), '#d3d3d3'),
                ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), '#f5f5f5'),
                ('GRID', (0, 0), (-1, -1), 1, '#000000'),
            ])
            elements.append(table)

            doc.build(elements)
            pdf = buffer.getvalue()
            buffer.close()

            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Receipt_{reservation_id}.pdf"'
            logger.info(f"Receipt downloaded for reservation {reservation_id} by {request.user.username}")
            return response
        except Reservation.DoesNotExist:
            logger.error(f"Reservation {reservation_id} not found or not owned by {request.user.username}")
            return Response({"status": "error", "message": "Reservation not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error generating receipt: {str(e)}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
class UserReservationsAPIView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated request to view reservations")
            return Response({"status": "error", "message": "You must be logged in to view reservations."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            logger.info(f"Fetching reservations for user: {request.user.username}")
            reservations = Reservation.objects.filter(user=request.user).select_related('parking_lot')
            logger.info(f"Found {reservations.count()} reservations for user: {request.user.username}")

            data = [{
                "id": res.id,
                "lot_name": res.parking_lot.lot_name,
                "location": res.parking_lot.location_name,  # Fixed to location_name
                "vehicle_type": res.parking_lot.vehicle_type,  # Added
                "price_per_hour": float(res.parking_lot.price_per_hour),  # Added
                "timestamp": res.timestamp.isoformat(),  # Using timestamp instead of created_at
                "status": res.status
            } for res in reservations]

            return Response({"status": "success", "reservations": data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching user reservations: {str(e)}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# core/views.py
class OwnerReservationsAPIView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated request to view owner reservations")
            return Response({"status": "error", "message": "You must be logged in to view reservations."}, status=status.HTTP_401_UNAUTHORIZED)

        tab_id = request.GET.get('tab_id', 'default')
        role_key = f"current_role_{tab_id}"
        user_roles = request.session.get(role_key, request.user.role if isinstance(request.user.role, list) else [request.user.role])
        if "owner" not in user_roles:
            logger.error("User does not have owner role")
            return Response({"status": "error", "message": "Only users with the 'owner' role can view parking lot reservations."}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Get all parking lots owned by the user
            owner_parking_lots = ParkingLot.objects.filter(owner=request.user)
            if not owner_parking_lots.exists():
                logger.info(f"No parking lots found for owner: {request.user.username}")
                return Response({"status": "success", "reservations": []}, status=status.HTTP_200_OK)

            # Get all reservations for those parking lots
            reservations = Reservation.objects.filter(parking_lot__in=owner_parking_lots).select_related('parking_lot', 'user')
            logger.info(f"Found {reservations.count()} reservations for owner: {request.user.username}")

            # Serialize the data
            data = [{
                "id": res.id,
                "lot_name": res.parking_lot.lot_name,
                "location": res.parking_lot.location_name,  # Fixed to location_name
                "user": res.user.username,
                "status": res.status,
                "created_at": res.timestamp.isoformat(),  # Assuming timestamp is the creation time
                "slot_number": getattr(res, 'slot_number', 'N/A'),  # Handle if field doesn't exist
                "start_time": res.start_time.isoformat() if hasattr(res, 'start_time') and res.start_time else 'N/A',
                "end_time": res.end_time.isoformat() if hasattr(res, 'end_time') and res.end_time else 'N/A',
                "vehicle_id": getattr(res, 'vehicle_id', 'N/A'),  # Handle if field doesn't exist
                "vehicle_capacity": res.parking_lot.vehicle_capacity,  # Added for completeness
                "price_per_hour": float(res.parking_lot.price_per_hour)  # Added for completeness
            } for res in reservations]

            return Response({"status": "success", "reservations": data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching owner reservations: {str(e)}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
# Existing owner_home_view (for reference)
@login_required
def owner_home_view(request):
    parking_lots = ParkingLot.objects.filter(owner=request.user)
    return render(request, 'core/owner_dashboard.html', {'parking_lots': parking_lots})

# New view for owner reservations page
@login_required
def owner_reservations_view(request):
    return render(request, 'core/owner_reservations.html', {'user': request.user})

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
            location_name = request.data.get("location_name", parking_lot.location_name)
            picture = request.FILES.get("picture", parking_lot.picture)

            parking_lot.lot_name = lot_name
            parking_lot.vehicle_type = vehicle_type
            parking_lot.vehicle_capacity = int(vehicle_capacity)
            parking_lot.price_per_hour = float(price_per_hour)
            parking_lot.location_name = location_name
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
    
@login_required
def view_reservations(request):
    return render(request, 'core/view_reservations.html', {'user': request.user})

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
        csrf_token = get_token(request)  # Get a fresh 64-char token
        logger.info(f"Generated CSRF token for tab {request.GET.get('tab_id', 'default')}: {csrf_token}, Length: {len(csrf_token)}")
        return render(request, 'core/owner_dashboard.html', {
            'parking_lots': parking_lots,
            'csrf_token': csrf_token  # Pass it explicitly
        })
    except Exception as e:
        print(f"Error fetching parking lots: {str(e)}")
        csrf_token = get_token(request)
        logger.info(f"Generated CSRF token (error case) for tab {request.GET.get('tab_id', 'default')}: {csrf_token}, Length: {len(csrf_token)}")
        return render(request, 'core/owner_dashboard.html', {
            'parking_lots': [],
            'error': str(e),
            'csrf_token': csrf_token
        })
        
@login_required
def admin_dashboard_view(request):
    tab_id = request.GET.get('tab_id', 'default')
    role_key = f"current_role_{tab_id}"
    user_roles = request.session.get(role_key, request.user.role if isinstance(request.user.role, list) else [request.user.role])

    # Restrict to superusers (admins)
    if not request.user.is_superuser:
        logger.error(f"User {request.user.username} attempted admin access without permission")
        return render(request, 'core/login.html', {'error': "Admin access only"})

    logger.info(f"Admin dashboard accessed by user: {request.user.username}")
    return render(request, 'core/admin_dashboard.html', {'user': request.user})

class AdminAnalyticsAPIView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated request to admin analytics")
            return Response({"status": "error", "message": "You must be logged in."}, status=status.HTTP_401_UNAUTHORIZED)

        if not request.user.is_superuser:
            logger.error(f"User {request.user.username} is not an admin")
            return Response({"status": "error", "message": "Only admins can access analytics."}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Number of parking lots
            total_parking_lots = ParkingLot.objects.count()

            # Number of users (excluding superusers)
            total_users = CustomUser.objects.filter(is_superuser=False).count()

            # Average occupancy (reservations vs capacity)
            parking_lots = ParkingLot.objects.annotate(
                reservation_count=Count('reservation')  # Now works with Count imported
            )
            total_capacity = sum(pl.vehicle_capacity for pl in parking_lots)
            total_reserved = sum(pl.reservation_count for pl in parking_lots if pl.reservation_count > 0)
            average_occupancy = (total_reserved / total_capacity * 100) if total_capacity > 0 else 0

            # Active reservations
            active_reservations = Reservation.objects.filter(status="Active").count()

            data = {
                "total_parking_lots": total_parking_lots,
                "total_users": total_users,
                "average_occupancy": round(average_occupancy, 2),  # Percentage
                "active_reservations": active_reservations
            }
            return Response({"status": "success", "analytics": data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching admin analytics: {str(e)}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
class AdminReportDownloadAPIView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated request to admin report download")
            return Response({"status": "error", "message": "You must be logged in."}, status=status.HTTP_401_UNAUTHORIZED)

        if not request.user.is_superuser:
            logger.error(f"User {request.user.username} is not an admin")
            return Response({"status": "error", "message": "Only admins can access reports."}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Fetch analytics data
            total_parking_lots = ParkingLot.objects.count()
            total_users = CustomUser.objects.filter(is_superuser=False).count()
            parking_lots = ParkingLot.objects.annotate(
                reservation_count=Count('reservation')
            )
            total_capacity = sum(pl.vehicle_capacity for pl in parking_lots)
            total_reserved = sum(pl.reservation_count for pl in parking_lots)
            average_occupancy = (total_reserved / total_capacity * 100) if total_capacity > 0 else 0
            active_reservations = Reservation.objects.filter(status="Active").count()

            # Create PDF in memory
            buffer = BytesIO()  # Now works with import
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            elements.append(Paragraph("ParkShare Admin Report", styles['Title']))
            elements.append(Spacer(1, 12))

            # Date and Time
            elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 12))

            # Analytics Table
            data = [
                ["Metric", "Value"],
                ["Total Parking Lots", str(total_parking_lots)],
                ["Total Users", str(total_users)],
                ["Average Occupancy", f"{round(average_occupancy, 2)}%"],
                ["Active Reservations", str(active_reservations)],
            ]
            table = Table(data, colWidths=[200, 200])
            table.setStyle([
                ('BACKGROUND', (0, 0), (-1, 0), '#d3d3d3'),
                ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), '#f5f5f5'),
                ('GRID', (0, 0), (-1, -1), 1, '#000000'),
            ])
            elements.append(table)

            # Build PDF
            doc.build(elements)
            pdf = buffer.getvalue()
            buffer.close()

            # Serve PDF as downloadable file
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="ParkShare_Admin_Report.pdf"'
            logger.info(f"Admin report downloaded by {request.user.username}")
            return response

        except Exception as e:
            logger.error(f"Error generating admin report: {str(e)}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def role_selection_view(request):
    return render(request, 'core/role_selection.html')

@login_required
def role_redirect_view(request):
    if request.method == "POST":
        selected_role = request.POST.get("role")
        logger.info(f"Received role: {selected_role}")

        if selected_role:
            tab_id = request.GET.get('tab_id', 'default')
            role_key = f"current_role_{tab_id}"
            if request.user.is_superuser and selected_role == "Admin":
                request.session[role_key] = ['admin']
            elif selected_role in ['Driver', 'Owner']:
                request.session[role_key] = [selected_role.lower()]  # Normalize to lowercase
            else:
                return render(request, "core/role_selection.html", {"error": "Invalid role selected"})

            logger.info(f"Set {role_key} to {request.session[role_key]} for session {request.session.session_key}")

            if request.session[role_key] == ['driver']:
                return redirect("user_dashboard")
            elif request.session[role_key] == ['owner']:
                return redirect("owner_dashboard")
            elif request.session[role_key] == ['admin']:
                return redirect("admin_dashboard")

    return render(request, "core/role_selection.html")