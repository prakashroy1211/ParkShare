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