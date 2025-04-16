from rest_framework import serializers
from .models import Movimiento, Categoria

class MovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movimiento
        fields = '__all__'
        read_only_fields = ['usuario', 'fecha']

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'