from rest_framework import serializers
from .models import User, ServiceOrder, ServiceOrderType, ServiceOrderStatus, ServiceProviderType, ServiceOrderPriority

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
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

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
        ]

        extra_kwargs = {
            'cpf': {'write_only': True}
        }

    def get_cpf_anonimo(self, obj):
        if hasattr(obj, 'cpf') and isinstance(obj.cpf, str) and len(obj.cpf) == 14:
            return f"{obj.cpf[:3]}.***.***-{obj.cpf[-2:]}"
        return "N/A"

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        return super().create(validated_data)
