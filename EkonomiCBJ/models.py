from django.db import models
from django.contrib.auth.models import User

class Cuenta(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f'Cuenta de {self.usuario.username}'

class Transaccion(models.Model):
    TIPO_CHOICES = [
        ('ingreso', 'Ingreso'),
        ('gasto', 'Gasto'),
    ]

    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='transacciones')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.tipo} de {self.monto}'
