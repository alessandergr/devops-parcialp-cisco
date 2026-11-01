
from collections import deque
from pathlib import Path

from access_control import obtener_permisos
from file_manager import (
    ErrorArchivo,
    guardar_inventario,
    leer_inventario
)
from search_manager import (
    ErrorBusqueda,
    buscar_dispositivos,
    paginar_resultados
)
from validators import (
    ErrorValidacion,
    normalizar_dispositivos,
    resumir_inventario,
    validar_opcion
)


RUTA_PROYECTO = Path(__file__).resolve().parent.parent


def actualizar_desde_cisco():
    from config import cargar_configuracion, ErrorConfiguracion
    from api_client import (
        ErrorAPI,
        configurar_registros,
        consultar_inventario
    )

    try:
        configurar_registros()
        configuracion = cargar_configuracion()

        print("\nConsultando Cisco Sandbox...")
        dispositivos = consultar_inventario(configuracion)
        inventario = normalizar_dispositivos(dispositivos)
        archivos = guardar_inventario(inventario)

        print("Consulta realizada correctamente.")
        print("Dispositivos obtenidos:", len(inventario))
        print("JSON:", archivos["json"])
        print("CSV:", archivos["csv"])

    except (ErrorConfiguracion, ErrorAPI) as error:
        print("ERROR de conexion:", error)


def mostrar_inventario():
    inventario = leer_inventario()

    print("\n=== INVENTARIO DE DISPOSITIVOS ===")
    print("{:<15} {:<18} {:<23} {}".format(
        "Nombre", "IP", "Tipo", "Estado"
    ))
    print("-" * 72)

    for equipo in inventario:
        print("{:<15} {:<18} {:<23} {}".format(
            equipo["nombre"][:15],
            equipo["ip"][:18],
            equipo["tipo"][:23],
            equipo["estado"]
        ))

    print("\nTotal de dispositivos:", len(inventario))


def mostrar_detalles(dispositivo):
    campos = [
        ("Nombre", "nombre"),
        ("IP", "ip"),
        ("Tipo", "tipo"),
        ("Estado", "estado"),
        ("Modelo", "modelo"),
        ("Serie", "serie"),
        ("Software", "software"),
        ("ID", "id")
    ]

    print("\n=== DETALLES DEL DISPOSITIVO ===")

    for etiqueta, campo in campos:
        print("{:<12} {}".format(
            etiqueta + ":",
            dispositivo[campo]
        ))

    while True:
        print("\n1. Buscar otro dispositivo")
        print("2. Volver a los resultados")
        print("0. Menu principal")

        opcion = input("\nSeleccione una opcion: ").strip()

        if opcion in ("0", "1", "2"):
            return opcion

        print("ERROR: Opcion invalida.")


def interfaz_busqueda():
    inventario = leer_inventario()

    if not inventario:
        print("\nNo existen dispositivos en el inventario.")
        return

    while True:
        print("\n=== BUSQUEDA DE DISPOSITIVOS ===")
        print("Buscar por nombre, IP o ID.")
        print("0. Regresar al menu principal")

        consulta = input("\nIngrese su busqueda: ").strip()

        if consulta == "0":
            return

        try:
            resultados = buscar_dispositivos(inventario, consulta)
        except ErrorBusqueda as error:
            print("ERROR:", error)
            continue

        if not resultados:
            print("No se encontraron coincidencias.")
            continue

        pagina = 1

        while True:
            datos = paginar_resultados(resultados, pagina)
            visibles = datos["resultados"]

            print("\n=== RESULTADOS ===")
            print("Coincidencias:", datos["total_resultados"])
            print("Pagina {} de {}".format(
                datos["pagina"],
                datos["total_paginas"]
            ))

            for numero, dispositivo in enumerate(visibles, start=1):
                print("{}. {} | {} | {}".format(
                    numero,
                    dispositivo["nombre"],
                    dispositivo["ip"],
                    dispositivo["estado"]
                ))

            print("\nIngrese el numero del dispositivo.")
            print("S. Pagina siguiente")
            print("A. Pagina anterior")
            print("B. Nueva busqueda")
            print("0. Menu principal")

            opcion = input("\nSeleccione una opcion: ").strip().lower()

            if opcion == "0":
                return

            if opcion == "b":
                break

            if opcion == "s":
                if pagina < datos["total_paginas"]:
                    pagina += 1
                else:
                    print("Ya esta en la ultima pagina.")
                continue

            if opcion == "a":
                if pagina > 1:
                    pagina -= 1
                else:
                    print("Ya esta en la primera pagina.")
                continue

            if opcion.isdecimal():
                numero = int(opcion)

                if 1 <= numero <= len(visibles):
                    accion = mostrar_detalles(visibles[numero - 1])

                    if accion == "0":
                        return

                    if accion == "1":
                        break

                    continue

            print("ERROR: Opcion invalida.")


