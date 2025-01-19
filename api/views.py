from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_205_RESET_CONTENT
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
import uuid
import hashlib
from .models import UserProfile, QRCode
from django.contrib.auth.models import User
from .serializers import QRCodeSerializer, UserProfileSerializer


def hash_qr_id(qr_id):
    return hashlib.sha256(qr_id.encode()).hexdigest()


def dehash_qr_id(hashed_qr_id, all_qr_ids):
    for qr_id in all_qr_ids:
        if hash_qr_id(qr_id) == hashed_qr_id:
            return qr_id
    return None


class RegisterView(APIView):
    """
    This view handles the registration of a user.
    It creates a User and UserProfile instance.
    """

    def post(self, request, *args, **kwargs):
        """
        Register a new user and create a UserProfile.
        """
        # Extract the required fields
        username = request.data.get("username")
        password = request.data.get("password")
        phone_number = request.data.get("phone_number")

        if not username or not password or not phone_number:
            return Response({"detail": "Missing required fields."}, status=HTTP_400_BAD_REQUEST)

        # Create a new user
        user = User.objects.create_user(username=username, password=password)

        # Create a UserProfile and store phone number
        user_profile = UserProfile.objects.create(user=user, phone_number=phone_number)

        # Return success response with token
        return Response(
            {
                "message": "User registered successfully.",
                "user_profile": UserProfileSerializer(user_profile).data,
            },
            status=HTTP_201_CREATED,
        )


class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = User.objects.filter(username=username).first()

        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({"refresh": str(refresh), "access": str(refresh.access_token)}, status=HTTP_200_OK)
        return Response({"detail": "Invalid credentials"}, status=HTTP_401_UNAUTHORIZED)


class GenerateQRCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Generates a QR code for the authenticated user's profile.
        Returns a URL containing a hashed QR code ID for scanning.
        """
        # Get the user_profile of the authenticated user
        user_profile = UserProfile.objects.get(user=request.user)

        # Generate a unique QR code ID
        qr_id = str(uuid.uuid4())
        hashed_qr_id = hash_qr_id(qr_id)  # Ensure you have a utility function to hash QR ID

        # Generate a one-time token for the QR code
        one_time_token = str(uuid.uuid4())

        # Create the QRCode instance associated with the user_profile
        QRCode.objects.create(
            qr_id=qr_id,
            user_profile=user_profile,  # Associate the QR code with the user_profile
            one_time_token=one_time_token
        )

        # Construct the URL for scanning the QR code
        qr_code_url = f"http://127.0.0.1:8000/api/scan-qr/{hashed_qr_id}/"
        
        # Return the QR code URL
        return Response({"qr_code_url": qr_code_url}, status=HTTP_201_CREATED)


class ScanQRCodeView(APIView):
    def get(self, request, hashed_qr_id):
        all_qr_ids = QRCode.objects.values_list('qr_id', flat=True)
        qr_id = dehash_qr_id(hashed_qr_id, all_qr_ids)

        if not qr_id:
            return Response({"error": "Invalid or expired QR code."}, status=HTTP_400_BAD_REQUEST)

        qr_code = get_object_or_404(QRCode, qr_id=qr_id)

        if qr_code.is_registered:
            return Response({"message": "Calling"}, status=HTTP_200_OK)

        register_url = f"http://127.0.0.1:8000/api/register-via-token/{qr_code.one_time_token}/"
        return Response(
            {"message": "Redirect to registration", "register_url": register_url}, 
            status=HTTP_200_OK
        )


class RegisterViaTokenAPI(APIView):
    """
    This view registers a user using a one-time token from a scanned QR code.
    """

    def post(self, request, *args, **kwargs):
        """
        Register a new user using the one-time token from the QR code.
        """
        token = request.data.get("one_time_token")
        if not token:
            return Response({"detail": "Missing one-time token."}, status=HTTP_400_BAD_REQUEST)

        try:
            qr_code = QRCode.objects.get(one_time_token=token, is_registered=False)
        except QRCode.DoesNotExist:
            return Response({"detail": "Invalid or expired token."}, status=HTTP_400_BAD_REQUEST)

        # Get user data from the request
        username = request.data.get("username")
        password = request.data.get("password")
        phone_number = request.data.get("phone_number")

        if not username or not password or not phone_number:
            return Response({"detail": "Missing required fields."}, status=HTTP_400_BAD_REQUEST)

        # Create the user
        user = User.objects.create_user(username=username, password=password)

        # Create a UserProfile
        user_profile = UserProfile.objects.create(user=user, phone_number=phone_number)

        # Mark the QR code as registered and invalidate the token
        qr_code.is_registered = True
        qr_code.invalidate_token()

        # Return success message and user profile details
        return Response(
            {
                "message": "User registered successfully.",
                "user_profile": UserProfileSerializer(user_profile).data,
            },
            status=HTTP_201_CREATED,
        )
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=HTTP_400_BAD_REQUEST)