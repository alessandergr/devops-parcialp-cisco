
#!/bin/bash

# Devops Parcial - Verificacion de usuarios y permisos
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Ejecute este script con sudo."
    exit 1
fi

RUTA_PROYECTO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"

CORRECTAS=0
FALLIDAS=0

for comando in runuser getfacl stat id; do
    if ! command -v "$comando" >/dev/null 2>&1; then
        echo "ERROR: Falta el comando $comando."
        exit 1
    fi
done

correcto() {
    echo "[OK] $1"
    CORRECTAS=$((CORRECTAS + 1))
}

error() {
    echo "[ERROR] $1"
    FALLIDAS=$((FALLIDAS + 1))
}

verificar_usuario() {
    local usuario="$1"
    local grupo="$2"

    if id "$usuario" >/dev/null 2>&1 &&
       [ "$(id -gn "$usuario")" = "$grupo" ]; then
        correcto "$usuario pertenece a $grupo"
    else
        error "Usuario o grupo incorrecto: $usuario"
    fi
}

verificar_grupo_secundario() {
    local usuario="$1"
    local grupo="$2"

    if id "$usuario" >/dev/null 2>&1 &&
       [[ " $(id -nG "$usuario") " == *" $grupo "* ]]; then
        correcto "$usuario pertenece al grupo $grupo"
    else
        error "$usuario no pertenece al grupo $grupo"
    fi
}

verificar_directorio() {
    local carpeta="$1"
    local esperado="$2"
    local ruta="$RUTA_PROYECTO/$carpeta"

    if [ -d "$ruta" ] &&
       [ "$(stat -c '%U:%G:%a' "$ruta")" = "$esperado" ]; then
        correcto "Directorio $carpeta: $esperado"
    else
        error "Configuracion incorrecta en $carpeta"
    fi
}

verificar_archivo() {
    local archivo="$1"
    local esperado="$2"
    local ruta="$RUTA_PROYECTO/$archivo"

    if [ -f "$ruta" ] &&
       [ ! -L "$ruta" ] &&
       [ "$(stat -c '%U:%G:%a' "$ruta")" = "$esperado" ]; then
        correcto "Archivo $archivo: $esperado"
    else
        error "Configuracion incorrecta en $archivo"
    fi
}

verificar_acceso() {
    local usuario="$1"
    local permiso="$2"
    local recurso="$3"
    local esperado="$4"

    local ruta="$RUTA_PROYECTO/$recurso"
    local resultado="denegado"

    if [ ! -e "$ruta" ]; then
        error "El recurso $recurso no existe"
        return
    fi

    if runuser -u "$usuario" -- test "$permiso" "$ruta"; then
        resultado="permitido"
    fi

    if [ "$resultado" = "$esperado" ]; then
        correcto "$usuario - $recurso: $resultado"
    else
        error "$usuario - $recurso: $resultado (esperado: $esperado)"
    fi
}

verificar_acl() {
    local carpeta="$1"

    if getfacl -cp "$RUTA_PROYECTO/$carpeta" 2>/dev/null |
       grep -qx 'default:group:auditoria:r-x'; then
        correcto "ACL heredable de auditoria en $carpeta"
    else
        error "ACL heredable incorrecta en $carpeta"
    fi
}

echo "=== VERIFICACION DEVOPS PARCIAL ==="

# Usuarios y grupos

verificar_usuario adminred administradores
verificar_usuario operador1 netops
verificar_usuario auditor1 auditoria

verificar_grupo_secundario adminred netops
verificar_grupo_secundario devasc netops

# Propietarios y permisos de directorios

verificar_directorio src "devasc:administradores:2775"
verificar_directorio scripts "devasc:administradores:2770"
verificar_directorio tests "devasc:administradores:2770"
verificar_directorio docs "devasc:administradores:2775"
verificar_directorio data "devasc:netops:2770"
verificar_directorio logs "devasc:administradores:2750"

# Archivos protegidos

verificar_archivo logs/app.log "devasc:administradores:640"
verificar_archivo .env "devasc:devasc:600"

# Permisos sobre codigo fuente

verificar_acceso adminred -w src/main.py permitido
verificar_acceso operador1 -r src/main.py permitido
verificar_acceso operador1 -w src/main.py denegado

# Permisos sobre scripts administrativos

verificar_acceso adminred -w scripts/configurar_linux.sh permitido
verificar_acceso operador1 -r scripts/configurar_linux.sh denegado
verificar_acceso auditor1 -r scripts/configurar_linux.sh denegado

# Permisos del inventario

verificar_acceso operador1 -r data/inventario.json permitido
verificar_acceso operador1 -w data permitido

verificar_acceso auditor1 -r data permitido
verificar_acceso auditor1 -w data denegado
verificar_acceso auditor1 -r data/inventario.json permitido
verificar_acceso auditor1 -w data/inventario.json denegado

# Permisos de registros

verificar_acceso devasc -w logs/app.log permitido

verificar_acceso adminred -r logs permitido
verificar_acceso adminred -w logs denegado
verificar_acceso adminred -r logs/app.log permitido
verificar_acceso adminred -w logs/app.log denegado

verificar_acceso operador1 -r logs denegado
verificar_acceso operador1 -w logs denegado
verificar_acceso operador1 -r logs/app.log denegado
verificar_acceso operador1 -w logs/app.log denegado

verificar_acceso auditor1 -r logs permitido
verificar_acceso auditor1 -w logs denegado
verificar_acceso auditor1 -r logs/app.log permitido
verificar_acceso auditor1 -w logs/app.log denegado

# Permisos sobre pruebas Python

verificar_acceso adminred -w tests/test_validators.py permitido
verificar_acceso operador1 -r tests/test_validators.py denegado

# Permisos de documentacion

verificar_acceso operador1 -r docs permitido
verificar_acceso operador1 -w docs denegado

verificar_acceso auditor1 -r docs permitido
verificar_acceso auditor1 -w docs denegado

# Proteccion de credenciales

verificar_acceso devasc -r .env permitido
verificar_acceso operador1 -r .env denegado
verificar_acceso auditor1 -r .env denegado

# ACL heredables

verificar_acl data
verificar_acl logs

# Resumen

echo
echo "=== RESULTADOS ==="
echo "Pruebas correctas: $CORRECTAS"
echo "Pruebas fallidas: $FALLIDAS"

if [ "$FALLIDAS" -ne 0 ]; then
    echo "Se detectaron problemas de seguridad."
    exit 1
fi

echo "Seguridad Linux verificada correctamente."
