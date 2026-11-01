
#!/bin/bash

# Devops Parcial - Configuracion de usuarios, grupos y permisos
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Ejecute este script con sudo."
    exit 1
fi

RUTA_PROYECTO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
PROPIETARIO="devasc"

for comando in getent useradd usermod groupadd setfacl; do
    if ! command -v "$comando" >/dev/null 2>&1; then
        echo "ERROR: No se encontro el comando $comando."
        exit 1
    fi
done

if ! id "$PROPIETARIO" >/dev/null 2>&1; then
    echo "ERROR: El usuario $PROPIETARIO no existe."
    exit 1
fi

crear_grupo() {
    local grupo="$1"

    if getent group "$grupo" >/dev/null; then
        echo "Grupo existente: $grupo"
    else
        groupadd "$grupo"
        echo "Grupo creado: $grupo"
    fi
}

crear_usuario() {
    local usuario="$1"
    local grupo="$2"

    if getent passwd "$usuario" >/dev/null; then
        if [ "$(id -gn "$usuario")" != "$grupo" ]; then
            echo "ERROR: $usuario tiene un grupo principal distinto de $grupo."
            return 1
        fi

        echo "Usuario existente: $usuario"
    else
        useradd -m -s /bin/bash -g "$grupo" "$usuario"
        echo "Usuario creado: $usuario"
    fi
}

agregar_grupo_secundario() {
    local usuario="$1"
    local grupo="$2"

    if [[ " $(id -nG "$usuario") " == *" $grupo "* ]]; then
        echo "$usuario ya pertenece a $grupo"
    else
        usermod -aG "$grupo" "$usuario"
        echo "$usuario agregado al grupo $grupo"
    fi
}

configurar_directorio() {
    local carpeta="$1"
    local grupo="$2"
    local permisos="$3"

    mkdir -p "$RUTA_PROYECTO/$carpeta"
    chown "$PROPIETARIO:$grupo" "$RUTA_PROYECTO/$carpeta"
    chmod "$permisos" "$RUTA_PROYECTO/$carpeta"
}

configurar_archivos() {
    local carpeta="$1"
    local patron="$2"
    local grupo="$3"
    local permisos="$4"
    local archivo

    for archivo in "$RUTA_PROYECTO/$carpeta"/$patron; do
        [ -f "$archivo" ] || continue

        chown "$PROPIETARIO:$grupo" "$archivo"
        chmod "$permisos" "$archivo"
    done
}

echo "=== CONFIGURACION DEVOPS PARCIAL ==="

# Administracion de grupos

crear_grupo administradores
crear_grupo netops
crear_grupo auditoria

# Administracion de usuarios

crear_usuario adminred administradores
crear_usuario operador1 netops
crear_usuario auditor1 auditoria

# Grupos secundarios

agregar_grupo_secundario adminred netops
agregar_grupo_secundario devasc netops

# Permisos de directorios

configurar_directorio src administradores 2775
configurar_directorio scripts administradores 2770
configurar_directorio tests administradores 2770
configurar_directorio docs administradores 2775
configurar_directorio data netops 2770
configurar_directorio logs administradores 2750

# Permisos de archivos del proyecto

configurar_archivos src '*.py' administradores 664
configurar_archivos scripts '*.sh' administradores 660
configurar_archivos tests '*.py' administradores 660

for archivo in README.md requirements.txt .env.example .gitignore; do
    if [ -f "$RUTA_PROYECTO/$archivo" ]; then
        chown "$PROPIETARIO:administradores" "$RUTA_PROYECTO/$archivo"
        chmod 664 "$RUTA_PROYECTO/$archivo"
    fi
done

# Inventarios: escritura para netops y lectura para auditoria

setfacl -m g:auditoria:r-x "$RUTA_PROYECTO/data"

setfacl -d -m \
    u::rwx,g::rwx,g:auditoria:r-x,m::rwx,o::--- \
    "$RUTA_PROYECTO/data"

for archivo in data/inventario.json data/inventario.csv; do
    if [ -f "$RUTA_PROYECTO/$archivo" ]; then
        chgrp netops "$RUTA_PROYECTO/$archivo"
        chmod 660 "$RUTA_PROYECTO/$archivo"
        setfacl -m g:auditoria:r-- "$RUTA_PROYECTO/$archivo"
    fi
done

# Registros: escritura exclusiva del propietario devasc

RUTA_LOGS="$RUTA_PROYECTO/logs"

# Eliminar ACL anteriores y aplicar la politica restringida

setfacl -b "$RUTA_LOGS"
setfacl -k "$RUTA_LOGS"

chmod 2750 "$RUTA_LOGS"

setfacl -m \
    u::rwx,g::r-x,g:auditoria:r-x,m::r-x,o::--- \
    "$RUTA_LOGS"

setfacl -d -m \
    u::rwx,g::r-x,g:auditoria:r-x,m::r-x,o::--- \
    "$RUTA_LOGS"

# Proteger el registro principal existente

if [ -f "$RUTA_LOGS/app.log" ]; then

    if [ -L "$RUTA_LOGS/app.log" ]; then
        echo "ERROR: app.log no puede ser un enlace simbolico."
        exit 1
    fi

    chown "$PROPIETARIO:administradores" "$RUTA_LOGS/app.log"

    setfacl -b "$RUTA_LOGS/app.log"
    chmod 640 "$RUTA_LOGS/app.log"

    setfacl -m \
        u::rw-,g::r--,g:auditoria:r--,m::r--,o::--- \
        "$RUTA_LOGS/app.log"
fi

# Proteccion de credenciales locales

if [ -f "$RUTA_PROYECTO/.env" ]; then
    chown "$PROPIETARIO:$PROPIETARIO" "$RUTA_PROYECTO/.env"
    chmod 600 "$RUTA_PROYECTO/.env"
fi

echo "Configuracion finalizada correctamente."
