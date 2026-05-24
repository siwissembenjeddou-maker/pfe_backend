from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView,
    LogoutView,
    MeView,
    ProfileUpdateView,
    RegisterView,
    ForgotPasswordView,
    VerifyResetCodeView,
    ResetPasswordView,
)

urlpatterns = [
    path('login',               LoginView.as_view(),         name='login'),
    path('register',            RegisterView.as_view(),      name='register'),
    path('logout',              LogoutView.as_view(),        name='logout'),
    path('me',                  MeView.as_view(),            name='me'),
    path('refresh',             TokenRefreshView.as_view(),  name='token-refresh'),
    path('me/update',           ProfileUpdateView.as_view(), name='profile-update'),
    path('forgot-password/',    ForgotPasswordView.as_view(),   name='forgot-password'),
    path('verify-reset-code/',  VerifyResetCodeView.as_view(),  name='verify-reset-code'),
    path('reset-password/',     ResetPasswordView.as_view(),    name='reset-password'),
]
