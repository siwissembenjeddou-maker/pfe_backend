import logging
from django.core.mail import send_mail
from django.conf import settings as django_settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, PasswordResetCode
from .serializers import (
    UserSerializer,
    LoginSerializer,
    CreateUserSerializer,
    ProfileUpdateSerializer,
    ForgotPasswordSerializer,
    VerifyResetCodeSerializer,
    ResetPasswordSerializer,
)
from .permissions import IsAdminUserRole, IsAdminOrSelf
from apps.system_logs.utils import log_event

logger = logging.getLogger(__name__)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            log_event('User login', user=user, metadata={'email': user.email, 'role': user.role})
            return Response({
                'success': True,
                'user': UserSerializer(user, context={'request': request}).data,
            })
        return Response({
            'success': False,
            'message': list(serializer.errors.values())[0][0],
        }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    def post(self, request):
        try:
            token = RefreshToken(request.data.get('refresh'))
            token.blacklist()
        except Exception as e:
            logger.warning(f'Logout token blacklist failed (token may already be invalid): {e}')
        return Response({'success': True})


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data)


class ProfileUpdateView(APIView):
    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
#  Password-reset flow  (3 steps)
# ─────────────────────────────────────────────────────────────────────────────

class ForgotPasswordView(APIView):
    """
    Step 1 – Request an OTP.
    POST { "email": "user@example.com" }
    Sends a 6-digit code to the user's email (valid 10 min).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = list(serializer.errors.values())[0][0]
            return Response(
                {"success": False, "message": str(first_error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email).first()

        if not user:
            return Response(
                {"success": False, "message": "This email does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete any previous unused codes so only the latest is valid
        PasswordResetCode.objects.filter(user=user).delete()

        code = PasswordResetCode.generate_code()
        PasswordResetCode.objects.create(user=user, code=code)

        # Send email
        try:
            send_mail(
                subject="Your Autisense password-reset code",
                message=(
                    f"Hello {user.name},\n\n"
                    f"Your password-reset verification code is:\n\n"
                    f"  {code}\n\n"
                    f"This code expires in 10 minutes.\n"
                    f"If you did not request a password reset, please ignore this email.\n\n"
                    f"— The Autisense Team"
                ),
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(f"Password-reset code sent to {email} (backend: {django_settings.EMAIL_BACKEND})")
        except Exception as exc:
            logger.error(f"Failed to send password-reset email to {email}: {type(exc).__name__}: {exc}")
            return Response(
                {"success": False, "message": f"Could not send email. Please try again later. ({type(exc).__name__})"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        log_event(
            "Password reset requested",
            user=user,
            metadata={"email": user.email, "role": user.role},
        )

        return Response(
            {"success": True, "message": "A verification code has been sent to your email."},
            status=status.HTTP_200_OK,
        )


class VerifyResetCodeView(APIView):
    """
    Step 2 – Verify the OTP before showing the new-password form.
    POST { "email": "user@example.com", "code": "123456" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyResetCodeSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = list(serializer.errors.values())[0][0]
            return Response(
                {"success": False, "message": str(first_error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"]
        code  = serializer.validated_data["code"]

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response(
                {"success": False, "message": "Invalid email or code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset_code = (
            PasswordResetCode.objects
            .filter(user=user, code=code)
            .order_by('-created_at')
            .first()
        )

        if not reset_code or not reset_code.is_valid:
            return Response(
                {"success": False, "message": "Invalid or expired verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"success": True, "message": "Code verified. You can now reset your password."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    """
    Step 3 – Set the new password.
    POST { "email": "user@example.com", "code": "123456", "new_password": "newPass123" }
    Marks the code as used after a successful reset.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = list(serializer.errors.values())[0][0]
            return Response(
                {"success": False, "message": str(first_error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email        = serializer.validated_data["email"]
        code         = serializer.validated_data["code"]
        new_password = serializer.validated_data["new_password"]

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response(
                {"success": False, "message": "Invalid email or code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset_code = (
            PasswordResetCode.objects
            .filter(user=user, code=code)
            .order_by('-created_at')
            .first()
        )

        if not reset_code or not reset_code.is_valid:
            return Response(
                {"success": False, "message": "Invalid or expired verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Apply new password & mark code used
        user.set_password(new_password)
        user.save()

        reset_code.used = True
        reset_code.save()

        log_event(
            "Password reset completed",
            user=user,
            metadata={"email": user.email},
        )

        return Response(
            {"success": True, "message": "Password reset successfully. You can now sign in."},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            log_event('User registered', user=user, metadata={'email': user.email, 'role': user.role})
            return Response({
                'success': True,
                'user': UserSerializer(user, context={'request': request}).data,
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': list(serializer.errors.values())[0][0],
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


class UserListCreateView(generics.ListCreateAPIView):
    queryset         = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUserRole]

    def get_queryset(self):
        qs   = super().get_queryset()
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = CreateUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            log_event('User created', user=request.user, metadata={'created_user': user.email, 'role': user.role})
            return Response(
                UserSerializer(user, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(generics.RetrieveDestroyAPIView):
    queryset         = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrSelf]

    def perform_destroy(self, instance):
        deleted_email = instance.email
        deleted_role = instance.role
        deleted_pk = instance.pk

        log_event(
            'User deleted',
            user=self.request.user,
            metadata={'deleted_user': deleted_email, 'role': deleted_role},
        )

        instance.delete()

        if User.objects.filter(pk=deleted_pk).exists():
            raise RuntimeError("User hard-delete failed; user row still exists.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'success': True, 'message': 'User deleted successfully.'},
            status=status.HTTP_200_OK,
        )
