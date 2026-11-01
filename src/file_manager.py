import csv
import json
import os
import tempfile
from pathlib import Path


RUTA_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_DATOS = RUTA_PROYECTO / "data"

CAMPOS = [
    "id",
    "nombre",
    "tipo",
    "ip",
    "estado",
    "modelo",
    "serie",
    "software"
]


class ErrorArchivo(Exception):
    pass


def validar_inventario(inventario):
    if not isinstance(inventario, list):
        raise ErrorArchivo("El inventario debe ser una lista.")

    for numero, dispositivo in enumerate(inventario, start=1):
        if not isinstance(dispositivo, dict):
            raise ErrorArchivo(
                "El dispositivo {} no es valido.".format(numero)
            )

        for campo in CAMPOS:
            if campo not in dispositivo:
                raise ErrorArchivo(
                    "Falta el campo {} en el dispositivo {}.".format(
                        campo, numero
                    )
                )

            if not isinstance(dispositivo[campo], str):
                raise ErrorArchivo(
                    "El campo {} debe contener texto.".format(campo)
                )


def escribir_archivo(nombre, funcion_escritura):
    try:
        RUTA_DATOS.mkdir(parents=True, exist_ok=True)

        descriptor, temporal = tempfile.mkstemp(
            prefix=".devops_",
            suffix=".tmp",
            dir=str(RUTA_DATOS)
        )
    except OSError as error:
        raise ErrorArchivo(
            "No se pudo preparar el directorio de datos."
        ) from error

    destino = RUTA_DATOS / nombre

    try:
        with os.fdopen(
            descriptor, "w", encoding="utf-8", newline=""
        ) as archivo:
            funcion_escritura(archivo)

        os.chmod(temporal, 0o660)
        os.replace(temporal, str(destino))

    except (OSError, ValueError, TypeError) as error:
        try:
            os.unlink(temporal)
        except OSError:
            pass

        raise ErrorArchivo(
            "No se pudo guardar el archivo {}.".format(nombre)
        ) from error

    return destino


def guardar_json(inventario):
    validar_inventario(inventario)

    def escribir(archivo):
        contenido = {
            "total": len(inventario),
            "dispositivos": inventario
        }

        json.dump(
            contenido,
            archivo,
            ensure_ascii=False,
            indent=2,
            allow_nan=False
        )
        archivo.write("\n")

    return escribir_archivo("inventario.json", escribir)


def proteger_valor_csv(valor):
    if valor.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + valor

    return valor


def guardar_csv(inventario):
    validar_inventario(inventario)

    def escribir(archivo):
        escritor = csv.DictWriter(
            archivo,
            fieldnames=CAMPOS
        )
        escritor.writeheader()

        for dispositivo in inventario:
            fila = {
                campo: proteger_valor_csv(dispositivo[campo])
                for campo in CAMPOS
            }
            escritor.writerow(fila)

    return escribir_archivo("inventario.csv", escribir)


def guardar_inventario(inventario):
    validar_inventario(inventario)

    ruta_json = guardar_json(inventario)
    ruta_csv = guardar_csv(inventario)

    return {
        "json": ruta_json,
        "csv": ruta_csv
    }


def leer_inventario():
    ruta = RUTA_DATOS / "inventario.json"

    try:
        with ruta.open("r", encoding="utf-8") as archivo:
            contenido = json.load(archivo)

    except FileNotFoundError as error:
        raise ErrorArchivo(
            "No existe un inventario guardado."
        ) from error

    except (OSError, UnicodeError, ValueError) as error:
        raise ErrorArchivo(
            "No se pudo leer el inventario JSON."
        ) from error

    if not isinstance(contenido, dict):
        raise ErrorArchivo("La estructura del inventario es invalida.")

    inventario = contenido.get("dispositivos")

    validar_inventario(inventario)

    if contenido.get("total") != len(inventario):
        raise ErrorArchivo(
            "El total de dispositivos no coincide con el inventario."
        )

    return inventario
