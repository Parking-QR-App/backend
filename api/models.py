from django.db import models
from django.contrib.auth.models import User  # Referencing the default User model
from django.utils.timezone import now
from datetime import timedelta


class UserProfile(models.Model):
    # Link to the default User model
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Add phone number and any other additional fields here
    phone_number = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.user.username


class QRCode(models.Model):
    qr_id = models.CharField(max_length=100, unique=True)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, default=None, related_name="qr_codes")
    one_time_token = models.CharField(max_length=100, unique=True, null=True, blank=True)
    is_registered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def invalidate_token(self):
        self.one_time_token = None
        self.save()

    def __str__(self):
        return f"QR Code for {self.user_profile.user.username}"
