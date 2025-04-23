from rest_framework import serializers
from .models import Movimiento, Categoria, PerfilUsuario
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Movimiento, Categoria

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'tipo']

class MovimientoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    categoria        = serializers.PrimaryKeyRelatedField(
                          queryset=Categoria.objects.all(),
                          allow_null=True,
                          required=False
                       )

    class Meta:
        model = Movimiento
        fields = [
            'id',
            'tipo',
            'descripcion',
            'monto',
            'categoria',
            'categoria_nombre',
            'fecha'
        ]
        read_only_fields = ['id', 'fecha', 'categoria_nombre']


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