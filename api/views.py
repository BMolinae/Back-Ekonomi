from decimal import Decimal
from datetime import timedelta

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string

from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import Movimiento, Categoria, PerfilUsuario
from .serializers import MovimientoSerializer, CategoriaSerializer


class MovimientoViewSet(viewsets.ModelViewSet):
    serializer_class = MovimientoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return Movimiento.objects.filter(usuario=self.request.user)

    def create(self, request, *args, **kwargs):
        # 1) valida y salva el movimiento
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movimiento = serializer.save(usuario=request.user)

        # 2) actualiza perfil
        perfil = PerfilUsuario.objects.get(usuario=request.user)
        if movimiento.tipo == 'ingreso':
            perfil.saldo += movimiento.monto
        else:  # gasto
            perfil.saldo -= movimiento.monto
            perfil.limite_mensual -= movimiento.monto
        perfil.save()

        # 3) arma la respuesta incluyendo los nuevos valores
        data = serializer.data
        data.update({
            "saldo": str(perfil.saldo),
            "limite_mensual": str(perfil.limite_mensual)
        })
        return Response(data, status=status.HTTP_201_CREATED)


class CategoriaListCreateView(generics.ListCreateAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = []


def vista_movimientos_html(request):
    return render(request, 'movimientos.html')


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        user = request.user
        perfil, _ = PerfilUsuario.objects.get_or_create(
            usuario=user,
            defaults={
                'saldo': Decimal('0.00'),
                'limite_mensual': Decimal('0.00')
            }
        )
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "saldo": perfil.saldo,
            "limite_mensual": perfil.limite_mensual,
            "tarjeta": perfil.tarjeta
        })


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

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

        new_user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        PerfilUsuario.objects.get_or_create(
            usuario=new_user,
            defaults={
                'saldo': Decimal('0.00'),
                'limite_mensual': Decimal('0.00')
            }
        )

        token, _ = Token.objects.get_or_create(user=new_user)

        return Response({
            "token": token.key,
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email
            }
        }, status=status.HTTP_201_CREATED)


class AddCardView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        perfil = PerfilUsuario.objects.get(usuario=request.user)
        card_number = request.data.get('cardNumber')
        perfil.tarjeta = card_number
        perfil.saldo += Decimal('500000.00')
        perfil.save()

        Movimiento.objects.create(
            usuario=request.user,
            tipo='ingreso',
            descripcion='Saldo inicial al agregar tarjeta',
            monto=perfil.saldo
        )

        return Response({"saldo": perfil.saldo, "tarjeta": perfil.tarjeta})


class SetLimitView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        perfil = PerfilUsuario.objects.get(usuario=request.user)
        new_limit = request.data.get('limite')

        try:
            perfil.limite_mensual = Decimal(str(new_limit))
            perfil.save()
        except (TypeError, ValueError, Decimal.InvalidOperation):
            return Response(
                {"error": "Límite inválido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"limite": perfil.limite_mensual})


class RecoverPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {'status': 'Error', 'message': 'Email requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            token = get_random_string(length=32)
            perfil = user.perfilusuario
            perfil.reset_token = token
            perfil.token_created_at = timezone.now()
            perfil.save()

            recovery_link = f"http://localhost:8100/reset-password?token={token}"
            # Aquí podrías enviar el email con recovery_link
            return Response(
                {'status': 'Success', 'recoveryLink': recovery_link},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'status': 'Error', 'message': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        perfil = get_object_or_404(PerfilUsuario, reset_token=token)

        # Verifica que no hayan pasado más de 1 hora
        if perfil.token_created_at + timedelta(hours=1) < timezone.now():
            return Response(
                {'error': 'Token expirado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = perfil.usuario
        user.set_password(new_password)
        user.save()

        # Limpia el token para que no se use de nuevo
        perfil.reset_token = None
        perfil.token_created_at = None
        perfil.save()

        return Response(
            {'status': 'success'},
            status=status.HTTP_200_OK
        )