from decimal import Decimal
from datetime import timedelta
from datetime import datetime

from io import BytesIO, StringIO
import logging
import csv

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.http import FileResponse
from django.conf import settings

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from django.http import HttpResponse

from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import Movimiento, Categoria, PerfilUsuario
from .serializers import MovimientoSerializer, CategoriaSerializer

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader


import os
from django.conf import settings


# Configuramos logger
logger = logging.getLogger(__name__)


from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from datetime import datetime

def generate_monthly_pdf(user):
    buf = BytesIO()
    try:
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4

        # 🖼 Logo + Encabezado
        logo_path = os.path.join(settings.BASE_DIR, "api", "static", "img", "logoEmpresa.jpeg")
        logo_width = 100
        logo_height = 60
        logo_y = h - 80

        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            c.drawImage(logo, x=40, y=logo_y, width=logo_width, height=logo_height, mask='auto')

        # 📄 Texto de encabezado a la derecha
        text_x = 160
        text_y = h - 40

        c.setFont("Helvetica-Bold", 18)
        c.drawString(text_x, text_y, "Informe mensual")
        c.setFont("Helvetica", 12)
        c.drawString(text_x, text_y - 20, f"Usuario: {user.username}")
        c.drawString(text_x, text_y - 40, f"Fecha de emisión: {datetime.now():%d/%m/%Y}")

        # Línea divisoria
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.5)
        c.line(40, text_y - 60, w - 40, text_y - 60)

        # 💰 Saldo
        saldo = getattr(user.perfilusuario, 'saldo', 0)
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.black)
        c.drawString(40, text_y - 90, f"Saldo actual: CLP {saldo:,.0f}".replace(',', '.'))

        # 🧾 Transacciones
        c.setFont("Helvetica-Bold", 13)
        c.drawString(40, text_y - 120, "Transacciones recientes")

        movimientos = user.movimiento_set.order_by('-fecha')[:5]
        data = [["Fecha", "Tipo", "Monto", "Descripción"]]
        for m in movimientos:
            data.append([
                m.fecha.strftime("%d/%m/%Y"),
                m.tipo.capitalize(),
                f"CLP {int(m.monto):,}".replace(',', '.'),
                m.descripcion
            ])

        table = Table(data, colWidths=[80, 80, 100, 260])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2656bf")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        table.wrapOn(c, w, h)
        table.drawOn(c, x=40, y=text_y - 320)

        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(colors.grey)
        c.drawString(40, 40, "CB&J Ekonomi © 2025 – Documento generado automáticamente.")

        # 📄 Página 2: Gráficos
        c.showPage()

        graficos = ['gauge', 'pie', 'line']
        titles = ['Uso del límite mensual', 'Distribución de gastos', 'Comparación mensual']
        x_pos = 40
        y_pos = h - 100
        img_width = 240
        img_height = 240

        for idx, chart_id in enumerate(graficos):
            chart_buf = generate_chart_png(user, chart_id)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(x_pos, y_pos + 10, titles[idx])
            c.drawImage(ImageReader(chart_buf), x_pos, y_pos - img_height,
                        width=img_width, height=img_height, mask='auto')

            if idx == 1:
                x_pos = 40
                y_pos -= img_height + 100
            else:
                x_pos += img_width + 40

        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(colors.grey)
        c.drawString(40, 40, "Gráficos generados automáticamente a partir de tus movimientos.")

        c.save()
        buf.seek(0)
        return buf

    except Exception:
        logger.exception("Error generando PDF mensual")
        raise


