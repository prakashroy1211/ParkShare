from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm, LoginForm
from .models import ParkingSpace
import logging

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
    return render(request, 'core/user_dashboard.html')

# Owner dashboard view
@login_required
def owner_dashboard(request):
    parking_lots = ParkingSpace.objects.filter(owner=request.user)  # Filter parking lots by owner
    return render(request, 'core/owner_dashboard.html', {'parking_lots': parking_lots})

# Parking space list view
def parking_space_list(request):
    vehicle_type = request.GET.get('vehicle_type', None)
    parking_spaces = ParkingSpace.objects.filter(available=True)
    
    if vehicle_type:
        parking_spaces = parking_spaces.filter(vehicle_type=vehicle_type)
    
    return render(request, 'core/parking_space_list.html', {'parking_spaces': parking_spaces})

# Add parking space view
def add_parking_space(request):
    if request.method == "POST":
        location = request.POST.get("location")
        vehicle_type = request.POST.get("vehicle_type")
        ParkingSpace.objects.create(name="Parking Lot", price=60, location=location, vehicle_type=vehicle_type, timings="06:00-00:00")
        return redirect("core:parking_space_list")

    return render(request, 'core/add_parking_space.html')

# Add parking lot view
def add_parking_lot(request):
    if request.method == 'POST':
        form = ParkingLotForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('core:owner_dashboard')
    else:
        form = ParkingLotForm()
    
    return render(request, 'core/add_parking_lot.html', {'form': form})

# Profile view
def profile(request):
    return render(request, 'core/profile.html')

# View reservations
def view_reservations(request):
    return render(request, 'core/view_reservations.html')
# Edit parking space (single definition)
def edit_parking_space(request, pk):
    parking_space = get_object_or_404(ParkingSpace, pk=pk)

    if request.method == "POST":
        parking_space.location = request.POST.get("location")
        parking_space.vehicle_type = request.POST.get("vehicle_type")
        parking_space.save()
        return redirect("core:owner_dashboard")

    return render(request, 'core/edit_parking_space.html', {'parking_space': parking_space})
def delete_parking_space(request, pk):
    parking_space = get_object_or_404(ParkingSpace, pk=pk)
    parking_space.delete()
    return redirect('core:parking_space_list')
