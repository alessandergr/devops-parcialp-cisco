# DevOps Manager - Automatización de Redes Cisco

Proyecto desarrollado para el curso **DevOps Fundamentos de IDAT**, utilizando Python y Linux en la máquina virtual Cisco DEVASC.

El proyecto parte del sistema de inventario desarrollado en el parcial. Para esta segunda versión se incorporaron herramientas de automatización de redes, monitoreo con Webex, una interfaz web, Docker y Jenkins.

## 1. Funcionalidades

- Consulta de dispositivos mediante la API de Cisco Catalyst Center.
- Búsqueda y exportación del inventario en JSON y CSV.
- Control de acceso mediante usuarios y permisos Linux.
- Visualización del inventario desde una interfaz web.
- Monitoreo y envío de reportes a Webex.
- Configuración de routers con Ansible, RESTCONF y NETCONF.
- Simulación y automatización de redes en CML.
- Pruebas y despliegue automático mediante Jenkins.

## 2. Requisitos e instalación

Para ejecutar el proyecto se necesita:

- Cisco DEVASC VM.
- Python 3.8 para las herramientas locales del laboratorio.
- Docker con Python 3.12 dentro de los contenedores.
- Jenkins y un agente con acceso a Docker.
- Router Cisco CSR1000v.
- Ansible, ncclient y Pexpect.
- Acceso a Cisco DevNet Sandbox y Webex.
- Herramientas de administración de permisos Linux y ACL.

Clonar el repositorio:

```bash
git clone https://github.com/alessandergr/devops-parcialp-cisco.git ~/devops-final
cd ~/devops-final
```

Las dependencias de requirements.txt se instalan al construir las imágenes Docker. Para ejecutar los scripts directamente en DEVASC se deben utilizar dependencias compatibles con su versión de Python.

## 3. Configuración del proyecto

Crear el archivo .env si todavía no existe:

```bash
cp -n .env.example .env
nano .env
```

Completar los datos de conexión:

```env
CISCO_BASE_URL=https://sandboxdnac.cisco.com
CISCO_USERNAME=tu_usuario
CISCO_PASSWORD=tu_contrasena
CISCO_TIMEOUT=15
CISCO_VERIFY_TLS=true
CISCO_CA_BUNDLE=

WEBEX_BOT_TOKEN=tu_token
WEBEX_ROOM_NAME=nombre_del_espacio
```

Proteger las credenciales:

```bash
chmod 600 .env
```

Configurar los usuarios, grupos y permisos Linux:

```bash
sudo bash scripts/configurar_linux.sh
```

| Usuario | Permisos principales |
|---|---|
| devasc | Actualizar, consultar, buscar y exportar |
| adminred | Consultar, buscar, exportar y revisar registros |
| operador1 | Consultar, buscar y exportar |
| auditor1 | Consultar y revisar registros en modo lectura |

Las opciones disponibles en la aplicación dependen del usuario que la ejecute. Los cambios de grupos pueden requerir iniciar sesión nuevamente.

## 4. Ejecución y monitoreo

### Menú principal

Desde el entorno Python local de DEVASC:

```bash
python3 src/main.py
```

Se mantiene el menú del proyecto parcial:

| Opción | Funcionalidad |
|---|---|
| 1 | Actualizar inventario desde Cisco |
| 2 | Consultar inventario |
| 3 | Exportar JSON y CSV |
| 4 | Consultar resumen |
| 5 | Verificar conexión con Cisco |
| 6 | Consultar registros |
| 7 | Buscar dispositivos |
| 0 | Salir |

Se recomienda actualizar primero el inventario desde el usuario devasc.

### Docker e interfaz web

Construir la imagen:

```bash
docker build -t devops-manager:local .
```

Generar el inventario y enviar un reporte a Webex:

```bash
docker run --rm \
  --user "$(id -u):$(getent group netops | cut -d: -f3)" \
  -v "$PWD/.env:/app/.env:ro" \
  -v "$PWD/data:/app/data" \
  -v "$PWD/logs:/app/logs" \
  devops-manager:local python src/monitoring.py
```

Crear el contenedor de la aplicación:

```bash
docker run -d \
  --name devops-manager \
  --restart unless-stopped \
  --group-add "$(getent group netops | cut -d: -f3)" \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  -p 127.0.0.1:8080:8080 \
  -v "$PWD/data:/app/data:ro" \
  devops-manager:local
```

Este comando se utiliza para el primer despliegue, cuando todavía no existe el contenedor.

La interfaz web está disponible en:

http://127.0.0.1:8080

Desde ella se puede consultar el inventario de Cisco y el último reporte generado del router CSR1000v.

### Monitoreo automático

Para ejecutar el monitoreo manualmente:

```bash
sh scripts/monitoreo_docker.sh
```

Para programar los reportes diarios:

```bash
crontab -e
```

Agregar la siguiente tarea:

```cron
0 13 * * * /bin/sh /home/devasc/devops-final/scripts/monitoreo_docker.sh >> /home/devasc/devops-final/logs/cron_reportes.log 2>&1
```

El horario corresponde a las 8:00 a. m. de Perú, considerando que DEVASC trabaja en UTC.

La máquina virtual y Docker deben estar activos para que se ejecute el monitoreo.

## 5. Automatización de redes Cisco

Se utilizó un router CSR1000v instalado en VirtualBox con la dirección IP 192.168.56.101 y acceso mediante SSH, RESTCONF y NETCONF.

### Ansible

```bash
ansible-playbook -i ansible/inventory_lab.ini ansible/router_lab.yml -k
```

