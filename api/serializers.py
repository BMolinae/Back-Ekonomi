from rest_framework import serializers
from .models import Movimiento, Categoria, PerfilUsuario
from django.contrib.auth.models import User

class MovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movimiento
        fields = '__all__'
        read_only_fields = ['usuario', 'fecha']

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create (self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        if not PerfilUsuario.objects.filter(usuario=user).exists():
            PerfilUsuario.objects.create(usuario=user)

        return user