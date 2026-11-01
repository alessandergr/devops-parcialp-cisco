# Inventario de Dispositivos Cisco

Proyecto desarrollado para el curso **DevOps Fundamentos**, utilizando Python y Linux en la máquina virtual Cisco DEVASC VM.

La aplicación se conecta a la API REST de Cisco Catalyst Center Sandbox para obtener información de dispositivos de red, consultar sus características, realizar búsquedas y exportar inventarios en formatos JSON y CSV.

También incorpora control de acceso mediante usuarios Linux y registros de actividad.

## 1. Requisitos

Para ejecutar el proyecto se necesita:

- Cisco DEVASC VM con Ubuntu Linux.
- Python 3.8 y pip.
- Conexión a Internet.
- Credenciales de acceso a Cisco Catalyst Center Sandbox.
- Herramientas de administración de permisos Linux y ACL.

## 2. Instalación

Abrir una terminal en Cisco DEVASC VM y acceder al proyecto:

```bash
cd ~/devops-parcial
```

Instalar las dependencias de Python:

```bash
python3 -m pip install --user -r requirements.txt
```

## 3. Configuración de la API

Si todavía no existe el archivo `.env`, crearlo utilizando la plantilla:

```bash
cp -n .env.example .env
```

Editar el archivo `.env`:

```bash
nano .env
```

Configurar los datos de conexión:

```env
CISCO_BASE_URL=https://sandboxdnac.cisco.com
CISCO_USERNAME=tu_usuario
CISCO_PASSWORD=tu_contrasena
CISCO_TIMEOUT=10
CISCO_VERIFY_TLS=true
```

Reemplazar el usuario y la contraseña por las credenciales autorizadas del Sandbox.

Guardar el archivo y proteger las credenciales:

```bash
chmod 600 .env
```

**Nota:** En el entorno de laboratorio DEVASC VM se detectó un problema de validación del certificado del Sandbox. Por ese motivo, la configuración utilizada en las pruebas establece `CISCO_VERIFY_TLS=false`. Esta opción desactiva la verificación de identidad del servidor y solo debe considerarse una excepción para el laboratorio, no una configuración de producción.

Si el archivo `.env` ya está configurado correctamente, no es necesario volver a crearlo.

## 4. Configuración de usuarios y permisos

Ejecutar el script de configuración Linux:

```bash
sudo bash scripts/configurar_linux.sh
```

Este script configura los usuarios, grupos, permisos de archivos y listas de control de acceso (ACL) necesarios para el proyecto.

Para comprobar que los permisos se aplicaron correctamente:

```bash
sudo bash scripts/verificar_permisos.sh
```

## 5. Ejecución del programa

Desde la carpeta principal del proyecto, ejecutar:

```bash
python3 src/main.py
```

La aplicación presenta un menú interactivo con las siguientes funcionalidades:

| Opción | Funcionalidad |
|---|---|
| 1 | Actualizar el inventario desde Cisco |
| 2 | Consultar el inventario de dispositivos |
| 3 | Exportar el inventario a JSON y CSV |
| 4 | Consultar el resumen del inventario |
| 5 | Comprobar la conexión con Cisco |
| 6 | Consultar registros de actividad |
| 7 | Buscar dispositivos y visualizar detalles |
| 0 | Salir del programa |

Las opciones disponibles dependen del usuario Linux que ejecute la aplicación.

Para comenzar, se recomienda actualizar el inventario mediante la **opción 1** desde la cuenta `devasc`. Después se podrán consultar, buscar y exportar los dispositivos obtenidos.

## 6. Usuarios del sistema

| Usuario | Permisos principales |
|---|---|
| `devasc` | Actualizar, consultar, buscar, exportar y revisar registros |
| `adminred` | Consultar, buscar, exportar y revisar registros |
| `operador1` | Consultar, buscar y exportar inventarios |
| `auditor1` | Consultar, buscar y revisar registros en modo lectura |

El acceso está controlado mediante usuarios, grupos y permisos del sistema operativo.

Las credenciales de Cisco se almacenan en `.env` y están protegidas contra el acceso de usuarios no autorizados.

## 7. Archivos generados

Después de consultar y exportar el inventario, la aplicación utiliza los siguientes archivos:

| Archivo | Descripción |
|---|---|
| `data/inventario.json` | Inventario almacenado en formato JSON |
| `data/inventario.csv` | Inventario exportado en formato CSV |
| `logs/app.log` | Registro de solicitudes y operaciones de la API |

Los datos provienen de Cisco Catalyst Center Sandbox. Durante las pruebas se obtuvieron cuatro dispositivos: `sw1`, `sw2`, `sw3` y `sw4`.

## 8. Pruebas y verificación

Para ejecutar todas las pruebas automatizadas de Python:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py" -v
```

Estas pruebas comprueban la validación de datos, autenticación, respuestas de la API y manejo de errores HTTP.

Para verificar los permisos Linux:

```bash
sudo bash scripts/verificar_permisos.sh
```

También es posible comprobar directamente la conexión con Cisco:

```bash
python3 src/api_client.py
```

Para consultar los últimos registros con el usuario auditor:

```bash
sudo -u auditor1 tail -n 10 logs/app.log
```

## 9. Estructura principal

```text
devops-parcial/
├── src/                 # Código Python de la aplicación
├── scripts/             # Configuración y verificación Linux
├── tests/               # Pruebas automatizadas
├── data/                # Inventarios JSON y CSV
├── logs/                # Registros de actividad
├── docs/                # Documentación adicional
├── .env.example         # Plantilla de configuración
├── requirements.txt     # Dependencias Python
└── README.md            # Instrucciones del proyecto
```

---
