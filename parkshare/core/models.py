from django.db import models
from django.contrib.auth.models import User

# Vehicle Type choices for users
class VehicleType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

# Parking Space model for parking lot owners
class ParkingSpace(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.SET_NULL, null=True)
    length = models.FloatField()
    width = models.FloatField()
    height = models.FloatField(null=True, blank=True)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='parking_spaces/', null=True, blank=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.owner.username}'s space at {self.location}"

# Booking model for storing user booking information
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parking_space = models.ForeignKey(ParkingSpace, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=[('Paid', 'Paid'), ('Pending', 'Pending')], default='Pending')

    def __str__(self):
        return f"Booking by {self.user.username} for {self.parking_space.location}"

# UserProfile model for extending the default User model (for additional user details)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.user.username