import re
from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import User, ServiceOrder, ServiceOrderType, ServiceOrderStatus, ServiceProviderType, ServiceOrderPriority
from .validators import validate_cpf

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6,
        max_length=30,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
        extra_kwargs = {
            'username': {'min_length': 5, 'max_length': 30}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_staff'
        ]
        read_only_fields = ['id', 'is_staff']

    def validate_username(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError('Este nome de usuário já está em uso.')
        return value

    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError('Este e-mail já está em uso.')
        return value

class ServiceOrderSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)

    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    type = serializers.ChoiceField(choices=ServiceOrderType.choices)
    status = serializers.ChoiceField(choices=ServiceOrderStatus.choices)
    provider = serializers.ChoiceField(choices=ServiceProviderType.choices)
    priority = serializers.ChoiceField(choices=ServiceOrderPriority.choices)

    cpf_anonimo = serializers.SerializerMethodField(source='get_cpf_anonimo', read_only=True)

    due_date = serializers.SerializerMethodField()
    sla_status = serializers.SerializerMethodField()
    time_remaining_seconds = serializers.SerializerMethodField()

    cpf = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_cpf],
    )

    class Meta:
        model = ServiceOrder
        fields = [
            'id',
            'protocol',
            'so_number',

            'type',
            'status',
            'provider',
            'priority',

            'type_display',
            'status_display',
            'provider_display',
            'priority_display',

            'recipient_name',
            'cpf',
            'cpf_anonimo',

            'description',

            'created_by',
            'created_at',
            'updated_at',

            'due_date',
            'sla_status',
            'time_remaining_seconds'
        ]

        read_only_fields = [
            'id',
            'created_by',
            'created_at',
            'updated_at',
            'type_display',
            'status_display',
            'provider_display',
            'priority_display',
            'due_date',
            'sla_status',
            'time_remaining_seconds'
        ]

        extra_kwargs = {
            'cpf': {'write_only': True}
        }

    def get_cpf_anonimo(self, obj):
        if hasattr(obj, 'cpf') and isinstance(obj.cpf, str) and len(obj.cpf) == 14:
            return f"{obj.cpf[:3]}.***.***-{obj.cpf[-2:]}"
        return "N/A"

    def _get_sla_hours(self, priority):
        if priority == 'high':
            return 24
        elif priority == 'medium':
            return 48
        else:
            return 72

    def get_due_date(self, obj):
        if not obj.created_at:
            return None

        hours = self._get_sla_hours(obj.priority)
        return obj.created_at + timedelta(hours=hours)

    def get_time_remaining_seconds(self, obj):
        due_date = self.get_due_date(obj)
        if not due_date:
            return None

        if obj.status == 'completed' or obj.status == 'concluida':
             return 0

        now = timezone.now()
        remaining = due_date - now
        return int(remaining.total_seconds())

    def get_sla_status(self, obj):
        if obj.status == 'completed' or obj.status == 'concluida':
             return 'on_time'

        time_remaining = self.get_time_remaining_seconds(obj)
        if time_remaining is None:
            return "N/A"

        if time_remaining < 0:
            return "overdue"

        if time_remaining < (4 * 60 * 60):
            return "nearing_due_date"

        return "on_time"

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        return super().create(validated_data)

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6,
        max_length=30,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        uid = attrs.get('uid')
        token = attrs.get('token')
        new_password = attrs.get('new_password')

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            self.user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({'detail': 'Token inválido ou expirado.'})

        if not default_token_generator.check_token(self.user, token):
            raise serializers.ValidationError({'detail': 'Token inválido ou expirado.'})

        try:
            validate_password(new_password, self.user)
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})

        attrs['user'] = self.user
        return attrs

    def save(self):
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']

        user.set_password(new_password)
        user.save()

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6,
        max_length=30,
        style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Sua senha antiga está incorreta.")
        return value

    def validate_new_password(self, value):
        user = self.context['request'].user
        try:
            validate_password(value, user)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def save(self):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()

