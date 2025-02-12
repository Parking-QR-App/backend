from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils.timezone import now
from .models import User, BlacklistedAccessToken
from .serializers import (
    RegisterSerializer, VerifyOTPSerializer, UserSerializer,
    VerifyEmailOTPSerializer, EmailOTPSerializer, UpdateUserInfoSerializer
)
from .utils import send_otp_email, generate_otp
from rest_framework_simplejwt.tokens import RefreshToken
import random  # For generating the OTP
from django.utils import timezone
from django.shortcuts import get_object_or_404

# Registration View (Sends OTP to user)
class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        otp = str(random.randint(100000, 999999))  # Generate OTP
        phone_number = request.data['phone_number']
        user = User.objects.filter(phone_number=phone_number).first()

        if user:
            user.otp = otp
            user.otp_expiry = now() + timezone.timedelta(minutes=5)
            user.save()
            return Response({
                'phone_number': user.phone_number,
                'otp': user.otp,
                'message': 'OTP updated for existing phone number.',
                'status': status.HTTP_200_OK
            }, status=status.HTTP_200_OK)
        else:
            user = User.objects.create(
                phone_number=phone_number,
                otp=otp,
                otp_expiry=now() + timezone.timedelta(minutes=5)
            )
            return Response({
                'phone_number': user.phone_number,
                'otp': user.otp,
                'message': 'New user created and OTP sent.',
                'status': status.HTTP_201_CREATED
            }, status=status.HTTP_201_CREATED)


# OTP Verification View (Handles OTP verification for login)
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)

            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'message': 'Login successful',
                'status': status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        return Response({
            'message': 'Invalid OTP',
            'errors': serializer.errors,
            'status': status.HTTP_400_BAD_REQUEST
        }, status=status.HTTP_400_BAD_REQUEST)
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            access_token = request.auth  # Get current access token
            refresh_token = request.data.get("refresh_token")

            if access_token:
                BlacklistedAccessToken.objects.create(token=str(access_token))  # Store token

            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response({'message': "Logged out", "status": status.HTTP_205_RESET_CONTENT}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


# Send Email OTP View (Sends OTP to user's email)
class SendEmailOTPView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = EmailOTPSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = request.user

            if user.email and user.email == email and user.email_verified:
                return Response({
                    "message": "Email already verified.",
                    "status": status.HTTP_200_OK
                }, status=status.HTTP_200_OK)

            otp = generate_otp()  # Generate a new OTP
            user.email_otp = otp
            user.email_otp_expiry = timezone.now() + timezone.timedelta(minutes=10)
            user.save()

            send_otp_email(email, otp)

            return Response({
                "message": "OTP sent to email.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "Invalid email.",
            "errors": serializer.errors,
            "status": status.HTTP_400_BAD_REQUEST
        }, status=status.HTTP_400_BAD_REQUEST)


# Verify Email OTP View (Verifies the OTP entered by the user)
class VerifyEmailOTPView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = VerifyEmailOTPSerializer(data=request.data)

        if serializer.is_valid():
            return Response({
                "message": "Email verified successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        if "Email already verified." in serializer.errors.get("non_field_errors", []):
            return Response({
                "message": "Email already verified.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "Invalid OTP.",
            "errors": serializer.errors,
            "status": status.HTTP_400_BAD_REQUEST
        }, status=status.HTTP_400_BAD_REQUEST)
    
class UpdateUserInfoView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request):
        serializer = UpdateUserInfoSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user  # Get the authenticated user
            serializer.update(user, serializer.validated_data)

            return Response({
                "message": "User information updated successfully.",
                "status": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "Invalid data.",
            "errors": serializer.errors,
            "status": status.HTTP_400_BAD_REQUEST
        }, status=status.HTTP_400_BAD_REQUEST)