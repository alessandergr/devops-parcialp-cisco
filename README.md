# DevOps Manager - Automatización de Redes Cisco

Proyecto desarrollado para el curso **DevOps Fundamentos de IDAT**, utilizando Python, Linux y herramientas de automatización de infraestructura de red.

DevOps Manager amplía el sistema de inventario desarrollado en el proyecto parcial, incorporando una interfaz web, monitoreo automático, configuración de routers Cisco, contenedores Docker y un pipeline CI/CD con Jenkins.

## 1. Funcionalidades

- Consulta del inventario mediante la API REST de Cisco Catalyst Center.
- Búsqueda y exportación de dispositivos en formatos JSON y CSV.
- Control de acceso mediante usuarios, grupos y permisos Linux.
- Visualización del inventario mediante una interfaz web con Flask.
- Generación de reportes y envío de alertas a Webex.
- Monitoreo automático mediante Docker y cron.
- Configuración de routers con Ansible, RESTCONF y NETCONF.
- Simulación y automatización de redes en Cisco Modeling Labs (CML).
- Integración y despliegue mediante Jenkins.
- Pruebas automatizadas, análisis de seguridad y recuperación ante fallos.

## 2. Tecnologías utilizadas

| Tecnología | Uso en el proyecto |
|---|---|
| Python | Desarrollo y automatización |
| Linux | Administración de usuarios y permisos |
| Cisco Catalyst Center | Consulta de dispositivos de red |
| Flask | Interfaz web |
| Webex | Reportes y notificaciones |
| Docker | Construcción y ejecución de contenedores |
| Jenkins | Pipeline CI/CD |
| Ansible | Configuración de routers |
| RESTCONF | Configuración mediante HTTP y JSON |
| NETCONF | Configuración mediante SSH y XML |
| CML | Simulación de redes Cisco |
| GitHub | Control de versiones |
| Cron | Programación del monitoreo |

## 3. Requisitos

- Cisco DEVASC VM con Ubuntu Linux.
- Python 3.8 para las herramientas locales del laboratorio.
- Docker para ejecutar la aplicación con Python 3.12.
- Jenkins y un agente con acceso a Docker.
- Router Cisco CSR1000v.
- Acceso a Cisco DevNet Sandbox.
- Credenciales de Cisco Catalyst Center.
- Bot y espacio de Webex.
- Ansible, ncclient y Pexpect para la automatización.
- Herramientas Linux de administración de permisos y ACL.

Las dependencias del archivo requirements.txt se instalan dentro de los contenedores Docker. Las herramientas locales requieren versiones compatibles con el Python de DEVASC.

## 4. Configuración inicial

Acceder a la carpeta del proyecto:

```bash
cd ~/devops-final
```

Crear el archivo de configuración si todavía no existe:

```bash
cp -n .env.example .env
nano .env
```

Completar las variables de conexión:

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

Proteger el archivo de credenciales:

```bash
chmod 600 .env
```

Las credenciales reales no deben almacenarse en GitHub.

## 5. Configuración de usuarios y permisos Linux

Ejecutar el script de configuración:

```bash
sudo bash scripts/configurar_linux.sh
```

El script configura los usuarios, grupos, permisos y listas de control de acceso necesarios para el funcionamiento del proyecto.

### Usuarios del sistema

| Usuario | Permisos principales |
|---|---|
| devasc | Actualizar, consultar, buscar, exportar y revisar registros |
| adminred | Consultar, buscar, exportar y revisar registros |
| operador1 | Consultar, buscar y exportar inventarios |
| auditor1 | Consultar, buscar y revisar registros en modo lectura |

Después de generar el inventario y los registros de actividad, comprobar los permisos:

```bash
sudo bash scripts/verificar_permisos.sh
```

Durante las pruebas se obtuvieron 49 verificaciones correctas de seguridad Linux.

## 6. Ejecución mediante terminal

Desde el entorno Python compatible de DEVASC:

```bash
python3 src/main.py
```

