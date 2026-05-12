import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import UserSerializer, LoginSerializer, CreateUserSerializer, ProfileUpdateSerializer
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
        log_event('User deleted', user=self.request.user, metadata={'deleted_user': instance.email, 'role': instance.role})
        super().perform_destroy(instance)
