from decimal import Decimal
from django.shortcuts import render
from rest_framework import viewsets, permissions, generics, status
from .models import Movimiento, Categoria, PerfilUsuario
from .serializers import MovimientoSerializer, CategoriaSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from api.models import PerfilUsuario


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

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            perfil = PerfilUsuario.objects.get(usuario=user)
            saldo = perfil.saldo
        except PerfilUsuario.DoesNotExist:
            saldo = 0
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name, 
            "saldo": saldo,
        })

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        if not username or not email or not password:
            return Response({"error": "Faltan datos obligatorios"}, status=status.HTPP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({"error": "Nombre de usuario ya existe"}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({"error": "El correo ya está en uso"}, status=status.HTTP_400_BAD_REQUEST)
        
        #crear usuario
        new_user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        #crear perfil con saldo inicial
        PerfilUsuario.objects.get_or_create(
            usuario=new_user,
            defaults={'saldo':500000}
        )

        return Response({"mensaje": "Usuario registrado exitosamente"}, status=status.HTTP_201_CREATED)

class AddCardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        perfil = PerfilUsuario.objects.get(usuario=request.user)

        #Al agregar tarjeta, asignamos el balance inical de 500000
        perfil.saldo = Decimal('500000.00')
        perfil.save()
        return Response({"saldo": perfil.saldo})

class SetLimitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        perfil = PerfilUsuario.objects.get(usuario=request.user)
        new_limit = request.data.get('limite', 0)
        perfil.limite_mensual = Decimal(str(new_limit))
        perfil.save()
        return Response({"limite": perfil.limite_mensual})