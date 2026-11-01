import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union
from urllib.parse import urlparse

from dotenv import dotenv_values


RUTA_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_ENV = RUTA_PROYECTO / ".env"


class ErrorConfiguracion(Exception):
    pass


@dataclass(frozen=True)
class ConfiguracionCisco:
    url_base: str
    usuario: str
    clave: str = field(repr=False)
    verificar_tls: Union[bool, str]
    tiempo_espera: int


def cargar_configuracion():
    try:
        variables = dotenv_values(str(RUTA_ENV)) if RUTA_ENV.exists() else {}
    except (OSError, UnicodeError) as error:
        raise ErrorConfiguracion(
            "No se pudo leer el archivo de configuracion."
        ) from error

    def obtener(nombre):
        valor = os.environ.get(nombre)
        if valor is None:
            valor = variables.get(nombre)
        return str(valor or "").strip()

    url = obtener("CISCO_BASE_URL") or "https://sandboxdnac.cisco.com"
    usuario = obtener("CISCO_USERNAME")
    clave = obtener("CISCO_PASSWORD")
    tiempo = obtener("CISCO_TIMEOUT") or "15"
    tls = (obtener("CISCO_VERIFY_TLS") or "true").lower()
    certificado = obtener("CISCO_CA_BUNDLE")

    datos_url = urlparse(url)

    if (
        datos_url.scheme != "https"
        or not datos_url.hostname
        or datos_url.username
        or datos_url.password
        or datos_url.path not in ("", "/")
        or datos_url.query
        or datos_url.fragment
    ):
        raise ErrorConfiguracion("La URL debe utilizar HTTPS y ser valida.")

    if not usuario or not clave:
        raise ErrorConfiguracion("Faltan las credenciales de Cisco.")

    try:
        tiempo = int(tiempo)
    except ValueError as error:
        raise ErrorConfiguracion("Tiempo de espera no valido.") from error

    if not 1 <= tiempo <= 60:
        raise ErrorConfiguracion(
            "El tiempo de espera debe estar entre 1 y 60 segundos."
        )

    if tls not in ("true", "false"):
        raise ErrorConfiguracion(
            "CISCO_VERIFY_TLS debe ser true o false."
        )

    if certificado:
        ruta_ca = Path(certificado).expanduser()

        if not ruta_ca.is_absolute():
            ruta_ca = RUTA_PROYECTO / ruta_ca

        if not ruta_ca.is_file():
            raise ErrorConfiguracion("Certificado CA no encontrado.")

        verificar_tls = str(ruta_ca)

    elif tls == "false":
        if datos_url.hostname != "sandboxdnac.cisco.com":
            raise ErrorConfiguracion(
                "Solo se permite desactivar TLS en el Sandbox autorizado."
            )

        warnings.warn(
            "La verificacion TLS esta desactivada para el laboratorio.",
            RuntimeWarning
        )
        verificar_tls = False

    else:
        verificar_tls = True

    return ConfiguracionCisco(
        url_base=url.rstrip("/"),
        usuario=usuario,
        clave=clave,
        verificar_tls=verificar_tls,
        tiempo_espera=tiempo
    )