La aplicación mantiene el menú desarrollado en el proyecto parcial.

| Opción | Funcionalidad |
|---|---|
| 1 | Actualizar el inventario desde Cisco |
| 2 | Consultar el inventario |
| 3 | Exportar el inventario a JSON y CSV |
| 4 | Consultar el resumen del inventario |
| 5 | Comprobar la conexión con Cisco |
| 6 | Consultar registros de actividad |
| 7 | Buscar dispositivos y visualizar detalles |
| 0 | Salir del programa |

Las opciones disponibles dependen de los permisos del usuario Linux.

Para comenzar, se recomienda actualizar el inventario desde la cuenta devasc.

## 7. Construcción y ejecución con Docker

El proyecto utiliza un Dockerfile multietapa para separar la instalación de dependencias del entorno de ejecución.

Construir la imagen:

```bash
docker build -t devops-manager:local .
```

Generar el inventario inicial y enviar un reporte a Webex:

```bash
docker run --rm \
  --user "$(id -u):$(getent group netops | cut -d: -f3)" \
  -v "$PWD/.env:/app/.env:ro" \
  -v "$PWD/data:/app/data" \
  -v "$PWD/logs:/app/logs" \
  devops-manager:local python src/monitoring.py
```

Para el primer despliegue de la aplicación:

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

Comprobar los contenedores activos:

```bash
docker ps
```

Este comando de despliegue inicial se utiliza cuando todavía no existe el contenedor devops-manager.

## 8. Interfaz web

Acceder desde el navegador de DEVASC:

http://127.0.0.1:8080

La interfaz desarrollada con Flask permite visualizar:

- Cantidad de dispositivos registrados.
- Nombre, dirección IP y tipo de dispositivo.
- Estado de conectividad.
- Interfaces del router CSR1000v.
- Configuraciones realizadas mediante Ansible, RESTCONF y NETCONF.
- Fecha del último reporte del router.

El inventario de Catalyst Center y el router CSR1000v corresponden a entornos de laboratorio diferentes.

## 9. Webex y monitoreo automático

El sistema consulta los dispositivos Cisco, genera reportes y los envía mediante un bot de Webex.

Para ejecutar el monitoreo manualmente:

```bash
sh scripts/monitoreo_docker.sh
```

Para programar su ejecución:

```bash
crontab -e
```

Agregar la siguiente tarea:

```cron
0 13 * * * /bin/sh /home/devasc/devops-final/scripts/monitoreo_docker.sh >> /home/devasc/devops-final/logs/cron_reportes.log 2>&1
```

En el laboratorio, DEVASC utiliza la zona horaria UTC. Por ello, el reporte se encuentra programado para las 8:00 a. m. de Perú.

El monitoreo requiere que la máquina virtual y Docker se encuentren operativos.

## 10. Automatización del router Cisco

Se utilizó un router CSR1000v instalado en VirtualBox y conectado a DEVASC mediante una red de administración.

Configuración utilizada durante las pruebas:

| Parámetro | Valor |
|---|---|
| Router | CSR1000v |
| Dirección IP | 192.168.56.101 |
| SSH | Puerto 22 |
| RESTCONF | Puerto 443 |
| NETCONF | Puerto 830 |
| Usuario | devops |

Las direcciones IP y los usuarios deben adaptarse al entorno donde se ejecute el proyecto.

### Ansible

Ejecutar el playbook:

```bash
ansible-playbook -i ansible/inventory_lab.ini ansible/router_lab.yml -k
```

El playbook verifica el estado inicial, respalda la configuración, crea la interfaz Loopback100 y comprueba los cambios realizados.

También se verificó la idempotencia mediante una segunda ejecución sin cambios adicionales.

### RESTCONF

```bash
python3 src/restconf_client.py
```

El script consulta las interfaces mediante solicitudes GET y configura Loopback101 mediante una solicitud PUT con datos JSON basados en el modelo YANG.

Para utilizar un certificado CA de confianza:

