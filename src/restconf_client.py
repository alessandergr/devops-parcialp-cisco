import json
import os
import sys
from getpass import getpass

import requests

HOST = "192.168.56.101"
BASE = f"https://{HOST}/restconf/data/ietf-interfaces:interfaces"
NOMBRE = "Loopback101"
DESCRIPCION = "DEVOPS-MANAGER-RESTCONF"
TIPO = "iana-if-type:softwareLoopback"

def consultar(session):
    respuesta = session.get(BASE, timeout=20)
    respuesta.raise_for_status()
    print(f"GET: HTTP {respuesta.status_code}")
    return respuesta.json()["ietf-interfaces:interfaces"]["interface"]

def validar(datos):
    if (
        datos.get("name") != NOMBRE
        or datos.get("description") != DESCRIPCION
        or datos.get("type") != TIPO
        or datos.get("enabled") is not True
    ):
        raise ValueError("Configuracion de interfaz no valida")

def ejecutar():
    with requests.Session() as session:
        session.auth = ("devops", getpass("Clave del router: "))
        session.headers.update({
            "Accept": "application/yang-data+json",
            "Content-Type": "application/yang-data+json"
        })

        session.verify = os.getenv("ROUTER_CA") or True
        if os.getenv("ROUTER_LAB_TLS") == "1":
            print("Aviso: certificado no verificado, laboratorio local.")
            session.verify = False

        antes = consultar(session)
        print("ANTES:", [i["name"] for i in antes])

        existente = next(
            (i for i in antes if i["name"] == NOMBRE), None
        )

        datos = {
            "name": NOMBRE,
            "description": DESCRIPCION,
            "type": TIPO,
            "enabled": True
        }

        validar(datos)

        if existente is None:
            payload = {"ietf-interfaces:interface": datos}
            respuesta = session.put(
                f"{BASE}/interface={NOMBRE}",
                json=payload,
                timeout=20
            )
            respuesta.raise_for_status()
            print(f"PUT: HTTP {respuesta.status_code}")
        else:
            validar(existente)
            print("Interfaz existente: sin cambios.")

        despues = consultar(session)
        resultado = next(
            (i for i in despues if i["name"] == NOMBRE), {}
        )
        validar(resultado)

        print("DESPUES:", [i["name"] for i in despues])
        print(json.dumps(resultado, indent=2))
        print("RESTCONF: VALIDACION EXITOSA")

if __name__ == "__main__":
    try:
        ejecutar()
    except (requests.RequestException, ValueError, KeyError) as error:
        print(f"Error RESTCONF: {error}", file=sys.stderr)
        sys.exit(1)
