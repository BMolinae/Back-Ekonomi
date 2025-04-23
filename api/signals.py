# api/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User

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
    # solo actualizamos el saldo, NO el límite
    if instance.tipo == 'ingreso':
        perfil.saldo += instance.monto
    else:  # gasto
        perfil.saldo -= instance.monto
    perfil.save()

@receiver(post_delete, sender=Movimiento)
def revertir_saldo_al_borrar_movimiento(sender, instance, **kwargs):
    perfil = instance.usuario.perfilusuario
    # al borrar, revertimos solo el saldo
    if instance.tipo == 'ingreso':
        perfil.saldo -= instance.monto
    else:
        perfil.saldo += instance.monto
    perfil.save()
