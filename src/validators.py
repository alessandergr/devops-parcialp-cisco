import ipaddress


class ErrorValidacion(ValueError):
    pass


def validar_opcion(opcion, opciones_validas):
    if not isinstance(opcion, str):
        raise ErrorValidacion("La opcion debe ser texto.")

    opcion = opcion.strip()

    if opcion not in opciones_validas:
        raise ErrorValidacion("Seleccione una opcion valida.")

    return opcion


def obtener_texto(valor, predeterminado="No disponible"):
    if valor is None:
        return predeterminado

    if not isinstance(valor, str):
        raise ErrorValidacion("Se recibio un campo de texto invalido.")

    valor = valor.strip()
    return valor if valor else predeterminado


def validar_ip(direccion):
    if direccion is None:
        return "No disponible"

    if not isinstance(direccion, str):
        raise ErrorValidacion("La direccion IP debe ser texto.")

    direccion = direccion.strip()

    if direccion.lower() in ("", "none", "null", "n/a"):
        return "No disponible"

    try:
        return str(ipaddress.ip_address(direccion))
    except ValueError as error:
        raise ErrorValidacion(
            "Direccion IP invalida: {}".format(direccion)
        ) from error


def normalizar_dispositivos(dispositivos):
    if not isinstance(dispositivos, list):
        raise ErrorValidacion(
            "El inventario debe contener una lista de dispositivos."
        )

    inventario = []
    identificadores = set()

    for indice, dispositivo in enumerate(dispositivos, start=1):
        if not isinstance(dispositivo, dict):
            raise ErrorValidacion(
                "El dispositivo {} tiene una estructura invalida.".format(
                    indice
                )
            )

        identificador = obtener_texto(
            dispositivo.get("id"),
            "sin-id-{}".format(indice)
        )

        if identificador in identificadores:
            raise ErrorValidacion(
                "Identificador duplicado: {}".format(identificador)
            )

        identificadores.add(identificador)

        equipo = {
            "id": identificador,
            "nombre": obtener_texto(
                dispositivo.get("hostname"),
                "Sin nombre"
            ),
            "tipo": obtener_texto(
                dispositivo.get("family"),
                "Desconocido"
            ),
            "ip": validar_ip(
                dispositivo.get("managementIpAddress")
            ),
            "estado": obtener_texto(
                dispositivo.get("reachabilityStatus"),
                "Desconocido"
            ),
            "modelo": obtener_texto(
                dispositivo.get("platformId")
            ),
            "serie": obtener_texto(
                dispositivo.get("serialNumber")
            ),
            "software": obtener_texto(
                dispositivo.get("softwareVersion")
            )
        }

        inventario.append(equipo)

    return inventario


def resumir_inventario(inventario):
    if not isinstance(inventario, list):
        raise ErrorValidacion("Inventario invalido.")

    resumen = {
        "total": len(inventario),
        "por_tipo": {},
        "por_estado": {}
    }

    for dispositivo in inventario:
        if not isinstance(dispositivo, dict):
            raise ErrorValidacion("Dispositivo invalido.")

        tipo = dispositivo.get("tipo", "Desconocido")
        estado = dispositivo.get("estado", "Desconocido")

        if not isinstance(tipo, str) or not isinstance(estado, str):
            raise ErrorValidacion("Tipo o estado invalido.")

        resumen["por_tipo"][tipo] = (
            resumen["por_tipo"].get(tipo, 0) + 1
        )

        resumen["por_estado"][estado] = (
            resumen["por_estado"].get(estado, 0) + 1
        )

    return resumen
