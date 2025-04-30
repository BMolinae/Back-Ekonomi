from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from .views import (
    AddCardView,
    CurrentUserView,
    MovimientoViewSet,
    CategoriaListCreateView,
    RegisterView,
    SetLimitView,
    vista_movimientos_html,
    RecoverPasswordView,
    ResetPasswordView,
    DocumentView
)

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
    path('token-auth/', obtain_auth_token, name='api_token_auth'),
    path('recover-password/', RecoverPasswordView.as_view(), name='recover-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('documents/<str:type>/', DocumentView.as_view(), name='documents'),
    

]