def generate_csv(user):
    try:
        txt_buf = StringIO(newline='')
        writer = csv.writer(txt_buf, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        # 📄 Resumen al inicio
        saldo = getattr(user.perfilusuario, 'saldo', 0)
        writer.writerow([f"Informe mensual de {user.username}"])
        writer.writerow([f"Saldo disponible: CLP {saldo:,}".replace(',', '.')])
        writer.writerow([])

        # 🧾 Encabezados
        writer.writerow(["Fecha", "Tipo", "Monto (CLP)", "Descripción"])

        for m in user.movimiento_set.order_by('fecha'):
            writer.writerow([
                m.fecha.strftime("%d/%m/%Y"),
                m.tipo.capitalize(),
                f"{int(m.monto):,}".replace(',', '.'),
                m.descripcion
            ])

        # 📦 Convertimos a bytes
        csv_bytes = txt_buf.getvalue().encode('utf-8-sig')  # BOM para Excel en Windows
        byte_buf = BytesIO(csv_bytes)
        byte_buf.seek(0)
        return byte_buf

    except Exception:
        logger.exception("Error generando CSV de transacciones")
        raise


def generate_chart_png(user, chart_id):
    buf = BytesIO()
    try:
        from collections import defaultdict
        import calendar
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(4, 4))
        perfil = user.perfilusuario
        movimientos = user.movimiento_set.all()

        if chart_id == 'gauge':
            limite = float(perfil.limite_mensual or 0)
            gastos = sum(float(abs(m.monto)) for m in movimientos if m.tipo == 'gasto')
            porcentaje_usado = int((gastos / limite) * 100) if limite > 0 else 0
            porcentaje_restante = 100 - porcentaje_usado
            ax.pie(
                [porcentaje_usado, porcentaje_restante],
                startangle=90,
                colors=['#ef476f', '#e0e0e0'],
                wedgeprops={'width': 0.4}
            )
            ax.text(0, 0, f"{porcentaje_usado}%", ha='center', va='center', fontsize=16)
            ax.set_title("Uso del límite mensual")

        elif chart_id == 'pie':
            categorias = defaultdict(float)
            for m in movimientos:
                if m.tipo == 'gasto' and m.categoria:
                    categorias[m.categoria.nombre] += float(abs(m.monto))

            if not categorias:
                categorias['Sin datos'] = 1

            ax.pie(
                categorias.values(),
                labels=categorias.keys(),
                autopct='%1.1f%%',
                startangle=90
            )
            ax.set_title("Distribución de gastos")

        elif chart_id == 'line':
            import calendar
            from datetime import datetime, timedelta
            from collections import OrderedDict

            hoy = datetime.now()
            # Obtener últimos 4 meses (mes y año)
            ultimos_4 = []
            for i in range(3, -1, -1):
                mes = (hoy.month - i - 1) % 12 + 1
                año = hoy.year if hoy.month - i > 0 else hoy.year - 1
                ultimos_4.append((año, mes))

            labels = [calendar.month_name[mes][:3] for (año, mes) in ultimos_4]
            ingresos = OrderedDict.fromkeys(ultimos_4, 0)
            gastos = OrderedDict.fromkeys(ultimos_4, 0)

            for m in movimientos:
                clave = (m.fecha.year, m.fecha.month)
                if clave in ingresos:
                    if m.tipo == 'ingreso':
                        ingresos[clave] += float(m.monto)
                    elif m.tipo == 'gasto':
                        gastos[clave] += float(m.monto)

            ingresos_valores = list(ingresos.values())
            gastos_valores = list(gastos.values())

            ax.plot(labels, ingresos_valores, marker='o', label='Ingresos', color='#00bfa6', linewidth=2.5)
            ax.plot(labels, gastos_valores, marker='o', label='Gastos', color='#ff6b6b', linewidth=2.5)

            ax.set_title("Comparación mensual")
            ax.set_xlabel("Mes")
            ax.set_ylabel("Monto (CLP)")
            ax.grid(True)
            ax.legend()



        else:
            ax.text(0.5, 0.5, "Gráfico no disponible", ha='center')

        fig.tight_layout()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf

    except Exception:
        logger.exception(f"Error generando PNG para '{chart_id}'")
        raise


class DocumentView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, type, format=None):
        try:
            if type == 'monthly':
                buf = generate_monthly_pdf(request.user)
                return FileResponse(buf, filename='informe_mensual.pdf', as_attachment=True)

            if type == 'csv':
                buf = generate_csv(request.user)
                return FileResponse(buf, filename='transacciones.csv', as_attachment=True)

            if type in ('gauge', 'pie', 'line'):
                buf = generate_chart_png(request.user, type)
                return FileResponse(buf, filename=f'{type}.png', as_attachment=True)

            return Response({'detail': 'Tipo no soportado.'}, status=404)

        except Exception:
            logger.exception(f"Fallo en DocumentView para '{type}'")
            return Response({'detail': 'Error interno al generar el documento.'}, status=500)
        
class MovimientoViewSet(viewsets.ModelViewSet):
    serializer_class = MovimientoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return Movimiento.objects.filter(usuario=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movimiento = serializer.save(usuario=request.user)

        #  Solo actualizamos el saldo, no tocamos limite_mensual
        perfil = PerfilUsuario.objects.get(usuario=request.user)

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
        added_amount = Decimal('500000.00')

        # Asigna la tarjeta (pero NO toques aquí el saldo)
        perfil.tarjeta = card_number
        perfil.save()

        # Crea un movimiento de INGRESO de 500k
        Movimiento.objects.create(
            usuario=request.user,
            tipo='ingreso',
            descripcion='Saldo inicial al agregar tarjeta',
            monto=added_amount
        )

        # La señal `post_save` se encargará de sumar esos 500k al perfil
        perfil.refresh_from_db()
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

            recovery_link = f"https://ekonomi-reset-production.up.railway.app?token={token}"
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
