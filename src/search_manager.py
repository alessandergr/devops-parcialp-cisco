class ErrorBusqueda(ValueError):
    pass


CAMPOS_BUSQUEDA = ("nombre", "ip", "id")


def buscar_dispositivos(inventario, consulta):
    if not isinstance(inventario, list):
        raise ErrorBusqueda("El inventario debe ser una lista.")

    if not isinstance(consulta, str) or not consulta.strip():
        raise ErrorBusqueda("Ingrese un valor de busqueda valido.")

    texto = consulta.strip().casefold()
    resultados = []

    for dispositivo in inventario:
        if not isinstance(dispositivo, dict):
            raise ErrorBusqueda("Se encontro un dispositivo invalido.")

        valores = []

        for campo in CAMPOS_BUSQUEDA:
            valor = dispositivo.get(campo)

            if not isinstance(valor, str):
                raise ErrorBusqueda(
                    "El campo {} del dispositivo es invalido.".format(campo)
                )

            valores.append(valor.casefold())

        if any(texto in valor for valor in valores):
            resultados.append(dispositivo)

    return sorted(
        resultados,
        key=lambda equipo: (
            equipo["nombre"].casefold(),
            equipo["ip"]
        )
    )


def paginar_resultados(resultados, pagina=1, cantidad=10):
    if not isinstance(resultados, list):
        raise ErrorBusqueda("Los resultados deben ser una lista.")

    if (
        isinstance(pagina, bool)
        or isinstance(cantidad, bool)
        or not isinstance(pagina, int)
        or not isinstance(cantidad, int)
        or pagina < 1
        or cantidad < 1
    ):
        raise ErrorBusqueda("Los parametros de paginacion son invalidos.")

    total = len(resultados)
    total_paginas = max(
        1, (total + cantidad - 1) // cantidad
    )

    if pagina > total_paginas:
        raise ErrorBusqueda("La pagina solicitada no existe.")

    inicio = (pagina - 1) * cantidad
    fin = inicio + cantidad

    return {
        "resultados": resultados[inicio:fin],
        "pagina": pagina,
        "total_paginas": total_paginas,
        "total_resultados": total
    }
