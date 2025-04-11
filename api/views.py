from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Movimiento
from .serializers import MovimientoSerializer

# Create your views here.

class MovimientoViewSet(viewsets.ModelViewSet):
    queryset = Movimiento.objects.all()
    serializer_class = MovimientoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
