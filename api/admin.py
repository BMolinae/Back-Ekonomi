# admin.py

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from api.models import PerfilUsuario, Categoria, Movimiento
class CustomUserAdmin(UserAdmin):
    def delete_model(self, request, obj):
        try:
            obj.perfilusuario.delete()
        except PerfilUsuario.DoesNotExist:
            pass
        obj.delete()

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Categoria)
admin.site.register(Movimiento)