def exportar_inventario():
    inventario = leer_inventario()
    archivos = guardar_inventario(inventario)

    print("\nArchivos exportados correctamente:")
    print("JSON:", archivos["json"])
    print("CSV:", archivos["csv"])


def mostrar_resumen():
    inventario = leer_inventario()
    resumen = resumir_inventario(inventario)

    print("\n=== RESUMEN DEL INVENTARIO ===")
    print("Total:", resumen["total"])

    print("\nDispositivos por tipo:")
    for tipo, cantidad in sorted(resumen["por_tipo"].items()):
        print("- {}: {}".format(tipo, cantidad))

    print("\nDispositivos por estado:")
    for estado, cantidad in sorted(resumen["por_estado"].items()):
        print("- {}: {}".format(estado, cantidad))


def comprobar_conexion():
    from config import cargar_configuracion, ErrorConfiguracion
    from api_client import (
        ErrorAPI,
        configurar_registros,
        consultar_inventario
    )

    print("\n=== VERIFICACION DE API CISCO ===")
    print("Consultando Cisco Catalyst Center Sandbox...")

    try:
        configurar_registros()
        configuracion = cargar_configuracion()

        # Comprueba autenticacion y consulta real del inventario.
        # No guarda ni modifica los archivos JSON y CSV.
        dispositivos = consultar_inventario(configuracion)

        print("\nServidor:", configuracion.url_base)
        print("Autenticacion: Correcta (HTTP 200)")
        print("Consulta de inventario: Correcta (HTTP 200)")
        print("Dispositivos disponibles:", len(dispositivos))

        if configuracion.verificar_tls:
            print("Verificacion TLS: Activada")
        else:
            print(
                "Verificacion TLS: "
                "Desactivada (laboratorio)"
            )

        print(
            "\nResultado: Conexion con la API "
            "verificada correctamente."
        )
        print("El inventario guardado no fue modificado.")

    except (ErrorConfiguracion, ErrorAPI) as error:
        print("\nResultado: No fue posible verificar la API.")
        print("Detalle del error:", error)


def mostrar_registros():
    archivo = RUTA_PROYECTO / "logs" / "app.log"

    if not archivo.is_file():
        print("\nTodavia no existen registros.")
        return

    with archivo.open("r", encoding="utf-8") as registro:
        ultimas_lineas = deque(registro, maxlen=10)

    print("\n=== ULTIMOS EVENTOS ===")

    if not ultimas_lineas:
        print("El registro esta vacio.")
        return

    for linea in ultimas_lineas:
        print(linea.rstrip())


ACCIONES = [
    ("1", "actualizar", "Actualizar desde Cisco", actualizar_desde_cisco),
    ("2", "consultar", "Ver inventario general", mostrar_inventario),
    ("3", "exportar", "Exportar JSON y CSV", exportar_inventario),
    ("4", "resumen", "Ver resumen", mostrar_resumen),
    ("5", "conexion", "Verificar acceso a la API Cisco", comprobar_conexion),
    ("6", "registros", "Ver registros de actividad", mostrar_registros),
    ("7", "buscar", "Buscar dispositivo y ver detalles", interfaz_busqueda)
]


def ejecutar_menu():
    usuario, permisos = obtener_permisos()

    if permisos is None:
        print("Acceso denegado: usuario o grupo no autorizado.")
        return 1

    while True:
        print("\n=== DEVOPS PARCIAL ===")
        print("Usuario:", usuario)
        print("Sistema de inventario de red\n")

        disponibles = {}

        for numero, permiso, descripcion, funcion in ACCIONES:
            if permiso in permisos:
                disponibles[numero] = funcion
                print("{}. {}".format(numero, descripcion))

        print("0. Salir")

        try:
            opcion = validar_opcion(
                input("\nSeleccione una opcion: "),
                set(disponibles) | {"0"}
            )

        except ErrorValidacion as error:
            print("ERROR:", error)
            continue

        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo de la aplicacion.")
            return 0

        if opcion == "0":
            print("Hasta luego.")
            return 0

        try:
            disponibles[opcion]()

        except (
            ErrorArchivo,
            ErrorValidacion,
            ErrorBusqueda,
            OSError,
            UnicodeError
        ) as error:
            print("ERROR:", error)

        except (KeyboardInterrupt, EOFError):
            print("\nOperacion cancelada. Volviendo al menu.")


if __name__ == "__main__":
    raise SystemExit(ejecutar_menu())
