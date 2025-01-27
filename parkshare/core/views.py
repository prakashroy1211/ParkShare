from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.urls import reverse  # Import reverse for URL generation
from .models import ParkingSpace, Booking
from .forms import ParkingSpaceForm, BookingForm, RegistrationForm, ParkingSlotForm
from django.contrib.auth.models import User

# Home page view
def home(request):
    return render(request, 'core/home.html')

# View to list all parking spaces
def parking_space_list(request):
    vehicle_type = request.GET.get('vehicle_type', None)
    if vehicle_type:
        parking_spaces = ParkingSpace.objects.filter(vehicle_type=vehicle_type, available=True)
    else:
        parking_spaces = ParkingSpace.objects.filter(available=True)
    return render(request, 'core/parking_space_list.html', {'parking_spaces': parking_spaces})

# Registration view for new user
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically log the user in after registration
            return redirect(reverse('core:home'))  # Use reverse to dynamically generate the URL
    else:
        form = RegistrationForm()

    return render(request, 'core/register.html', {'form': form})

# View to add a new parking space
@login_required
def add_parking_space(request):
    if request.method == 'POST':
        form = ParkingSpaceForm(request.POST, request.FILES)
        if form.is_valid():
            parking_space = form.save(commit=False)
            parking_space.owner = request.user
            parking_space.save()
            return redirect(reverse('core:parking_space_list'))  # Use reverse
    else:
        form = ParkingSpaceForm()
    return render(request, 'core/add_parking_space.html', {'form': form})

# View to book a parking space
@login_required
def book_parking_space(request, pk):
    try:
        parking_space = ParkingSpace.objects.get(pk=pk)
    except ParkingSpace.DoesNotExist:
        raise Http404("Parking space not found")
    
    if not parking_space.available:
        return HttpResponse("This parking space is already booked", status=400)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.total_price = parking_space.price_per_hour * (booking.end_time - booking.start_time).seconds / 3600
            booking.save()
            parking_space.available = False
            parking_space.save()
            return redirect(reverse('core:parking_space_list'))  # Use reverse
    else:
        form = BookingForm(initial={'parking_space': parking_space})
    
    return render(request, 'core/book_parking_space.html', {'form': form, 'parking_space': parking_space})

# Login view for custom login page
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(reverse('core:parking_space_list'))  # Use reverse
    else:
        form = AuthenticationForm()
    
    login_url = reverse('core:user_login')  # Example of dynamically generating login URL
    return render(request, 'core/login.html', {'form': form, 'login_url': login_url})

# Search parking spaces view
def search_parking_spaces(request):
    query = request.GET.get('q', '')
    parking_spaces = ParkingSpace.objects.filter(location__icontains=query, available=True)
    return render(request, 'core/parking_space_list.html', {'parking_spaces': parking_spaces, 'query': query})

# Role selection view for users
@login_required
def role_selection(request):
    user = request.user
    if request.method == 'POST':
        is_slot_owner = request.POST.get('is_slot_owner') == 'on'
        user.profile.is_slot_owner = is_slot_owner  # Assuming you have a profile model with 'is_slot_owner'
        user.profile.save()
        return redirect(reverse('core:add_parking_slot'))  # Use reverse
    
    return render(request, 'role_selection.html', {'user': user})

# Add parking slot details view
@login_required
def add_parking_slot(request):
    if not request.user.profile.is_slot_owner:
        return redirect(reverse('core:home'))  # Use reverse

    if request.method == 'POST':
        form = ParkingSlotForm(request.POST)
        if form.is_valid():
            parking_slot = form.save(commit=False)
            parking_slot.owner = request.user
            parking_slot.save()
            return redirect(reverse('core:home'))  # Use reverse
    else:
        form = ParkingSlotForm()

    return render(request, 'add_parking_slot.html', {'form': form})
