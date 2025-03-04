from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm, ParkingLotForm
from .models import ParkingSpace
import logging
from django.http import JsonResponse
from .models import ParkingSpace
from .forms import ParkingLotForm
from .models import ParkingSpace
from .forms import ParkingLotForm
import requests
from django.contrib import messages
from .forms import UserProfileForm, ChangePasswordForm
from .models import Reservation



# Set up logging
logger = logging.getLogger(__name__)

# Home page view
def home(request):
    return render(request, 'core/home.html')


# User login view with role-based redirection
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        role = request.POST.get('role')

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if role == 'driver':
                return redirect(reverse('core:user_dashboard'))
            elif role == 'owner':
                return redirect(reverse('core:owner_dashboard'))

            return redirect(reverse('core:home'))

        else:
            logger.error(f"Login failed: {form.errors}")
            return render(request, 'core/login.html', {'form': form, 'error': "Invalid username or password"})

    else:
        form = AuthenticationForm()
    
    return render(request, 'core/login.html', {'form': form})

# User logout view
@login_required
def user_logout(request):
    logout(request)
    return redirect(reverse('core:home'))

# User registration view
def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('core:user_login'))
        else:
            logger.error(f"Registration errors: {form.errors}")
    else:
        form = CustomUserCreationForm()

    return render(request, 'core/register.html', {'form': form})

# User dashboard view
@login_required
def user_dashboard(request):
    parking_lots = ParkingSpace.objects.all()  # ✅ Fetch all parking spaces
    print("Parking Spaces:", parking_lots)
    return render(request, 'core/user_dashboard.html',{'parking_spaces': parking_lots})

# Owner dashboard view
@login_required
def owner_dashboard(request):
    
    parking_lots = ParkingSpace.objects.filter(owner=request.user)  # ✅ Ensure it loads all lots
    return render(request, 'core/owner_dashboard.html', {'parking_lots': parking_lots})

# Parking space list view
def parking_space_list(request):
    vehicle_type = request.GET.get('vehicle_type', None)
    parking_spaces = ParkingSpace.objects.all()
    
    if vehicle_type:
        parking_spaces = parking_spaces.filter(vehicle_type=vehicle_type)
    
    return render(request, 'core/parking_space_list.html', {'parking_spaces': parking_spaces})


# ✅ View for Adding a New Parking Space
@login_required
def add_parking_space(request):
    if request.method == "POST":
        form = ParkingLotForm(request.POST, request.FILES)
        if form.is_valid():
            parking_space = form.save(commit=False)
            parking_space.owner = request.user

            # 🗺️ Get latitude & longitude using OpenStreetMap API
            geocode_url = f"https://nominatim.openstreetmap.org/search?q={parking_space.location}&format=json"
            headers = {
                "User-Agent": "ParkShare/1.0 (dinasreep@gmail.com)"  # Replace with your app name and email
            }
            try:
                response = requests.get(geocode_url, headers=headers, timeout=5)
                response.raise_for_status()  # 🚨 Raise error if status != 200
                geocode_data = response.json()

                if geocode_data and len(geocode_data) > 0:
                    parking_space.latitude = float(geocode_data[0]["lat"])
                    parking_space.longitude = float(geocode_data[0]["lon"])
                else:
                    return JsonResponse({"success": False, "error": "Location not found"}, status=400)

            except requests.exceptions.RequestException as e:
                return JsonResponse({"success": False, "error": f"Geocoding API error: {str(e)}"}, status=500)

            parking_space.save()

            return JsonResponse({
                'success': True,
                'id': parking_space.id,
                'lotName': parking_space.lot_name,
                'location': parking_space.location,
                'latitude': parking_space.latitude,
                'longitude': parking_space.longitude,
                'startTime': str(parking_space.start_time),
                'endTime': str(parking_space.end_time),
                'pricePerHour': str(parking_space.price_per_hour),
                'vehicleType': parking_space.vehicle_type,
                'vehicleCapacity': parking_space.vehicle_capacity,
                'date': str(parking_space.date),
                'imageUrl': parking_space.picture.url if parking_space.picture else ''
            })

        else:
            print("❌ Form Errors:", form.errors)
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    return JsonResponse({'success': False}, status=400)


# ✅ View for Editing an Existing Parking Space
@login_required
def edit_parking_space(request, id):
    parking_space = get_object_or_404(ParkingSpace, id=id, owner=request.user)

    if request.method == "POST":
        form = ParkingLotForm(request.POST, request.FILES, instance=parking_space)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    # ✅ Return existing parking lot details for editing
    return JsonResponse({
        'success': True,
        'id': parking_space.id,
        'lotName': parking_space.lot_name,
        'location': parking_space.location,
        'latitude': parking_space.latitude,
        'longitude': parking_space.longitude,
        'startTime': str(parking_space.start_time),
        'endTime': str(parking_space.end_time),
        'pricePerHour': str(parking_space.price_per_hour),
        'vehicleType': parking_space.vehicle_type,
        'vehicleCapacity': parking_space.vehicle_capacity,
        'date': str(parking_space.date),
        'imageUrl': parking_space.picture.url if parking_space.picture else ''
    })


# ✅ View for Deleting a Parking Space
@login_required
def delete_parking_space(request, pk):
    if request.method == "POST":
        parking_space = get_object_or_404(ParkingSpace, id=pk, owner=request.user)
        parking_space.delete()
        return JsonResponse({"success": True, "message": "Parking space deleted successfully"})

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)


# ✅ View to Load Parking Spaces for Map
def get_parking_spaces(request):
    parking_spaces = ParkingSpace.objects.filter(is_approved=True).values(
        "id", "lot_name", "location", "latitude", "longitude", 
        "price_per_hour", "vehicle_type", "vehicle_capacity"
    )
    return JsonResponse(list(parking_spaces), safe=False)

@login_required
def view_reservations(request):
    return render(request, 'core/reservations.html')

@login_required
def user_profile(request):
    return render(request, "core/profile.html", {
        'user': request.user
    })

# View to update user profile
@login_required
def update_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('core:user_profile')  # Redirect to the profile page after saving
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'core/profile.html', {'form': form})

# View to change the user's password
@login_required
def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password changed successfully!")
            return redirect('core:user_profile')  # Redirect to the profile page after changing password
    else:
        form = ChangePasswordForm(user=request.user)

    return render(request, 'core/profile.html', {'form': form})



def payment_confirmation(request, lot_id):
    parking_lot = get_object_or_404(ParkingSpace, id=lot_id)
    return render(request, 'core/payment_confirmation.html', {'parking_lot': parking_lot})

@login_required
def reservations(request, lot_id=None):
    if request.method == "POST":
        # Fetch the parking lot by ID
        parking_lot = get_object_or_404(ParkingSpace, id=lot_id)

        # Check if there are available slots
        if parking_lot.vehicle_capacity > 0:
            # Create a reservation entry
            reservation = Reservation.objects.create(
                user=request.user,
                parking_lot=parking_lot,
                status='Booked'
            )

            # Decrease available slots in the parking lot
            parking_lot.vehicle_capacity -= 1
            parking_lot.save()

            return JsonResponse({"success": True, "message": "Reservation confirmed!"})

        else:
            return JsonResponse({"success": False, "error": "No slots available"})

    # If GET request (no POST)
    # Fetch all confirmed reservations for the logged-in user
    reservations = Reservation.objects.filter(user=request.user, status='Booked')

    # Render the reservations template
    return render(request, 'core/reservations.html', {'reservations': reservations})