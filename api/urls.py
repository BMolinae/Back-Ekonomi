from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MovimientoViewSet, CategoriaListCreateView, vista_movimientos_html

router = DefaultRouter()
router.register(r'movimientos', MovimientoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('categorias/', CategoriaListCreateView.as_view(), name='categoria-list-create'),
    path('movimientos/', vista_movimientos_html, name='vista-movimientos-html'),
]