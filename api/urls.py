from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AddCardView, CurrentUserView, MovimientoViewSet, CategoriaListCreateView, RegisterView, SetLimitView, vista_movimientos_html

router = DefaultRouter()
router.register(r'movimientos', MovimientoViewSet, basename='movimientos')

urlpatterns = [
    path('', include(router.urls)),
    path('categorias/', CategoriaListCreateView.as_view(), name='categoria-list-create'),
    path('movimientos/', vista_movimientos_html, name='vista-movimientos-html'),
    path('user/', CurrentUserView.as_view(), name='current_user'),
    path('register/', RegisterView.as_view(), name='register'),
    path('add-card/', AddCardView.as_view(), name='add_card'),
    path('set-limit/', SetLimitView.as_view(), name='set_limit'),
    path('movimientos-html/', vista_movimientos_html, name='vista-movimientos-html'),
] 