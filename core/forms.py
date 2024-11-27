from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from .models import Account, Categoria, TipoTrans, Tags, NuevoProducto, MatchProductoRegalo, MatchValoracion
from core.validators import validar_rut  # Asegúrate de que la ruta sea correcta
from django.utils.safestring import mark_safe

class RegistroForm(UserCreationForm):
    email = forms.EmailField(max_length=60, help_text='Se requiere un email válido')
    nombre = forms.CharField(max_length=50)
    apellido = forms.CharField(max_length=50)
    rut_usuario = forms.CharField(max_length=20, help_text="Introduce un RUT válido")

    class Meta:
        model = Account
        fields = ('email', 'nombre', 'apellido', 'rut_usuario', 'password1', 'password2')  # Campos a mostrar en el formulario

    #def clean_rut_usuario(self):
        #rut = self.cleaned_data.get('rut_usuario')
        #if not validar_rut(rut):  # Validación adicional del RUT
            #raise forms.ValidationError("El RUT ingresado no es válido.")
        #return rut

    
class LoginForm(AuthenticationForm):
    username = forms.EmailField(max_length=60, label="Email", help_text="Introduce tu email")
    
    # El campo username se personaliza para que sea el email
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'
        self.fields['username'].widget.attrs['placeholder'] = 'Email'
        self.fields['password'].widget.attrs['placeholder'] = 'Contraseña'


class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = Account  # Asegúrate de que tu modelo sea Account
        fields = ['profile_image']


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs['placeholder'] = 'Contraseña actual'




class NuevoProductoForm(forms.ModelForm):

    class Meta:
        model = NuevoProducto
        fields = [
            'p_nombre',
            'p_img',
            'p_tipoTrans',
            'p_descripcion',
            'p_categoria',
            'p_tags',
            'p_precio'  # Asegúrate de incluir el campo de precio
        ]
        widgets = {
            'p_img': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'p_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'p_descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'p_tipoTrans': forms.Select(attrs={'class': 'form-control', 'id': 'id_p_tipoTrans'}),  # Asegúrate de que el ID coincida
            'p_categoria': forms.Select(attrs={'class': 'form-control'}),
            'p_tags': forms.Select(attrs={'class': 'form-control'}),
            'p_precio': forms.NumberInput(attrs={'class': 'form-control'}),  # Ocultar por defecto
        }

    def clean(self):
        cleaned_data = super().clean()
        p_tipoTrans = cleaned_data.get('p_tipoTrans')
        p_precio = cleaned_data.get('p_precio')

        # Validación del campo precio
        if p_tipoTrans and p_tipoTrans.id == 3:  # Verifica por el ID
            if p_precio is None or p_precio == '':
                self.add_error('p_precio', "El precio es obligatorio para productos de venta.")
            elif p_precio <= 0:
                self.add_error('p_precio', "El precio debe ser mayor que cero.")

        return cleaned_data



class ModificarProductoForm(forms.ModelForm):
    class Meta:
        model = NuevoProducto
        fields = [
            'p_nombre',
            'p_img',
            'p_tipoTrans',
            'p_descripcion',
            'p_categoria',
            'p_tags',
            'p_precio'  # Asegúrate de incluir el campo de precio
        ]
        labels = {
            'p_nombre': 'Modifica el título de tu publicación',
            'p_img': 'Cambia la imagen precargada',
            'p_tipoTrans': 'Selecciona o cambia el tipo de transacción a realizar:',
            'p_descripcion': 'Ingresa o cambia la descripción (máximo 300 caracteres)',
            'p_categoria': 'Selecciona o cambia la categoría para tu producto:',
            'p_tags': 'Selecciona los tags asociados a tu publicación:',
            'p_precio': 'Precio del producto (solo si es venta)'  # Etiqueta para el precio
        }
        widgets = {
            'p_nombre': forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 98%;'}),
            'p_img': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'p_tipoTrans': forms.Select(attrs={'class': 'form-control-check', 'id': 'tipoTrans'}),
            'p_descripcion': forms.Textarea(attrs={'class': 'form-control-wider-textarea', 'rows': 5, 'style': 'width: 98%;'}),
            'p_categoria': forms.Select(attrs={'class': 'form-control-check'}),
            'p_tags': forms.Select(attrs={'class': 'form-control-check'}),
            'p_precio': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el precio ', 'style': 'display:none;'})  # Ocultar por defecto
        }

    def clean(self):
        cleaned_data = super().clean()
        p_tipoTrans = cleaned_data.get('p_tipoTrans')
        p_precio = cleaned_data.get('p_precio')

        # Validación del campo precio
        if p_tipoTrans and p_tipoTrans.nombreTrans == "Venta":
            if p_precio is None or p_precio == '':
                self.add_error('p_precio', "El precio es obligatorio para productos de venta.")
            elif p_precio <= 0:
                self.add_error('p_precio', "El precio debe ser mayor que cero.")

        return cleaned_data




class OptarARegaloForm(forms.Form):
    producto_id = forms.IntegerField(widget=forms.HiddenInput())
    usuario_dueño = forms.IntegerField(widget=forms.HiddenInput()) 

class OptarACambioForm(forms.Form):
    producto_id = forms.IntegerField(widget=forms.HiddenInput())
    usuario_dueño = forms.IntegerField(widget=forms.HiddenInput())
    producto_propuesto_id = forms.IntegerField(required=False, widget=forms.HiddenInput())  # Ahora es opcional

    def clean(self):
        cleaned_data = super().clean()
        producto_id = cleaned_data.get('producto_id')
        producto_propuesto_id = cleaned_data.get('producto_propuesto_id')

        # Validar `producto_propuesto_id` solo si es necesario
        # Aquí no lanzaremos error si falta `producto_propuesto_id`
        if producto_id is None:
            self.add_error('producto_id', 'Este campo es requerido.')

        return cleaned_data


class MensajeForm(forms.Form):
    mensaje = forms.CharField(
        label='Mensaje',
        widget=forms.Textarea(attrs={'placeholder': 'Escribe tu mensaje', 'class': 'form-control'}),
        max_length=500,
        error_messages={
            'required': 'Este campo es obligatorio.',
            'max_length': 'El mensaje no puede exceder los 500 caracteres.'
        }
    )



from django import forms
from .models import MatchValoracion

class ValoracionForm(forms.ModelForm):
    class Meta:
        model = MatchValoracion
        fields = ['valormatch', 'opinion']
        widgets = {
            # Campo de calificación: Usamos un campo 'Select' en lugar de 'NumberInput'
            'valormatch': forms.Select(
                choices=[(1, '1 estrella'), 
                         (2, '2 estrellas'), 
                         (3, '3 estrellas'), 
                         (4, '4 estrellas'), 
                         (5, '5 estrellas')],
                attrs={'class': 'form-select', 'placeholder': 'Selecciona una calificación'}
            ),
            # Campo de opinión
            'opinion': forms.Textarea(attrs={'placeholder': 'Escribe tu opinión', 'rows': 4, 'cols': 50}),
        }
        error_messages = {
            'valormatch': {'required': 'La valoración es obligatoria.'},
            'opinion': {'required': 'La opinión es obligatoria.'},
        }

