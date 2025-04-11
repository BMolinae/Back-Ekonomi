from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Movimiento(models.Model):
    TIPO_CHOICES = [
        ('ingreso', 'Ingreso'),
        ('gasto', 'Gasto'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    descripcion = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
       return f'{self.tipo} - {self.descripcion} - {self.monto}' 

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=[('ingreso', 'Ingreso'), ('gasto', 'Gasto')])

    def __str__(self):
        return self.nombre