from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, QRCode

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile, includes user-related fields like phone_number.
    """
    user = serializers.StringRelatedField()  # Serialize the related User (username)
    
    class Meta:
        model = UserProfile
        fields = ['user', 'phone_number']

class QRCodeSerializer(serializers.ModelSerializer):
    """
    Serializer for QRCode to handle QR code data.
    """
    class Meta:
        model = QRCode
        fields = ['qr_id', 'one_time_token', 'is_registered', 'created_at']
