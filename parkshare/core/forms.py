from django import forms
from .models import ParkingSpace, Booking

# Form for parking space creation and updates
class ParkingSpaceForm(forms.ModelForm):
    class Meta:
        model = ParkingSpace
        fields = ['vehicle_type', 'length', 'width', 'height', 'price_per_hour', 'location', 'image']

# Form for booking parking spaces
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['parking_space', 'start_time', 'end_time']