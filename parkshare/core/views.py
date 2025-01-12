from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import ParkingSpace, Booking
from .forms import ParkingSpaceForm, BookingForm
from django.contrib.auth.decorators import login_required

# View to list all parking spaces
from django.shortcuts import render
from .models import ParkingSpace

def parking_space_list(request):
    # For debugging: print/log if view is called
    print("parking_space_list view called")
    
    parking_spaces = ParkingSpace.objects.all()  # Get all parking spaces
    
    # Check if we are fetching data
    print("Fetched parking spaces:", parking_spaces)
    
    return render(request, 'core/parking_space_list.html', {'parking_spaces': parking_spaces})
# View to add a new parking space (for parking lot owners)
@login_required
def add_parking_space(request):
    if request.method == 'POST':
        form = ParkingSpaceForm(request.POST, request.FILES)
        if form.is_valid():
            parking_space = form.save(commit=False)
            parking_space.owner = request.user
            parking_space.save()
            return redirect('core:parking_space_list')
    else:
        form = ParkingSpaceForm()
    return render(request, 'core/add_parking_space.html', {'form': form})

# View to book a parking space
@login_required
def book_parking_space(request, pk):
    parking_space = ParkingSpace.objects.get(pk=pk)
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.total_price = parking_space.price_per_hour * (booking.end_time - booking.start_time).seconds / 3600
            booking.save()
            parking_space.available = False  # Mark the space as unavailable after booking
            parking_space.save()
            return redirect('core:parking_space_list')
    else:
        form = BookingForm(initial={'parking_space': parking_space})
    return render(request, 'core/book_parking_space.html', {'form': form, 'parking_space': parking_space})
