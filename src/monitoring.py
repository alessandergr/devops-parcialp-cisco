import sys
import requests

from config import cargar_configuracion, ErrorConfiguracion
from api_client import configurar_registros, consultar_inventario, ErrorAPI
from validators import normalizar_dispositivos, ErrorValidacion
from file_manager import guardar_inventario, ErrorArchivo
from report_manager import generar_reporte
from webex_client import WebexClient


def actualizar_inventario():
    configurar_registros()
    configuracion = cargar_configuracion()
    dispositivos = consultar_inventario(configuracion)
    inventario = normalizar_dispositivos(dispositivos)
    guardar_inventario(inventario)
    return inventario


def ejecutar_monitoreo():
    print("=== DEVOPS MANAGER - MONITOREO ===")

    try:
        inventario = actualizar_inventario()
        print("Inventario actualizado correctamente.")
        print(f"Dispositivos encontrados: {len(inventario)}")

    except (ErrorAPI, ErrorConfiguracion, ErrorValidacion,
            ErrorArchivo, OSError) as error:
        print(f"Error de actualizacion: {error}", file=sys.stderr)

        try:
            WebexClient().enviar_mensaje(
                "**DevOps Manager - Alerta de monitoreo**\n\n"
                "No se pudo actualizar el inventario de Cisco. "
                "Se requiere revisar la conexion."
            )
        except (requests.RequestException, ValueError):
            print("No se pudo enviar la alerta.", file=sys.stderr)

        return 1

    try:
        mensaje, ruta = generar_reporte()
        print(f"Reporte generado: {ruta.name}")

        mensaje += f"\n\n**Identificador:** `{ruta.name}`"

        WebexClient().enviar_mensaje(mensaje)
        print("Reporte enviado correctamente a Webex.")
        print("Monitoreo finalizado correctamente.")
        return 0

    except (requests.RequestException, ValueError, OSError) as error:
        print(f"Error en el reporte: {type(error).__name__}",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(ejecutar_monitoreo())
