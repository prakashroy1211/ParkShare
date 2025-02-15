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

# Add parking space view
@login_required
def add_parking_space(request):
    if request.method == "POST":
        form = ParkingLotForm(request.POST, request.FILES)
        if form.is_valid():
            parking_space = form.save(commit=False)
            parking_space.owner = request.user
            parking_space.save()
            return JsonResponse({
                'success': True,
                'lotName': parking_space.lot_name,
                'location': parking_space.location,
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

# Edit parking space
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
        'startTime': str(parking_space.start_time),
        'endTime': str(parking_space.end_time),
        'pricePerHour': str(parking_space.price_per_hour),
        'vehicleType': parking_space.vehicle_type,
        'vehicleCapacity': parking_space.vehicle_capacity,
        'date': str(parking_space.date),
        'imageUrl': parking_space.picture.url if parking_space.picture else ''
    })


# ✅ Delete Parking Lot
@login_required
def delete_parking_space(request, id):
    parking_space = get_object_or_404(ParkingSpace, pk=pk, owner=request.user)
    parking_space.delete()
    return JsonResponse({'success': True})

@login_required
def view_reservations(request):
    return render(request, 'core/reservations.html')

@login_required
def user_profile(request):
    return render(request, "core/profile.html")