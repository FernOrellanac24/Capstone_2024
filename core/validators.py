import re

def validar_rut(rut: str) -> bool:
    """
    Valida un RUT chileno.

    Args:
        rut (str): El RUT a validar en formato string.

    Returns:
        bool: True si el RUT es válido, False en caso contrario.
    """
    # Eliminar puntos y guiones del RUT
    rut = rut.replace(".", "").replace("-", "")
    
    # Validar longitud del RUT
    if len(rut) < 8 or len(rut) > 9:
        return False

    cuerpo = rut[:-1]
    dv = rut[-1].upper()

    # Verificar que el cuerpo del RUT contenga solo dígitos
    if not cuerpo.isdigit():
        return False

    suma = 0
    multiplicador = 2
    
    # Calcular el dígito verificador
    for caracter in reversed(cuerpo):
        suma += int(caracter) * multiplicador
        multiplicador = 9 if multiplicador == 2 else multiplicador - 1

    dv_calculado = 11 - (suma % 11)
    dv_calculado = 'K' if dv_calculado == 10 else '0' if dv_calculado == 11 else str(dv_calculado)

    return dv == dv_calculado
