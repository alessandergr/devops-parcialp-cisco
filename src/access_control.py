
import grp
import os
import pwd


PERMISOS_USUARIOS = {
    "devasc": {
        "actualizar", "consultar", "exportar",
        "resumen", "conexion", "registros", "buscar"
    },
    "adminred": {
        "consultar", "exportar", "resumen",
        "registros", "buscar"
    },
    "operador1": {
        "consultar", "exportar", "resumen", "buscar"
    },
    "auditor1": {
        "consultar", "resumen", "registros", "buscar"
    }
}

GRUPOS_REQUERIDOS = {
    "devasc": {"netops"},
    "adminred": {"administradores", "netops"},
    "operador1": {"netops"},
    "auditor1": {"auditoria"}
}


def identificar_usuario():
    return pwd.getpwuid(os.getuid()).pw_name


def obtener_grupos_activos():
    identificadores = set(os.getgroups())
    identificadores.add(os.getegid())

    try:
        return {
            grp.getgrgid(identificador).gr_name
            for identificador in identificadores
        }
    except KeyError:
        return set()


def obtener_permisos():
    usuario = identificar_usuario()

    if usuario not in PERMISOS_USUARIOS:
        return usuario, None

    grupos = obtener_grupos_activos()
    requeridos = GRUPOS_REQUERIDOS[usuario]

    if not requeridos.issubset(grupos):
        return usuario, None

    return usuario, PERMISOS_USUARIOS[usuario]
