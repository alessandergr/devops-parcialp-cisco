import sys
from getpass import getpass

from ncclient import manager

HOST = "192.168.56.101"
NOMBRE = "Loopback102"
DESCRIPCION = "DEVOPS-MANAGER-NETCONF"
NS = "{urn:ietf:params:xml:ns:yang:ietf-interfaces}"

FILTRO = """
<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
        <name>Loopback102</name>
    </interface>
</interfaces>
"""

CONFIG = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"
                   nc:operation="create">
            <name>Loopback102</name>
            <description>DEVOPS-MANAGER-NETCONF</description>
            <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:softwareLoopback</type>
            <enabled>true</enabled>
        </interface>
    </interfaces>
</config>
"""

def consultar(conexion):
    respuesta = conexion.get_config(
        source="running",
        filter=("subtree", FILTRO)
    )
    print(respuesta.data_xml)
    return respuesta.data.find(f".//{NS}interface")

def ejecutar():
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

        print("NETCONF: CONEXION EXITOSA")
        print("Sesion:", conexion.session_id)

        conexion.lock(target="running")
        print("LOCK: OK")

        try:
            print("ESTADO ANTES:")
            antes = consultar(conexion)

            if antes is None:
                respuesta = conexion.edit_config(
                    target="running",
                    config=CONFIG
                )
                if not respuesta.ok:
                    raise RuntimeError("Edicion no confirmada")
                print("EDIT-CONFIG: OK")
            else:
                print("Interfaz existente: sin cambios.")

            print("ESTADO DESPUES:")
            despues = consultar(conexion)

            if despues is None:
                raise ValueError("Interfaz no encontrada")

            if despues.findtext(NS + "name") != NOMBRE:
                raise ValueError("Nombre incorrecto")

            if despues.findtext(NS + "description") != DESCRIPCION:
                raise ValueError("Descripcion incorrecta")

            print("NETCONF: VALIDACION EXITOSA")

        finally:
            conexion.unlock(target="running")
            print("UNLOCK: OK")

if __name__ == "__main__":
    try:
        ejecutar()
    except Exception as error:
        print(f"Error NETCONF: {error}", file=sys.stderr)
        sys.exit(1)
