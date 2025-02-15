from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import ParkingSpace, Booking, ParkingSlot, CustomUser

# Form for booking parking spaces
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['parking_space', 'start_time', 'end_time']

    def clean_end_time(self):
        start_time = self.cleaned_data.get('start_time')
        end_time = self.cleaned_data.get('end_time')
        if end_time <= start_time:
            raise forms.ValidationError('End time must be later than start time.')
        return end_time

    def clean_parking_space(self):
        parking_space = self.cleaned_data.get('parking_space')
        if not parking_space.available:
            raise forms.ValidationError('This parking space is already booked.')
        return parking_space

# Registration form
class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, widget=forms.RadioSelect)
    phone_number = forms.CharField(max_length=15, required=True)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2', 'phone_number', 'role', 'username']

# Login form
class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username or Email")
    password = forms.CharField(widget=forms.PasswordInput)

# Form for parking slot creation and updates
class ParkingSlotForm(forms.ModelForm):
    class Meta:
        model = ParkingSlot
        fields = ['parking_space', 'slot_number', 'available', 'vehicle_type']

    def clean_parking_space(self):
        parking_space = self.cleaned_data.get('parking_space')
        if not parking_space.available:
            raise forms.ValidationError('This parking space is not available.')
        return parking_space

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'parking_space' in self.data:
            try:
                parking_space = ParkingSpace.objects.get(id=self.data['parking_space'])
                self.fields['location'].initial = parking_space.location
                self.fields['price_per_hour'].initial = parking_space.price_per_hour
                self.fields['latitude'].initial = parking_space.latitude
                self.fields['longitude'].initial = parking_space.longitude
            except ParkingSpace.DoesNotExist:
                pass  # Handle the case if parking_space doesn't exist or data is invalid

    def clean_slot_number(self):
        slot_number = self.cleaned_data.get('slot_number')
        parking_space = self.cleaned_data.get('parking_space')
        if ParkingSlot.objects.filter(parking_space=parking_space, slot_number=slot_number).exists():
            raise forms.ValidationError('Slot number already exists for this parking space.')
        return slot_number
    


class ParkingLotForm(forms.ModelForm):
    class Meta:
        model = ParkingSpace
        fields = ['lot_name', 'location', 'start_time', 'end_time', 'price_per_hour', 'vehicle_capacity', 'vehicle_type', 'date', 'picture']
