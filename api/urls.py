from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    GenerateQRCodeView,
    ScanQRCodeView,
    RegisterViaTokenAPI,
    LogoutView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('generate-qr/', GenerateQRCodeView.as_view(), name='generate_qr'),
    path('scan-qr/<str:hashed_qr_id>/', ScanQRCodeView.as_view(), name='scan_qr'),
    path('register-via-token/<str:one_time_token>/', RegisterViaTokenAPI.as_view(), name='register_via_token'),
    path('token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout')
]