```bash
ROUTER_CA=/ruta/certificado.pem python3 src/restconf_client.py
```

### NETCONF

```bash
/usr/bin/python3 src/netconf_client.py
```

El script establece una conexión NETCONF, bloquea la configuración running, crea Loopback102 mediante XML, verifica el resultado y libera el bloqueo.

### Reporte del router

```bash
/usr/bin/python3 src/router_report.py
```

Genera el archivo data/router.json, utilizado por la interfaz web para mostrar las interfaces configuradas.

Este reporte se actualiza al ejecutar el script. No corresponde a una consulta en tiempo real.

## 11. Cisco Modeling Labs (CML)

Se creó una topología personalizada denominada DEVOPS-MANAGER-LAB.

| Equipo | Modelo | Dirección IP |
|---|---|---|
| R1 | Cisco CAT8000V | 10.10.10.1/30 |
| R2 | Cisco IOSv | 10.10.10.2/30 |

Topología:

```text
R1 (CAT8000V)                  R2 (IOSv)
10.10.10.1/30                  10.10.10.2/30
     G1 --------------------------- G0/0
```

La automatización se realizó desde DEVASC mediante una conexión VPN al sandbox de Cisco y acceso SSH al servidor de consolas de CML.

```bash
/usr/bin/python3 scripts/cml_automation.py
```

El script crea Loopback110 en R1, verifica la configuración, comprueba la conectividad con R2 y guarda los cambios.

### Recuperación del laboratorio

El archivo de topología se encuentra en:

```text
cml/DEVOPS-MANAGER-LAB.yaml
```

Para recuperar el laboratorio:

1. Acceder a Cisco Modeling Labs.
2. Seleccionar la opción Import.
3. Cargar el archivo YAML.
4. Iniciar los routers.
5. Verificar las interfaces y la conectividad.

La importación y recuperación de la topología fueron comprobadas exitosamente.

Para utilizar el script en una nueva reserva, se debe actualizar la dirección del servidor CML y utilizar las credenciales correspondientes.

## 12. Pipeline CI/CD con Jenkins

El pipeline automatiza las siguientes etapas:

1. Obtención del código fuente.
2. Construcción del entorno de pruebas.
3. Ejecución de pruebas unitarias.
4. Análisis estático con Bandit.
5. Auditoría de dependencias con pip-audit.
6. Construcción de la imagen Docker.
7. Escaneo de vulnerabilidades con Trivy.
8. Detección de secretos en la imagen.
9. Despliegue automático.
10. Verificación del servicio mediante HTTP.

El archivo Jenkinsfile contiene la definición del pipeline.

Durante las pruebas realizadas en DEVASC, Jenkins obtuvo el código desde una carpeta local del agente. La integración con el repositorio GitHub se encuentra en preparación.

El script de despliegue utiliza la ruta /home/devasc/devops-final/data y el identificador de grupo 1001 del laboratorio. Estos valores deben revisarse si se utiliza otro entorno.

### Recuperación ante fallos

El script scripts/desplegar.sh conserva la versión anterior del contenedor antes de desplegar una nueva imagen.

Si la nueva versión no supera la comprobación HTTP, se restaura automáticamente el contenedor anterior.

Este procedimiento fue probado en un entorno aislado sin afectar la aplicación principal.

## 13. Seguridad del proyecto

Se aplicaron las siguientes medidas:

- Control de acceso mediante usuarios y grupos Linux.
- Permisos y listas ACL sobre archivos y directorios.
- Protección de credenciales mediante archivos de entorno.
- Contenedores ejecutados sin privilegios de administrador.
- Eliminación de capacidades adicionales del contenedor.
- Restricción del acceso web a la máquina local.
- Verificación de claves SSH para las conexiones automatizadas.
- Análisis de código, dependencias e imágenes Docker.

### Certificados TLS

Durante las pruebas se encontraron certificados no reconocidos en los entornos Cisco de laboratorio.

