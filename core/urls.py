from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import registro, CustomLoginView, home, PerfilUsuario, editar_perfil, ProductoAgregar, ProductoModificar, ProductoListar,\
ProductoEliminar, ProductoReactivar, ProductoDesactivar, optar_a_regalo, MatchesRegalo, optar_a_cambio, MatchesCambio, ConfirmarMatchRegalo,\
ConfirmarMatchCambio, ChatMensajes, ListaChatMatch, valoracion_match, optar_a_venta, descargar_qr,CustomPasswordResetView,CustomPasswordResetDoneView,\
CustomPasswordResetConfirmView,CustomPasswordResetCompleteView, pago_exitoso, pago_fallido, pago_pendiente


urlpatterns = [

    path('', CustomLoginView.as_view(), name='login'),
    path('home/', home, name='home'),
    path('home/<int:postmatch_id>/', home, name='home_with_postmatch'),

    path('registro/', registro, name='registro'),
    path('logout/', LogoutView.as_view(), name='logout'),  # Vista para logout
    path('PerfilUsuario/', PerfilUsuario, name='PerfilUsuario'),
    path('PerfilUsuario/descargar_qr/',descargar_qr, name='descargar_qr'),

    path('editar_perfil/', editar_perfil, name='editar_perfil'), 


    path('producto/agregar/', ProductoAgregar, name='producto_agregar'),
    
    path('ProductoModificar/<int:id>', ProductoModificar, name="ProductoModificar"),
    path('ProductoListar/', ProductoListar, name="ProductoListar"),
    path('ProductoEliminar/<int:id>/', ProductoEliminar, name='ProductoEliminar'),


    path('ProductoReactivar', ProductoReactivar, name="ProductoReactivar"),
    path('ProductoDesactivar', ProductoDesactivar, name="ProductoDesactivar"),


    path('optar-a-regalo/', optar_a_regalo, name='optar_a_regalo'),
    path('optar-a-cambio/', optar_a_cambio, name='optar_a_cambio'),
    path('MatchesRegalo/', MatchesRegalo, name='MatchesRegalo'),
    path('MatchesCambio/', MatchesCambio, name='MatchesCambio'),

    path('ConfirmarMatchRegalo/', ConfirmarMatchRegalo, name='ConfirmarMatchRegalo'),
    path('ConfirmarMatchCambio/', ConfirmarMatchCambio, name='ConfirmarMatchCambio'),


    path('ListaChatMatch/', ListaChatMatch, name='ListaChatMatch'),
    path('ChatMensajes/<int:postmatch_id>/', ChatMensajes, name='ChatMensajes'),
    path('valoracion/<int:postmatch_id>/', valoracion_match, name='valoracion_match'),


    path('optar-a-venta/', optar_a_venta, name='optar_a_venta'),

    path('pago-exitoso/', pago_exitoso, name='pago_exitoso'),
    path('pago-fallido/', pago_fallido, name='pago_fallido'),
    path('pago-pendiente/', pago_pendiente, name='pago_pendiente'),



    # URLs para recuperación de contraseña
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

