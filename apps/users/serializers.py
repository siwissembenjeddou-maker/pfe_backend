from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User


class UserSerializer(serializers.ModelSerializer):
    name       = serializers.SerializerMethodField()
    token      = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ['id', 'name', 'email', 'role', 'avatar_url', 'token']

    def get_name(self, obj):
        return obj.name

    def get_token(self, obj):
        refresh = RefreshToken.for_user(obj)
        return str(refresh.access_token)

    def get_avatar_url(self, obj):
        if obj.avatar_url:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.avatar_url.url) if request else str(obj.avatar_url.url)
        return None


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField()
    role     = serializers.ChoiceField(choices=['admin', 'parent', 'psychologist', 'educator'])

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        if user.role != data['role']:
            raise serializers.ValidationError(f'This account is not a {data["role"]}')
        if not user.is_active:
            raise serializers.ValidationError('Account is disabled')
        data['user'] = user
        return data


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model  = User
        fields = ['id', 'name', 'email', 'password', 'role', 'phone']

    def create(self, validated_data):
        password   = validated_data.pop('password')
        name       = validated_data.pop('name', '')
        name_parts = name.split(' ', 1)
        user = User(
            username   = validated_data['email'],
            email      = validated_data['email'],
            role       = validated_data.get('role', 'parent'),
            first_name = name_parts[0],
            last_name  = name_parts[1] if len(name_parts) > 1 else '',
        )
        user.set_password(password)
        user.save()
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'avatar_url', 'name']
        read_only_fields = ['avatar_url']

    def update(self, instance, validated_data):
        name = validated_data.pop('name', None)
        if name is not None:
            name_parts = name.split(' ', 1)
            instance.first_name = name_parts[0]
            instance.last_name = name_parts[1] if len(name_parts) > 1 else ''
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
