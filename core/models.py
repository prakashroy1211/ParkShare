from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.EmailField(max_length=150, unique=True)
    phone_number = models.CharField(max_length=15)
    role = models.JSONField(default=list)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

class ParkingLot(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='parking_lots')
    lot_name = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=20, choices=[
        ('Car', 'Car'),
        ('Bike', 'Bike'),
        ('Truck', 'Truck'),
    ])
    vehicle_capacity = models.PositiveIntegerField()
    price_per_hour = models.DecimalField(max_digits=6, decimal_places=2)
    location_name = models.CharField(max_length=255)  # Renamed from 'location'
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    picture = models.ImageField(upload_to='parking_lots/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.lot_name

class Reservation(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    slot_number = models.CharField(max_length=10, null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    vehicle_id = models.BigIntegerField(null=True, blank=True)