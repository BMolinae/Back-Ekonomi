# api/signals.py

from decimal import Decimal
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import PerfilUsuario, Movimiento

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance, saldo=0)


@receiver(post_save, sender=Movimiento)
def update_perfil_on_save(sender, instance, created, **kwargs):
    perfil = PerfilUsuario.objects.get(usuario=instance.usuario)

    # Solo al crear mov nuevo
    if created:
        if instance.tipo == 'ingreso':
            perfil.saldo += instance.monto
        else:  # gasto
            perfil.saldo -= instance.monto
            perfil.limite_mensual -= instance.monto
        perfil.save()

@receiver(post_delete, sender=Movimiento)
def update_perfil_on_delete(sender, instance, **kwargs):
    perfil = PerfilUsuario.objects.get(usuario=instance.usuario)

    # Al borrar, revertimos el efecto
    if instance.tipo == 'ingreso':
        perfil.saldo -= instance.monto
    else:
        perfil.saldo += instance.monto
        perfil.limite_mensual += instance.monto
    perfil.save()