from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.mail import send_mail
from decimal import Decimal
from django.db.models import Sum

from .models import PerfilUsuario, Movimiento


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance, saldo=0)


@receiver(post_save, sender=Movimiento)
def actualizar_saldo_al_crear_movimiento(sender, instance, created, **kwargs):
    if not created:
        return
    perfil = instance.usuario.perfilusuario
    if instance.tipo == 'ingreso':
        perfil.saldo += instance.monto
    else:
        perfil.saldo -= instance.monto
    perfil.save()


@receiver(post_delete, sender=Movimiento)
def revertir_saldo_al_borrar_movimiento(sender, instance, **kwargs):
    perfil = getattr(instance.usuario, 'perfilusuario', None)
    if not perfil:
        return

    if instance.tipo == 'gasto':
        perfil.saldo += instance.monto
    elif instance.tipo == 'ingreso':
        perfil.saldo -= instance.monto

    perfil.save()


@receiver(post_save, sender=Movimiento)
def enviar_alerta_gasto(sender, instance, created, **kwargs):
    if not created or instance.tipo != 'gasto':
        return

    perfil = getattr(instance.usuario, 'perfilusuario', None)
    if not perfil or not perfil.limite_mensual:
        return

    hoy = timezone.now()
    inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Total de gastos ANTES del movimiento actual
    gastos_previos = Movimiento.objects.filter(
        usuario=instance.usuario,
        tipo='gasto',
        fecha__gte=inicio_mes
    ).exclude(id=instance.id).aggregate(total=Sum('monto'))['total'] or Decimal('0')

    # Total actual (después de incluir el movimiento recién creado)
    gastos_actuales = gastos_previos + instance.monto
    limite = perfil.limite_mensual

    porc_anterior = (gastos_previos / limite) * 100
    porc_actual = (gastos_actuales / limite) * 100

    if porc_anterior < 50 <= porc_actual:
        enviar_correo_alerta(perfil.usuario.email, '📊 Has alcanzado el 50% de tu límite mensual.')
    elif porc_anterior < 90 <= porc_actual:
        enviar_correo_alerta(perfil.usuario.email, '⚠️ Te queda menos del 10% de tu límite mensual.')

def enviar_correo_alerta(destinatario, mensaje):
    send_mail(
        subject='Alerta de gasto mensual - Ekonomi',
        message=mensaje,
        from_email=None,  # usa DEFAULT_FROM_EMAIL desde settings.py
        recipient_list=[destinatario],
        fail_silently=False,
    )
