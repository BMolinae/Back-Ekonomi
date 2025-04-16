from django.shortcuts import render
from rest_framework import viewsets, permissions, generics
from .models import Movimiento, Categoria, PerfilUsuario
from .serializers import MovimientoSerializer, CategoriaSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from rest_framework.authentication import TokenAuthentication


# Create your views here.

class MovimientoViewSet(viewsets.ModelViewSet):
    queryset = Movimiento.objects.all()
    serializer_class = MovimientoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return Movimiento.objects.filter(usuario=self.request.user)
         

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
        
class CategoriaListCreateView(generics.ListCreateAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = []

def vista_movimientos_html(request):
    return render(request, 'movimientos.html')

def perform_create(self, serializer):
    if self.request.user.is_authenticated:
        movimiento = serializer.save(usuario=self.request.user)
        perfil = PerfilUsuario.objects.get(usuario=self.request.user)

        if movimiento.tipo == 'ingreso':
            perfil.saldo += movimiento.monto
        elif movimiento.tipo == 'gasto':
            perfil.saldo -= movimiento.monto
        
        perfil.save()