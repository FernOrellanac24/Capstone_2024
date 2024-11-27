# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin  # Importa el UserAdmin de Django para personalizar la administración de usuarios
from .models import Account, Categoria, NuevoProducto, Tags, TipoTrans, TagsPublicacion, MatchProductoRegalo, MatchProductoCambio, Mensajes, MatchValoracion

# Clase personalizada para la administración del modelo Account en el panel de administración
class AccountAdmin(UserAdmin):

    # Campos que se mostrarán en la lista de usuarios en el panel de administración
    list_display = ('email', 'nombre', 'apellido', 'rut_usuario', 'is_admin', 'is_staff', 'is_superuser')
    # Campos por los que se podrá buscar en el panel de administración
    search_fields = ('email', 'nombre', 'apellido', 'rut_usuario')
    # Filtros laterales que se mostrarán en la interfaz de administración
    list_filter = ('is_admin', 'is_staff', 'is_active', 'is_superuser')

    # Organización de los campos en el formulario de edición de usuarios
    fieldsets = (
        (None, {'fields': ('email', 'password')}), # Email y contraseña (campos esenciales)
        ('Información Personal', {'fields': ('nombre', 'apellido', 'rut_usuario')}), # Información personal del usuario
        ('Permisos', {'fields': ('is_admin', 'is_staff', 'is_superuser', 'is_active')}), # Permisos y estados del usuario
        ('Fechas Importantes', {'fields': ('last_login',)}), # Fecha de último login
    )

    # Campos que se mostrarán al agregar un nuevo usuario en el panel de administración
    add_fieldsets = (
        (None, {
            'classes': ('wide',), # Hace que los campos sean más anchos en la interfaz de administración
            'fields': ('email', 'nombre', 'apellido', 'rut_usuario', 'password1', 'password2'), # Campos necesarios para crear un usuario
        }),
    )

    # Ordenamiento de los usuarios por el campo 'email'
    ordering = ('email',)

# Registro del modelo Account con su correspondiente clase de administración personalizada# Asegúrate de registrar el modelo y el admin correctamente
admin.site.register(Account, AccountAdmin)
admin.site.register(Categoria)
admin.site.register(NuevoProducto)
admin.site.register(TipoTrans)
admin.site.register(Tags)
admin.site.register(TagsPublicacion)
admin.site.register(MatchProductoRegalo)
admin.site.register(MatchProductoCambio)
admin.site.register(Mensajes)
admin.site.register(MatchValoracion)



