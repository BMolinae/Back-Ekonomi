# api/signals.py

from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import PerfilUsuario, Movimiento

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance, saldo=0)

@receiver(post_save, sender=Movimiento)
def actualizar_perfil_al_crear_movimiento(sender, instance, created, **kwargs):
    if not created:
        return
    perfil = instance.usuario.perfilusuario
    if instance.tipo == 'ingreso':
        perfil.saldo += instance.monto
    else:  # gasto
        perfil.saldo -= instance.monto
        perfil.limite_mensual -= instance.monto
    perfil.save()
