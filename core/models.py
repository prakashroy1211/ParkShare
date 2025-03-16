# core/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.EmailField(max_length=150, unique=True)
    phone_number = models.CharField(max_length=15)
    role = models.JSONField(default=list)  # Store roles as a list using JSONField
    USERNAME_FIELD = 'username'  # Use username (which is actually an email) as the username field
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

class ParkingLot(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='parking_lots')
    lot_name = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=20, choices=[
        ('car', 'Car'),
        ('bike', 'Bike'),
        ('truck', 'Truck'),
    ])
    vehicle_capacity = models.PositiveIntegerField()
    price_per_hour = models.DecimalField(max_digits=6, decimal_places=2)
    location = models.CharField(max_length=255)
    picture = models.ImageField(upload_to='parking_lots/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.lot_name