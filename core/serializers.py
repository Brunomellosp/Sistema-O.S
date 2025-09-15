from rest_framework import serializers
from .models import User, OrdemServico

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class OrdemServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdemServico
        fields = ['id', 'cliente', 'descricao', 'prioridade', 'status', 'criado_por', 'criado_em', 'atualizado_em']
        read_only_fields = ['id', 'criado_por', 'criado_em', 'atualizado_em']
