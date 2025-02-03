from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings
# Vehicle Type choices for users
class VehicleType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('owner', 'Owner'),
    ]
    phone = models.CharField(max_length=15)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return self.username
    
# UserProfile model for extending the default User model (for additional user details)
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.SET_NULL, null=True)
    is_slot_owner = models.BooleanField(default=False)  # New field to track if the user is a slot owner

    def __str__(self):
        return self.user.username

# ParkingSlot model for representing each parking slot
class ParkingSlot(models.Model):
    # Associate the parking slot with a parking space
    parking_space = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Track whether a slot is available
    available = models.BooleanField(default=True)
    # Define the slot number or name
    slot_number = models.CharField(max_length=50)
    # Optional: Define a vehicle type to restrict which vehicle type fits in the slot
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Slot {self.slot_number} in {self.parking_space.location}"

# Parking Space model for parking lot owners
class ParkingSpace(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Should exist
    lot_name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    vehicle_capacity = models.IntegerField()
    vehicle_type = models.CharField(max_length=50)
    picture = models.ImageField(upload_to="parking_spaces/", null=True, blank=True)

    def __str__(self):
        return f"{self.lot_name} - {self.location}"

# Booking model for storing user booking information
class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parking_space = models.ForeignKey(ParkingSpace, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(
        max_length=20,
        choices=[('Paid', 'Paid'), ('Pending', 'Pending')],
        default='Pending'
    )

    def __str__(self):
        return f"Booking by {self.user.username} for {self.parking_space.location}"
  