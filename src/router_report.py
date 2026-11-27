import json
import sys
from datetime import datetime, timezone
from getpass import getpass
from pathlib import Path

from ncclient import manager

HOST = "192.168.56.101"
NS = "{urn:ietf:params:xml:ns:yang:ietf-interfaces}"
BASE = Path(__file__).resolve().parent.parent

METODOS = {
    "GigabitEthernet1": "Administracion",
    "Loopback100": "Ansible",
    "Loopback101": "RESTCONF",
    "Loopback102": "NETCONF"
}

def generar_reporte():
    with manager.connect(
        host=HOST,
        port=830,
        username="devops",
        password=getpass("Clave del router: "),
        hostkey_verify=True,
        allow_agent=False,
        look_for_keys=False,
        device_params={"name": "iosxe"},
        timeout=30
    ) as conexion:
        respuesta = conexion.get_config(
            source="running",
            filter=("subtree",
                '<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"/>')
        )

        interfaces = []

        for interfaz in respuesta.data.findall(f".//{NS}interface"):
            nombre = interfaz.findtext(NS + "name")
            interfaces.append({
                "nombre": nombre,
                "descripcion": interfaz.findtext(NS + "description") or "",
                "habilitada": interfaz.findtext(NS + "enabled") == "true",
                "metodo": METODOS.get(nombre, "Otro")
            })

        nombres = {i["nombre"] for i in interfaces}

        if not set(METODOS).issubset(nombres):
            raise ValueError("Faltan interfaces del laboratorio")

        reporte = {
            "router": "CSR1000v",
            "ip": HOST,
            "fecha": datetime.now(timezone.utc).isoformat(),
            "total": len(interfaces),
            "interfaces": interfaces
        }

        ruta = BASE / "data" / "router.json"
        temporal = ruta.with_suffix(".tmp")
        temporal.write_text(json.dumps(reporte, indent=4))
        temporal.chmod(0o640)
        temporal.replace(ruta)

        print(json.dumps(reporte, indent=4))
        print("REPORTE DEL ROUTER: EXITOSO")

if __name__ == "__main__":
    try:
        generar_reporte()
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