El playbook realiza un respaldo de la configuración, crea Loopback100 y verifica los cambios.

### RESTCONF

```bash
python3 src/restconf_client.py
```

Consulta las interfaces del router y configura Loopback101 mediante solicitudes HTTP y datos JSON.

### NETCONF

```bash
/usr/bin/python3 src/netconf_client.py
```

Configura Loopback102 mediante XML y verifica el resultado antes de liberar el bloqueo de la configuración.

### Reporte del router

```bash
/usr/bin/python3 src/router_report.py
```

Genera el archivo data/router.json que utiliza la interfaz web.

### Cisco Modeling Labs (CML)

Se creó una topología con dos routers conectados entre sí:

| Router | Modelo | Dirección IP |
|---|---|---|
| R1 | CAT8000V | 10.10.10.1/30 |
| R2 | IOSv | 10.10.10.2/30 |

El archivo de la topología se encuentra en:

```text
cml/DEVOPS-MANAGER-LAB.yaml
```

Para utilizarlo, importar el archivo desde CML e iniciar los routers.

La automatización se ejecuta desde DEVASC mediante una conexión VPN al Sandbox de Cisco:

```bash
/usr/bin/python3 scripts/cml_automation.py
```

El script configura Loopback110 en R1 y comprueba la comunicación con R2.

Las direcciones IP y los datos de acceso deben adaptarse al laboratorio utilizado. En una nueva reserva de CML se debe verificar la clave SSH del servidor y actualizar su dirección en el script.

## 6. Pipeline CI/CD con Jenkins

El archivo Jenkinsfile contiene las etapas de integración y despliegue del proyecto.

El pipeline realiza las siguientes tareas:

- Obtención del código fuente.
- Construcción del entorno de pruebas.
- Ejecución de pruebas unitarias.
- Análisis de código con Bandit.
- Revisión de dependencias con pip-audit.
- Construcción de la imagen Docker.
- Escaneo de vulnerabilidades y secretos con Trivy.
- Despliegue y comprobación del servicio web.

Si la nueva versión no supera la comprobación HTTP, el script desplegar.sh restaura el contenedor anterior.

Jenkins obtiene el código directamente del repositorio de GitHub y ejecuta las pruebas, la construcción de la imagen Docker y el despliegue de la aplicación.

La ruta de datos y el grupo Linux utilizados en desplegar.sh corresponden a la configuración de DEVASC y deben revisarse si se trabaja en otro entorno.

## 7. Seguridad y pruebas

Las credenciales se almacenan en .env y los datos y registros se generan localmente. Estos archivos no se incluyen en el repositorio.

Para ejecutar las pruebas unitarias:

```bash
docker build -f Dockerfile.ci -t devops-manager-ci .
docker run --rm devops-manager-ci
```

Después de generar el inventario y los registros, verificar los permisos Linux:

```bash
sudo bash scripts/verificar_permisos.sh
```

### Resultados obtenidos

| Prueba | Resultado |
|---|---|
| Inventario Cisco | 4 dispositivos |
| Pruebas unitarias | 37 correctas |
| Permisos Linux | 49 verificaciones correctas |
| Análisis estático y dependencias | Sin hallazgos pendientes |
| Trivy | 0 vulnerabilidades HIGH y CRITICAL detectadas |
| Despliegue Jenkins | Exitoso |
| Servicio web | HTTP 200 |
| Reportes Webex | Envío exitoso |
| Ansible, RESTCONF y NETCONF | Configuraciones verificadas |
| Conectividad CML | 100% |
| Recuperación de la topología | Exitosa |
| Rollback Docker | Exitoso |

Los resultados corresponden a las pruebas realizadas en nuestro laboratorio.

### Nota sobre los certificados TLS

Durante las pruebas se encontraron problemas de validación de certificados en los laboratorios Cisco.

Para Catalyst Center se utilizó:

```env
CISCO_VERIFY_TLS=false
```

Para RESTCONF:

```bash
ROUTER_LAB_TLS=1 python3 src/restconf_client.py
```

También se utilizó una excepción temporal al exportar la topología mediante la API de CML.

Estas opciones desactivan la validación de identidad del servidor. Solo se utilizaron en el laboratorio. En otros entornos se deben utilizar certificados de confianza y mantener activa la verificación TLS.

El acceso al socket de Docker desde Jenkins debe limitarse a usuarios y código autorizados.

## 8. Estructura y control de versiones

```text
devops-final/
├── ansible/           # Playbook, inventario y roles
├── cml/               # Topología de red
├── scripts/           # Scripts de automatización
├── src/               # Código Python
├── templates/         # Interfaz web
├── tests/             # Pruebas unitarias
├── data/              # Datos generados localmente
├── logs/              # Registros locales
├── app.py             # Aplicación Flask
├── Dockerfile
├── Dockerfile.ci
├── Jenkinsfile
├── .dockerignore
├── .gitignore
├── .env.example
├── requirements.txt
└── README.md
```

El proyecto utiliza Gitflow para organizar los cambios de cada integrante:

- main: versiones estables.
- develop: integración de cambios.
- feature/: desarrollo de funcionalidades.
- release/: preparación de versiones.

### Versiones

- v1.0.0: Inventario de Dispositivos Cisco.
- v2.0.0: DevOps Manager (en preparación).

## 9. Integrantes

- Salvinia Palomino Ochoa
- Daniel Alessander Guillén Rios
- Yrsa Cueto Zarate
- Juan Espetia Torrealva
- Isaac William Gavidia Rioja

---

IDAT - DevOps Fundamentos - 2026.