Para Catalyst Center se utilizó temporalmente:

```env
CISCO_VERIFY_TLS=false
```

Para RESTCONF en el router local:

```bash
ROUTER_LAB_TLS=1 python3 src/restconf_client.py
```

También se utilizó una excepción TLS temporal para exportar la topología mediante la API de CML.

Estas excepciones desactivan la comprobación de identidad del servidor y se utilizaron únicamente dentro de los laboratorios autorizados.

En producción se deben utilizar certificados de confianza y mantener activa la validación TLS.

El agente Jenkins tiene acceso al socket de Docker, por lo que debe utilizarse únicamente con código y usuarios autorizados.

## 14. Pruebas y resultados

Ejecutar las pruebas unitarias dentro de Docker:

```bash
docker build -f Dockerfile.ci -t devops-manager-ci .
docker run --rm devops-manager-ci
```

Resultados obtenidos durante las pruebas del laboratorio:

| Prueba | Resultado |
|---|---|
| Consulta de Catalyst Center | 4 dispositivos obtenidos |
| Pruebas unitarias | 37 correctas |
| Seguridad Linux | 49 verificaciones correctas |
| Bandit | Sin hallazgos pendientes en el alcance analizado |
| pip-audit | Sin vulnerabilidades conocidas detectadas |
| Trivy | Sin vulnerabilidades HIGH o CRITICAL detectadas |
| Despliegue Jenkins | Exitoso |
| Verificación web | HTTP 200 |
| Reportes Webex | Envío exitoso |
| Ansible | Configuración e idempotencia verificadas |
| RESTCONF | Configuración validada |
| NETCONF | Configuración validada |
| Conectividad CML | 100% de respuestas |
| Recuperación CML | Exitosa |
| Rollback Docker | Exitoso |

Los resultados de seguridad corresponden a las versiones y condiciones del momento de las pruebas.

## 15. Archivos generados

| Archivo | Descripción |
|---|---|
| data/inventario.json | Inventario de dispositivos |
| data/inventario.csv | Inventario en formato CSV |
| data/router.json | Reporte de interfaces del router |
| data/reportes/ | Reportes de monitoreo |
| logs/app.log | Registro de actividad |
| logs/cron_reportes.log | Registro del monitoreo programado |

Los datos, registros y credenciales se generan o configuran localmente y no se almacenan en el repositorio público.

## 16. Estructura del proyecto

```text
devops-final/
├── ansible/             # Inventario, playbook y roles
├── cml/                 # Topología virtual Cisco
├── scripts/             # Administración y automatización
├── src/                 # Módulos Python
├── templates/           # Interfaz web
├── tests/               # Pruebas unitarias
├── data/                # Datos generados localmente
├── logs/                # Registros locales
├── app.py               # Aplicación Flask
├── Dockerfile           # Imagen de la aplicación
├── Dockerfile.ci        # Entorno de pruebas
├── Jenkinsfile          # Pipeline CI/CD
├── .dockerignore        # Exclusiones de Docker
├── .gitignore           # Archivos ignorados por Git
├── .env.example         # Plantilla de credenciales
├── requirements.txt     # Dependencias
└── README.md            # Documentación del proyecto
```

## 17. Control de versiones - Gitflow

El desarrollo se organiza mediante las siguientes ramas:

- main: versiones estables.
- develop: integración de funcionalidades.
- feature/: desarrollo de funcionalidades.
- release/: preparación de versiones finales.

Los cambios se integran mediante Pull Requests, conservando el historial del proyecto parcial.

### Versiones

- v1.0.0: Inventario de Dispositivos Cisco.
- v2.0.0: DevOps Manager - Automatización de Redes Cisco (en preparación).

## 18. Integrantes

- Salvinia Palomino Ochoa
- Daniel Alessander Guillén Rios
- Yrsa Cueto Zarate
- Juan Espetia Torrealva
- Isaac William Gavidia Rioja

---

Proyecto académico - DevOps Fundamentos - IDAT 2026.
