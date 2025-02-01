'''
from django.contrib import admin
from .models import ParkingSpace, Booking, VehicleType, UserProfile, CustomUser

admin.site.register(ParkingSpace)
admin.site.register(Booking)
admin.site.register(VehicleType)
admin.site.register(UserProfile)
admin.site.register(CustomUser)
'''

from django.contrib import admin
from .models import CustomUser

admin.site.register(CustomUser)