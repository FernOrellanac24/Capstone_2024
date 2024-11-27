from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth import login, update_session_auth_hash

from django.contrib import messages

from django.contrib.auth.views import LoginView

from .forms import RegistroForm, LoginForm, CustomPasswordChangeForm, ProfileImageForm, NuevoProductoForm, ModificarProductoForm, OptarARegaloForm, OptarACambioForm, MensajeForm, ValoracionForm

from .models import Account, NuevoProducto, MatchProductoRegalo, MatchProductoCambio, Mensajes, MatchValoracion

from django.contrib.contenttypes.models import ContentType 

from django.core.paginator import Paginator

from django.db.models import Q

from datetime import datetime

from decouple import config

from django.db.models import Avg

import mercadopago

from django.http import HttpResponseNotFound

from django.http import HttpResponse
import base64
from io import BytesIO
import qrcode
from django.core.files.base import ContentFile


# Create your views here.


def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()  # Guarda el usuario
            login(request, user)  # Loguea al usuario automáticamente después de registrarlo
            return redirect('login')  # Redirige a una página de inicio o donde desees
    else:
        form = RegistroForm()
    return render(request, 'registration/registro.html', {'form': form})


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'registration/login.html'


def PerfilUsuario(request):
    # Si el usuario hace clic en "Eliminar QR", borra el código QR de la sesión
    if request.method == "POST" and "delete_qr" in request.POST:
        request.session.pop("qr_image_data_url", None)
        return render(request, 'core/PerfilUsuario.html', {'qr_image_data_url': None})

    # Verifica si ya existe un código QR en la sesión
    qr_image_data_url = request.session.get("qr_image_data_url", None)

    # Genera el QR si no está en la sesión o si se ha solicitado generar uno nuevo
    if request.method == "POST" and "generate_qr" in request.POST or not qr_image_data_url:
        usuario = request.user
        user_data = f"Nombre: {usuario.nombre} {usuario.apellido}\nEmail: {usuario.email}\nRUT: {usuario.rut_usuario}"

        qr = qrcode.make(user_data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_image_data = buffer.getvalue()

        qr_image_data_url = "data:image/png;base64," + base64.b64encode(qr_image_data).decode("utf-8")

        # Guarda el QR en la sesión
        request.session["qr_image_data_url"] = qr_image_data_url

    return render(request, 'core/PerfilUsuario.html', {'qr_image_data_url': qr_image_data_url})


# Nueva vista para descargar el QR
def descargar_qr(request):
    usuario = request.user
    user_data = f"Nombre: {usuario.nombre} {usuario.apellido}\nEmail: {usuario.email}\nRUT: {usuario.rut_usuario}"

    qr = qrcode.make(user_data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)  # Regresa al inicio del archivo en memoria

    # Respuesta HTTP para la descarga
    response = HttpResponse(buffer, content_type="image/png")
    response["Content-Disposition"] = 'attachment; filename="codigo_qr.png"'
    return response


def editar_perfil(request):
    # Inicializa el formulario de cambio de contraseña
    form_password = CustomPasswordChangeForm(request.user)

    if request.method == 'POST':
        if 'cambiar_foto' in request.POST:
            imagen = request.FILES.get('fotoPerfil')
            if imagen:
                account = request.user
                account.profile_image = imagen
                account.save()
                messages.success(request, 'Foto de perfil actualizada correctamente.')
                return redirect('editar_perfil')  # Redirigir a la misma página

        elif 'cambiar_contrasenia' in request.POST:
            form_password = CustomPasswordChangeForm(request.user, request.POST)
            if form_password.is_valid():
                form_password.save()
                messages.success(request, 'Tu contraseña ha sido cambiada correctamente.')
                return redirect('login')
            else:
                messages.error(request, 'Por favor, corrige los errores.')

    # Renderiza la plantilla con el formulario de cambio de contraseña
    return render(request, 'core/editar_perfil.html', {'form_password': form_password})



def ProductoAgregar(request):
    if request.method == 'POST':
        form = NuevoProductoForm(request.POST, request.FILES)
        if form.is_valid():
            nuevoProducto = form.save(commit=False)  # No guardamos aún en la base de datos
            nuevoProducto.p_account_email = request.user  # Asignamos el usuario actual
            nuevoProducto.save()  # Ahora guardamos el producto en la base de datos
            return redirect('ProductoListar')  # Redirige a una página después de crear el producto
    else:
        form = NuevoProductoForm()

    return render(request, 'core/producto_agregar.html', {'form': form})



def ProductoModificar(request, id):
    # Obtener el objeto del producto que se desea modificar
    producto = get_object_or_404(NuevoProducto, id=id)
    if request.method == 'POST':
        # Crear una instancia del formulario con los datos del POST y el objeto actual
        form = ModificarProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            # Guardar los cambios directamente desde el formulario
            form.save()
            messages.success(request, 'Producto modificado exitosamente.')
            return redirect('ProductoListar')  # Redirigir a la vista deseada
        else:
            messages.error(request, 'Error al modificar el producto. Verifica los campos.')
    else:
        # Si es una solicitud GET, crear una instancia del formulario con el producto actual
        form = ModificarProductoForm(instance=producto)
    context = {'form': form, 'producto': producto}  # Opcional: para mostrar más detalles
    return render(request, 'core/producto_modificar.html', context)


def ProductoListar(request):
    query = request.GET.get('q')
    
    # Verificar si el usuario es el administrador
    if request.user.email == 'admin@admin.cl':
        productos_list = NuevoProducto.objects.all()
    else:
        productos_list = NuevoProducto.objects.filter(p_account_email=request.user)
    
    # Filtrar productos por la consulta de búsqueda si existe
    if query:
        productos_list = productos_list.filter(
            Q(p_nombre__icontains=query) | Q(p_descripcion__icontains=query)
        )
    
    # Obtener solo los productos activos
    productos_activos = productos_list.filter(p_habilitar__gt=0)

    # Paginación de los productos activos
    paginator = Paginator(productos_activos, 5)  # Muestra 5 productos por página
    page = request.GET.get('page')
    productos = paginator.get_page(page)
    
    context = {
        'productos': productos,
        'search_query': query  # Pasar la consulta de búsqueda al contexto
    }
    return render(request, 'core/producto_listar.html', context)


def ProductoEliminar(request, id):
    producto = get_object_or_404(NuevoProducto, id=id) 
    # Verificar si el producto pertenece al usuario actual o si es el administrador
    if request.user.email == 'admin@admin.cl' or producto.p_account_email == request.user:
        producto.delete()
        messages.success(request, 'Producto eliminado exitosamente.')
    else:
        messages.error(request, 'No tienes permisos para eliminar este producto.')
    return redirect('ProductoReactivar')  # Redirigir a la vista de reactivación


def ProductoReactivar(request):
    # Inicializar la lista de productos inactivos
    productos_inactivos = []
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        producto = get_object_or_404(NuevoProducto, id=producto_id)
        # Verificar si el producto pertenece al usuario actual
        if request.user.email == 'admin@admin.cl' or producto.p_account_email == request.user:
            # Activar el producto estableciendo p_habilitar en 1
            producto.p_habilitar = 1
            producto.save()
            messages.success(request, 'Producto reactivado exitosamente.')
        else:
            messages.error(request, 'No tienes permisos para reactivar este producto.')

        return redirect('ProductoReactivar')  # Redireccionar a la misma página después de activar el producto
    # Resto del código para la búsqueda y la lista de productos inactivos
    query = request.GET.get('q')
    # Filtrar productos en función de si el usuario es administrador o no
    if request.user.email == 'admin@admin.cl':
        productos_list = NuevoProducto.objects.all()
    else:
        productos_list = NuevoProducto.objects.filter(p_account_email=request.user)
    if query:
        # Filtrar los productos por el nombre o la descripción que coincidan con la consulta de búsqueda
        productos_list = productos_list.filter(Q(p_nombre__icontains=query) | Q(p_descripcion__icontains=query))
    # Obtener solo los productos con p_habilitar igual a 0 (inactivos)
    productos_inactivos = productos_list.filter(p_habilitar=0)
    paginator = Paginator(productos_inactivos, 5)  # Muestra 5 productos inactivos por página
    page = request.GET.get('page')
    productos = paginator.get_page(page)
    context = {
        'productos': productos,
        'search_query': query  # Pasar la consulta de búsqueda al contexto
    }
    return render(request, 'core/producto_reactivar.html', context)


def ProductoDesactivar(request):
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        producto = NuevoProducto.objects.get(id=producto_id)
        producto.p_habilitar = 0  # Cambiar el valor a 0 (deshabilitado)
        producto.save()
    return redirect('ProductoListar')

def ProductoActivar(request):
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        producto = NuevoProducto.objects.get(id=producto_id)
        producto.p_habilitar = 1 # Cambiar el valor a 1 (habilitado)
        producto.save()
    return redirect('ProductoReactivar')


def redondear_a_rango(valor):
    # Redondea el valor al entero más cercano dentro del rango [1, 2, 3, 4, 5]
    return max(1, min(5, round(valor)))

# views.py
from django.shortcuts import render
from .models import NuevoProducto, MatchValoracion

def home(request):
    # Obtener todos los productos
    productos = NuevoProducto.objects.all()

    productos_con_promedio = []
    rango_estrellas = range(1, 6)  # El rango de estrellas es del 1 al 5.

    for producto in productos:
        # Obtener las valoraciones para el dueño del producto
        valoraciones = MatchValoracion.objects.filter(dueño_producto=producto.p_account_email)

        if valoraciones.exists():
            promedio_valoracion = valoraciones.aggregate(Avg('valormatch'))['valormatch__avg']
            # Redondeamos al valor entero más cercano
            promedio_valoracion = redondear_a_rango(promedio_valoracion)  # Redondeo al entero más cercano
        else:
            promedio_valoracion = 0

        productos_con_promedio.append({
            'producto': producto,
            'promedio_valoracion': promedio_valoracion
        })

    return render(request, 'core/home.html', {
        'productos_con_promedio': productos_con_promedio,
        'rango': rango_estrellas
    })







#############################################################################33






def optar_a_regalo(request):
    if request.method == 'POST':
        form = OptarARegaloForm(request.POST)
        if form.is_valid():
            producto_id = form.cleaned_data['producto_id']
            usuario_dueño_id = form.cleaned_data['usuario_dueño']

            # Obtener la instancia de Account para el usuario dueño
            #usuario_dueño = get_object_or_404(Account, id=usuario_dueño_id) # Cambio por lo de abajo
            usuario_dueño = Account.objects.get(id=usuario_dueño_id) 

            # Obtener el usuario actual como solicitante
            usuario_solicitante = request.user

            # Verificar si ya existe una solicitud para este producto por el usuario solicitante
            if MatchProductoRegalo.objects.filter(producto_id=producto_id, usuario_solicitante=usuario_solicitante).exists():
                messages.error(request, 'Ya has optado por este producto.')
                return redirect('home')  # Cambia esto a la URL de éxito deseada

            else:
                # Guardar el regalo en la base de datos
                MatchProductoRegalo.objects.create(
                    producto_id=producto_id,
                    usuario_dueño=usuario_dueño,
                    usuario_solicitante=usuario_solicitante
                )
                messages.success(request, 'El regalo se ha guardado correctamente.')
                return redirect('MatchesRegalo')  # Cambia esto a la URL de éxito deseada
        else:
            messages.error(request, 'Hubo un error al intentar guardar el regalo. Por favor, verifica los campos.')
    else:
        producto_id = request.GET.get('producto_id')
        form = OptarARegaloForm(initial={'producto_id': producto_id, 'usuario_dueño': request.user.id})

    return render(request, 'core/home.html', {'form': form})




def MatchesRegalo(request):
    query = request.GET.get('q')
    user = request.user

    # Verificar si el usuario está autenticado y es el administrador
    if user.is_authenticated and user.email == 'admin@admin.cl':
        matches_list = MatchProductoRegalo.objects.all()  # Obtener todos los matches de regalo
    else:
        user_id = user.id  # ID del usuario logueado
        # Filtrar los matches por el ID del usuario dueño o solicitante
        matches_list = MatchProductoRegalo.objects.filter(
            Q(usuario_dueño_id=user_id) | Q(usuario_solicitante_id=user_id)
        )

    if query:
        # Filtrar matches adicionales por nombre o descripción del producto
        matches_list = matches_list.filter(
            Q(producto__p_nombre__icontains=query) | Q(producto__p_descripcion__icontains=query)
        )

    # Asegúrate de ordenar antes de la paginación
    matches_list = matches_list.order_by('-fecha_propuesta')  # Ordena según lo necesites

    paginator = Paginator(matches_list, 5)  # Mostrar 5 matches por página
    page = request.GET.get('page')
    matches = paginator.get_page(page)

    # Manejo de la eliminación de un match
    if request.method == 'POST':
        match_id = request.POST.get('match_id')
        match = get_object_or_404(MatchProductoRegalo, pk=match_id)  # Asegúrate de usar pk
        match.delete()
        messages.success(request, 'Match eliminado correctamente.')

        # Regresar a la misma página con la consulta de búsqueda
        return redirect('MatchesRegalo')  # Asegúrate de que esta URL esté configurada correctamente

    # Crear contexto para la plantilla
    context = {
        'matches': matches,
        'search_query': query  # Pasar la consulta de búsqueda al contexto
    }

    return render(request, 'core/MatchesRegalo.html', context)




def ConfirmarMatchRegalo(request):
    if request.method == 'POST':
        postmatch_id = request.POST.get('match_id')
        if postmatch_id:
            match = get_object_or_404(MatchProductoRegalo, PostMatch=int(postmatch_id))
            # Toggle the confirmation state
            match.confirmacion_match = 1 if match.confirmacion_match == 0 else 0
            match.save()
            # Optional: Perform any additional actions after confirming the match
    return redirect('MatchesRegalo')



def EliminarMatchProductoRegalo(request, match_id):
    # Usar get_object_or_404 para manejar la excepción si el match no existe
    match = get_object_or_404(MatchProductoRegalo, PostMatch=match_id)
    
    if request.method == 'POST':
        match.delete()
        messages.success(request, 'Match eliminado exitosamente.')  # Mensaje de éxito
        return redirect('MatchesRegalo')
    
    # Si no es POST, renderizar una plantilla de confirmación
    return render(request, 'core/MatchesRegalo.html', {'match_id': match_id, 'match': match})

########################################################################################################





def optar_a_cambio(request):
    if request.method == 'POST':
        form = OptarACambioForm(request.POST)
        if form.is_valid():
            producto_id = form.cleaned_data['producto_id']
            usuario_dueño_id = form.cleaned_data['usuario_dueño']
            producto_propuesto_id = form.cleaned_data.get('producto_propuesto_id')  # Puede ser None

            usuario_dueño = get_object_or_404(Account, id=usuario_dueño_id)
            usuario_solicitante = request.user

            # Verifica si ya existe una solicitud para este producto
            if MatchProductoCambio.objects.filter(producto_id=producto_id, usuario_solicitante=usuario_solicitante).exists():
                messages.error(request, 'Ya has optado por este producto.')
                return redirect('home')
            else:
                # Guardar el cambio en la base de datos sin producto_propuesto
                MatchProductoCambio.objects.create(
                    producto_id=producto_id,
                    usuario_dueño=usuario_dueño,
                    usuario_solicitante=usuario_solicitante,
                    producto_propuesto_id=producto_propuesto_id  # Puede ser None
                )
                messages.success(request, 'La solicitud de cambio se ha guardado correctamente.')
                return redirect('MatchesCambio')
        else:
            messages.error(request, 'Hubo un error al intentar crear la solicitud de cambio. Por favor, verifica los campos.')
    else:
        form = OptarACambioForm()

    return render(request, 'core/home.html', {'form': form})




def MatchesCambio(request):
    query = request.GET.get('q')
    user = request.user

    # Obtener matches de cambio según el usuario
    if user.is_authenticated and user.email == 'admin@admin.cl':
        matches_list = MatchProductoCambio.objects.all()  # Obtener todos los matches de cambio
    else:
        user_id = user.id  # ID del usuario logueado
        matches_list = MatchProductoCambio.objects.filter(
            Q(usuario_dueño_id=user_id) | Q(usuario_solicitante_id=user_id)
        )  # Filtrar los matches por el ID del usuario dueño o solicitante

    # Filtrar matches por nombre o descripción del producto
    if query:
        matches_list = matches_list.filter(
            Q(producto__p_nombre__icontains=query) | Q(producto__p_descripcion__icontains=query)
        )

    # Paginación
    paginator = Paginator(matches_list, 5)  # Mostrar 5 matches por página
    page = request.GET.get('page')
    matches = paginator.get_page(page)

    # Contexto para la plantilla
    context = {
        'matches': matches,
        'search_query': query
    }

    # Manejo de eliminación de matches
    if request.method == 'POST':
        match_id = request.POST.get('match_id')
        match = get_object_or_404(MatchProductoCambio, PostMatch=match_id)  # Manejo de errores
        match.delete()
        messages.success(request, 'Match eliminado exitosamente.')  # Mensaje de éxito
        return redirect('MatchesCambio')

    return render(request, 'core/MatchesCambio.html', context)



def EliminarMatchProductoCambio(request, match_id):
    # Use get_object_or_404 to handle cases where the match does not exist
    match = get_object_or_404(MatchProductoCambio, PostMatch=match_id)
    
    if request.method == 'POST':
        match.delete()  # Delete the match
        return redirect('MatchesCambio')  # Redirect to the matches list
    else:
        # Render a confirmation template if it's not a POST request
        return render(request, 'core/MatchesCambio.html', {'match_id': match_id, 'match': match})
    



def ConfirmarMatchCambio(request):
    if request.method == 'POST':
        postmatch_id = request.POST.get('match_id')
        if postmatch_id:
            match = get_object_or_404(MatchProductoCambio, PostMatch=int(postmatch_id))
            # Toggle the confirmation state
            match.confirmacion_match = 1 if match.confirmacion_match == 0 else 0
            match.save()
            # Optional: Perform any additional actions after confirming the match
    return redirect('MatchesCambio')




#################################################################################################3




from django.contrib.contenttypes.models import ContentType

def ChatMensajes(request, postmatch_id):
    # Intenta obtener el MatchProductoRegalo
    match_producto_regalo = MatchProductoRegalo.objects.filter(PostMatch=postmatch_id).first()
    
    # Si no se encuentra, intenta con MatchProductoCambio
    match_producto_cambio = MatchProductoCambio.objects.filter(PostMatch=postmatch_id).first()

    if match_producto_regalo is None and match_producto_cambio is None:
        return render(request, 'core/error.html', {"error": "Match no encontrado."})

    # Determinar qué match utilizar
    match_producto = match_producto_regalo or match_producto_cambio

    # Verificar si se puede valorar el match usando content_type y object_id
    content_type = ContentType.objects.get_for_model(match_producto)
    puede_valorar = not MatchValoracion.objects.filter(
        content_type=content_type,
        object_id=match_producto.PostMatch,
        evaluador=request.user
    ).exists()

    new_message = False
    form = MensajeForm()

    if request.method == 'POST':
        form = MensajeForm(request.POST)
        print(request.POST)  # Esto imprimirá todos los datos enviados en el POST
        print(form.errors)    # Esto imprimirá errores del formulario
        if form.is_valid():
            mensaje = form.cleaned_data['mensaje']
            usuario_post = request.user
            
            # Crear el mensaje
            Mensajes.objects.create(
                usuarioPost=usuario_post,
                mensajePost=mensaje,
                content_type=content_type,
                object_id=match_producto.PostMatch
            )

            new_message = True

    # Obtener los mensajes anteriores para este match
    citas = Mensajes.objects.filter(
        content_type=content_type,
        object_id=match_producto.PostMatch
    )

    return render(request, 'core/Mensajes.html', {
        'form': form,
        'citas': citas,
        'nombre': request.user.nombre,
        'match_producto': match_producto,
        'postmatch_id': postmatch_id,
        'new_message': new_message,
        'puede_valorar': puede_valorar  # Agregado para el contexto
    })



def ListaChatMatch(request):
    query = request.GET.get('q')
    user = request.user

    # Recuperar matches según el rol del usuario
    if user.is_authenticated and user.email == 'admin@admin.cl':
        matches_regalo = MatchProductoRegalo.objects.filter(confirmacion_match=1)
        matches_cambio = MatchProductoCambio.objects.filter(confirmacion_match=1)
    else:
        matches_regalo = MatchProductoRegalo.objects.filter(
            Q(usuario_dueño=user) | Q(usuario_solicitante=user),
            confirmacion_match=1
        )
        matches_cambio = MatchProductoCambio.objects.filter(
            Q(usuario_dueño=user) | Q(usuario_solicitante=user),
            confirmacion_match=1
        )

    # Filtrar por búsqueda
    if query:
        matches_regalo = matches_regalo.filter(
            Q(producto__p_nombre__icontains=query) | Q(producto__p_descripcion__icontains=query)
        )
        matches_cambio = matches_cambio.filter(
            Q(producto__p_nombre__icontains=query) | Q(producto_propuesto__p_nombre__icontains=query)
        )

    context = {
        'matches_regalo': matches_regalo,
        'matches_cambio': matches_cambio,
        'search_query': query
    }
    return render(request, 'core/ListaChatMatch.html', context)








def valoracion_match(request, postmatch_id):
    match_producto = MatchProductoRegalo.objects.filter(PostMatch=postmatch_id).first() or \
                     MatchProductoCambio.objects.filter(PostMatch=postmatch_id).first()

    if not match_producto:
        return HttpResponseNotFound("Match no encontrado.")

    content_type = ContentType.objects.get_for_model(match_producto)

    existing_valoracion = MatchValoracion.objects.filter(
        content_type=content_type, object_id=match_producto.PostMatch, evaluador=request.user
    ).first()

    form = ValoracionForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            if existing_valoracion:
                existing_valoracion.valormatch = form.cleaned_data['valormatch']
                existing_valoracion.opinion = form.cleaned_data['opinion']
                existing_valoracion.save()
                messages.success(request, 'Tu valoración ha sido actualizada con éxito.')
            else:
                valoracion = form.save(commit=False)
                valoracion.dueño_producto = match_producto.usuario_dueño
                valoracion.evaluador = request.user
                valoracion.content_type = content_type
                valoracion.object_id = match_producto.PostMatch
                valoracion.save()
                messages.success(request, 'Tu valoración ha sido registrada con éxito.')
            return redirect('ListaChatMatch')

    else:
        if existing_valoracion:
            form.fields['valormatch'].initial = existing_valoracion.valormatch
            form.fields['opinion'].initial = existing_valoracion.opinion

    promedio_valoracion = MatchValoracion.objects.filter(
        content_type=content_type, object_id=match_producto.PostMatch
    ).aggregate(Avg('valormatch'))['valormatch__avg']

    if not promedio_valoracion:
        promedio_valoracion = 0

    # Obtener todas las valoraciones de este match
    valoraciones = MatchValoracion.objects.filter(
        content_type=content_type, object_id=match_producto.PostMatch
    )

    context = {
        'form': form,
        'match': match_producto,
        'promedio_valoracion': promedio_valoracion,
        'estrellas': range(1, 6),
        'valoraciones': valoraciones,  # Pasar las valoraciones al template
    }

    return render(request, 'core/valoracion_form.html', context)



######################################################################################################



def pago_exitoso(request):
    # Aquí puedes capturar los parámetros GET de la URL, si los necesitas
    collection_id = request.GET.get('collection_id')
    collection_status = request.GET.get('collection_status')
    payment_id = request.GET.get('payment_id')
    # Puedes hacer lo que necesites con estos datos, por ejemplo, almacenarlos en la base de datos.

    return render(request, 'pago_exitoso.html', {
        'collection_id': collection_id,
        'collection_status': collection_status,
        'payment_id': payment_id
    })

def pago_fallido(request):
    return render(request, 'pago_fallido.html')

def pago_pendiente(request):
    return render(request, 'pago_pendiente.html')



def optar_a_venta(request):
    if request.method == "POST":
        producto_id = request.POST.get('producto_id')
        usuario_dueño = get_object_or_404(Account, id=request.POST.get('usuario_dueño'))

        # Obtén el producto de la base de datos
        producto = get_object_or_404(NuevoProducto, id=producto_id)

        # Inicializa el SDK de Mercado Pago usando el token de .env
        sdk = mercadopago.SDK(config("MERCADOPAGO_ACCESS_TOKEN"))

        # Crea un ítem en la preferencia con el nombre y precio del producto
        preference_data = {
            "items": [
                {
                    "title": producto.p_nombre,
                    "quantity": 1,
                    "unit_price": float(producto.p_precio) if producto.p_precio is not None else 0.0
                }
            ],
            "payer": {
                "name": f"{usuario_dueño.nombre} {usuario_dueño.apellido}",
                "email": usuario_dueño.email
            },
            "back_urls": {
                "success": "http://127.0.0.1:8000/pago-exitoso/",
                "failure": "http://127.0.0.1:8000/pago-fallido/",
                "pending": "http://127.0.0.1:8000/pago-pendiente/"
            },
            "auto_return": "approved"  # Configura auto retorno en éxito
        }

        preference_response = sdk.preference().create(preference_data)

        # Maneja la respuesta de Mercado Pago
        if preference_response["response"] and "init_point" in preference_response["response"]:
            # Redirige al usuario a la URL de pago
            return redirect(preference_response["response"]["init_point"])

        # Maneja el caso en que no se pudo crear la preferencia
        messages.error(request, "Error al crear la preferencia de pago.")
        return redirect('home')

    # Manejo de otras solicitudes (GET, etc.)
    return redirect('home')







##################################################################################################



from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site

class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    from_email = 'fern.orellanac@gmail.com'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['protocol'] = 'http'  # Cambia a 'https' en producción
        current_site = get_current_site(self.request)
        context['domain'] = current_site.domain
        # Intenta agregar manualmente el contexto url para probar
        context['url'] = self.request.build_absolute_uri('/password_reset_confirm/')
        return context


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'  # Asegúrate de que la plantilla exista
    success_url = '/reset/done/'  # O el nombre de la URL que desees

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'




