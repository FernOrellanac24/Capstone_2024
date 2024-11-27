# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth import get_user_model
from core.validators import validar_rut  # Asegúrate de que la ruta sea correcta
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

# Manager personalizado para manejar la creación de usuarios y superusuarios
class MyAccountManager(BaseUserManager):

    # Método para crear un usuario estándar
    def create_user(self, email, nombre, apellido, rut_usuario, password=None, **extra_fields):
        if not email:
            raise ValueError('El email debe ser proporcionado')
        email = self.normalize_email(email)
        
        # Validar RUT antes de crear el usuario
        #if not validar_rut(rut_usuario):
            #raise ValueError('El RUT proporcionado no es válido')
        
        # Crear el usuario con los campos proporcionados
        user = self.model(email=email, nombre=nombre, apellido=apellido, rut_usuario=rut_usuario, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # Método para crear un superusuario (admin con todos los permisos)
    def create_superuser(self, email, nombre, apellido, rut_usuario, password=None, **extra_fields):
        
        # Establece por defecto los permisos de superusuario
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, nombre, apellido, rut_usuario, password, **extra_fields)

# Modelo de usuario personalizado
class Account(AbstractBaseUser, PermissionsMixin):

    # Definición de los campos para el usuario
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    nombre = models.CharField(verbose_name='nombre', max_length=50, unique=False)
    apellido = models.CharField(verbose_name='apellido', max_length=50, unique=False)
    rut_usuario = models.CharField(verbose_name='rut_usuario', max_length=20, unique=True)
    profile_image   = models.ImageField(max_length=255, null=True, blank=True)
    
    # Campos de estado del usuario
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # Relación con los permisos y grupos (de 'auth')
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='user_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='user_set',
        related_query_name='user',
    )

    # Asocia el modelo con el manager personalizado
    objects = MyAccountManager()

    # Define el campo que se utilizará para loguearse (aquí es el email en lugar de username)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido', 'rut_usuario'] # Campos obligatorios además del email

    # Método para retornar la representación en string del usuario (su email)
    def __str__(self):
        return self.email
    
    # Método que limpia y valida el modelo antes de guardarlo
    #def clean(self):
        #super().clean()# Llama al método clean original
        # Validar RUT aquí también, en caso de que se use save en lugar de create_user
        
        #if not validar_rut(self.rut_usuario):
            #raise ValueError('El RUT proporcionado no es válido')# Levanta un error si el RUT no es válido


class Categoria(models.Model):
    nombreCategoria = models.CharField(max_length=60)

    def __str__(self):
        return self.nombreCategoria

class TipoTrans(models.Model):
    nombreTrans = models.CharField(max_length=30)

    def __str__(self):
        return self.nombreTrans

class Tags(models.Model):
    nombreTags = models.CharField(max_length=90)
    categoriaTags = models.ForeignKey(Categoria, on_delete=models.PROTECT,  null=True)

    def __str__(self):
        return self.nombreTags
    


class NuevoProducto(models.Model):
    p_nombre = models.CharField(max_length=60)
    p_img = models.ImageField(null=True)
    p_descripcion = models.TextField(null=True)
    p_tipoTrans = models.ForeignKey(TipoTrans, on_delete=models.PROTECT, null=True)
    p_categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, null=True)
    p_tags = models.ForeignKey(Tags, on_delete=models.PROTECT, null=True)
    p_account_email = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, null=True)
    p_habilitar = models.IntegerField(choices=[(0, 'deshabilitado'), (1, 'habilitado')], default=1)
    p_precio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Campo para el precio

    def save(self, *args, **kwargs):
        # Verifica si el tipo de transacción es "Venta" y si el precio es None
        if self.p_tipoTrans and self.p_tipoTrans.nombreTrans == "Venta" and self.p_precio is None:
            raise ValidationError("El precio es obligatorio para productos de venta.")
        super().save(*args, **kwargs)  # Llama al método save del padre

    def __str__(self):
        return self.p_nombre


    

