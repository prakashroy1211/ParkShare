from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    role = models.CharField(max_length=10, choices=[('driver', 'Driver'), ('owner', 'Owner')])
    USERNAME_FIELD = 'username'  # Use username (which is actually an email) as the username field
    REQUIRED_FIELDS = []
    def __str__(self):
        return self.username