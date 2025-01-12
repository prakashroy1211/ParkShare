from django.contrib import admin
from .models import ParkingSpace, Booking, VehicleType, UserProfile

admin.site.register(ParkingSpace)
admin.site.register(Booking)
admin.site.register(VehicleType)
admin.site.register(UserProfile)