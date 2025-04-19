# api/views.py

from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Movimiento, Categoria, PerfilUsuario
from .serializers import MovimientoSerializer, CategoriaSerializer


class MovimientoViewSet(viewsets.ModelViewSet):
    """
    CRUD de movimientos del usuario autenticado.
    """
    serializer_class = MovimientoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        # Solo los movimientos de este usuario
        return Movimiento.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        # Al crear un movimiento, lo relacionamos con el usuario
        serializer.save(usuario=self.request.user)


class CategoriaListCreateView(generics.ListCreateAPIView):
    """
    Lista y crea categorías (sin autenticación).
    """
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = []


def vista_movimientos_html(request):
    """
    Vista HTML para ver movimientos (solo para testing).
    """
    return render(request, 'movimientos.html')


class CurrentUserView(APIView):
    """
    Devuelve datos del usuario autenticado: usuario + saldo + límite.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        user = request.user

        # Obtener o crear perfil si faltara
        perfil, _ = PerfilUsuario.objects.get_or_create(
            usuario=user,
            defaults={'saldo': Decimal('0.00'), 'limite_mensual': Decimal('0.00')}
        )

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "saldo": perfil.saldo,
            "limite_mensual": perfil.limite_mensual,
        })


class RegisterView(APIView):
    """
    Registro de nuevos usuarios y creación de perfil con saldo inicial.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username   = request.data.get('username')
        email      = request.data.get('email')
        password   = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name  = request.data.get('last_name', '')

        # Validaciones básicas
        if not username or not email or not password:
            return Response(
                {"error": "Faltan datos obligatorios."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Nombre de usuario ya existe."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "El correo ya está en uso."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crear usuario
        new_user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Crear perfil con saldo inicial = 0 y límite inicial = 0
        PerfilUsuario.objects.create(
            usuario=new_user,
            saldo=Decimal('0.00'),
            limite_mensual=Decimal('0.00')
        )

        return Response(
            {"mensaje": "Usuario registrado exitosamente."},
            status=status.HTTP_201_CREATED
        )


class AddCardView(APIView):
    """
    Al agregar tarjeta, asigna el saldo inicial de 500000 y crea un movimiento de ingreso.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        perfil = PerfilUsuario.objects.get(usuario=request.user)

        # 1) Asignar saldo inicial
        perfil.saldo = Decimal('500000.00')
        perfil.save()

        # 2) Registrar movimiento de tipo ingreso
        Movimiento.objects.create(
            usuario=request.user,
            tipo='ingreso',
            descripcion='Saldo inicial al agregar tarjeta',
            monto=perfil.saldo
        )

        return Response({"saldo": perfil.saldo})


class SetLimitView(APIView):
    """
    Establece el límite mensual de gasto en el perfil.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        perfil = PerfilUsuario.objects.get(usuario=request.user)
        new_limit = request.data.get('limite')

        try:
            # Convertir a Decimal y asignar
            perfil.limite_mensual = Decimal(str(new_limit))
            perfil.save()
        except (TypeError, ValueError, Decimal.InvalidOperation):
            return Response(
                {"error": "Límite inválido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"limite": perfil.limite_mensual})