class TagsPublicacion(models.Model):
    idPublicacion = models.ForeignKey(NuevoProducto, on_delete=models.PROTECT)
    tagPublicacion = models.ForeignKey(Tags, on_delete=models.CASCADE)

    def __str__(self):
        return f"Publicación: {self.idPublicacion.p_nombre} - Tag: {self.tagPublicacion.nombreTags}"
    

class MatchProductoRegalo(models.Model):
    PostMatch = models.AutoField(primary_key=True)
    fecha_propuesta = models.DateTimeField(auto_now_add=True)
    producto = models.ForeignKey(NuevoProducto, on_delete=models.CASCADE, related_name='matches_producto')
    usuario_dueño = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='matches_dueno')
    usuario_solicitante = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='matches_solicitante')
    estado_solicitud = models.IntegerField(choices=[(0, 'Inactivo'), (1, 'Activo')], default=1)
    confirmacion_match = models.IntegerField(choices=[(0, 'No confirmado'), (1, 'Confirmado')], default=0)

    def __str__(self):
        return f'ID: {self.PostMatch} - Producto: {self.producto.p_nombre}'
    


class MatchProductoCambio(models.Model):
    PostMatch = models.AutoField(primary_key=True)
    fecha_propuesta = models.DateTimeField(auto_now_add=True)
    producto = models.ForeignKey(NuevoProducto, on_delete=models.CASCADE, related_name='matches_cambio_producto')
    producto_propuesto = models.ForeignKey(NuevoProducto, on_delete=models.CASCADE, related_name='matches_cambio_propuesto', null=True, blank=True)
    usuario_dueño = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='matches_cambio_dueno')
    usuario_solicitante = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='matches_cambio_solicitante')
    estado_solicitud = models.IntegerField(choices=[(0, 'Inactivo'), (1, 'Activo')], default=1)
    confirmacion_match = models.IntegerField(choices=[(0, 'No confirmado'), (1, 'Confirmado')], default=0)

    def save(self, *args, **kwargs):
        if not self.PostMatch:
            max_postmatch = MatchProductoCambio.objects.aggregate(models.Max('PostMatch'))['PostMatch__max']
            self.PostMatch = max(max_postmatch + 1, 9000) if max_postmatch is not None else 9000
        super().save(*args, **kwargs)

    def __str__(self):
        return f'ID: {self.PostMatch} - Producto: {self.producto.p_nombre}'
    



class Mensajes(models.Model):
    usuarioPost = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='UsuarioPosteo')
    mensajePost = models.TextField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)  # Cambia a null=True
    object_id = models.PositiveIntegerField(null=True)  # Cambia a null=True
    content_object = GenericForeignKey('content_type', 'object_id')  # Esto es opcional, pero útil

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Mensaje de {self.usuarioPost} el {self.created_at}'

    class Meta:
        ordering = ['created_at']



from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

class MatchValoracion(models.Model):
    id = models.AutoField(primary_key=True)
    valormatch = models.IntegerField(choices=[(1, '1 estrella'), (2, '2 estrellas'), (3, '3 estrellas'), 
                                               (4, '4 estrellas'), (5, '5 estrellas')])
    dueño_producto = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='valoraciones_dueño')
    evaluador = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='valoraciones_evaluador')

    # Campos genéricos
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    postmatch = GenericForeignKey('content_type', 'object_id')

    opinion = models.TextField(null=True)

    class Meta:
        verbose_name = 'Valoración de Match'
        verbose_name_plural = 'Valoraciones de Matches'
        constraints = [
            models.UniqueConstraint(
                fields=['dueño_producto', 'evaluador', 'content_type', 'object_id'],
                name='unique_valoracion_match'
            )
        ]

    def __str__(self):
        return f'Valoración de {self.evaluador} a {self.dueño_producto} con {self.valormatch} estrellas'

    def calcular_promedio(self):
        # Calcular el promedio de valoraciones para este objeto
        valoraciones = MatchValoracion.objects.filter(
            content_type=self.content_type, object_id=self.object_id
        )
        promedio = valoraciones.aggregate(models.Avg('valormatch'))
        return promedio.get('valormatch__avg', 0)  # Devuelve el promedio o 0 si no hay valoraciones

