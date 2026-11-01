import logging
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

from config import cargar_configuracion, ErrorConfiguracion


RUTA_PROYECTO = Path(__file__).resolve().parent.parent
LOGGER = logging.getLogger("devops_parcial.api")

RUTA_TOKEN = "/dna/system/api/v1/auth/token"
RUTA_INVENTARIO = "/dna/intent/api/v1/network-device"


class ErrorAPI(Exception):
    pass


def configurar_registros():
    if LOGGER.handlers:
        return

    archivo = RUTA_PROYECTO / "logs" / "app.log"
    archivo.parent.mkdir(parents=True, exist_ok=True)

    manejador = logging.FileHandler(str(archivo), encoding="utf-8")
    manejador.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )
    )

    LOGGER.addHandler(manejador)
    LOGGER.setLevel(logging.INFO)


def realizar_solicitud(metodo, ruta, configuracion, **opciones):
    url = configuracion.url_base + ruta

    try:
        respuesta = requests.request(
            metodo,
            url,
            timeout=configuracion.tiempo_espera,
            verify=configuracion.verificar_tls,
            allow_redirects=False,
            **opciones
        )
    except requests.exceptions.SSLError as error:
        LOGGER.error("Error de certificado TLS en %s", ruta)
        raise ErrorAPI("No se pudo verificar el certificado HTTPS.") from error
    except requests.exceptions.Timeout as error:
        LOGGER.error("Tiempo de espera agotado en %s", ruta)
        raise ErrorAPI("El servidor no respondio a tiempo.") from error
    except requests.exceptions.ConnectionError as error:
        LOGGER.error("Error de conexion en %s", ruta)
        raise ErrorAPI("No fue posible conectar con Cisco Sandbox.") from error
    except requests.exceptions.RequestException as error:
        LOGGER.error("Error de solicitud en %s", ruta)
        raise ErrorAPI("La solicitud HTTP fallo.") from error

    estado = respuesta.status_code
    LOGGER.info("%s %s - HTTP %s", metodo, ruta, estado)

    errores = {
        400: "Solicitud incorrecta.",
        401: "Credenciales o token incorrectos.",
        403: "No tiene autorizacion para consultar el recurso.",
        404: "No se encontro el endpoint solicitado.",
        429: "Se alcanzo el limite de solicitudes de la API."
    }

    if estado >= 400:
        mensaje = errores.get(estado)

        if not mensaje and estado >= 500:
            mensaje = "El servidor Cisco presenta un error interno."

        if not mensaje:
            mensaje = "La solicitud fue rechazada."

        raise ErrorAPI("HTTP {}: {}".format(estado, mensaje))

    if 300 <= estado < 400:
        raise ErrorAPI("Redireccion inesperada: HTTP {}.".format(estado))

    if estado != 200:
        raise ErrorAPI("Respuesta HTTP no esperada: {}.".format(estado))

    return respuesta


def validar_json(respuesta):
    tipo = respuesta.headers.get("Content-Type", "").lower()

    if "application/json" not in tipo:
        raise ErrorAPI("El servidor no devolvio contenido JSON.")

    try:
        datos = respuesta.json()
    except ValueError as error:
        raise ErrorAPI("La respuesta contiene JSON invalido.") from error

    if not isinstance(datos, dict):
        raise ErrorAPI("La estructura JSON recibida es incorrecta.")

    return datos


def obtener_token(configuracion):
    respuesta = realizar_solicitud(
        "POST",
        RUTA_TOKEN,
        configuracion,
        auth=HTTPBasicAuth(
            configuracion.usuario,
            configuracion.clave
        ),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    )

    datos = validar_json(respuesta)
    token = datos.get("Token")

    if not isinstance(token, str) or not token.strip():
        raise ErrorAPI("Cisco no devolvio un token valido.")

    LOGGER.info("Autenticacion realizada correctamente")
    return token


def consultar_inventario(configuracion):
    token = obtener_token(configuracion)

    respuesta = realizar_solicitud(
        "GET",
        RUTA_INVENTARIO,
        configuracion,
        headers={
            "Accept": "application/json",
            "X-Auth-Token": token
        }
    )

    datos = validar_json(respuesta)
    dispositivos = datos.get("response")

    if not isinstance(dispositivos, list):
        raise ErrorAPI("El inventario no contiene una lista valida.")

    if any(not isinstance(item, dict) for item in dispositivos):
        raise ErrorAPI("El inventario contiene dispositivos invalidos.")

    LOGGER.info(
        "Consulta correcta: %s dispositivos recibidos",
        len(dispositivos)
    )

    return dispositivos


if __name__ == "__main__":
    try:
        configurar_registros()
        configuracion = cargar_configuracion()

        print("Conectando con Cisco Catalyst Center...")
        dispositivos = consultar_inventario(configuracion)

        print("Autenticacion correcta.")
        print("Consulta de inventario correcta.")
        print("Dispositivos encontrados:", len(dispositivos))

        for dispositivo in dispositivos[:5]:
            nombre = dispositivo.get("hostname") or "Sin nombre"
            tipo = dispositivo.get("family") or "Desconocido"
            print("- {} ({})".format(nombre, tipo))

    except (ErrorConfiguracion, ErrorAPI, OSError) as error:
        LOGGER.error("Operacion fallida: %s", error)
        print("ERROR:", error)
        raise SystemExit(1)
