import json
from pathlib import Path
from datetime import datetime, timezone
from webex_client import WebexClient

BASE_DIR = Path(__file__).resolve().parent.parent


def generar_reporte():
    ruta = BASE_DIR / "data" / "inventario.json"

    with ruta.open(encoding="utf-8") as archivo:
        inventario = json.load(archivo)

    equipos = inventario["dispositivos"]
    activos = sum(e["estado"] == "Reachable" for e in equipos)
    otros = len(equipos) - activos

    fecha = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    lineas = [
        "# DevOps Manager - Reporte de red",
        f"Fecha: {fecha}",
        "",
        f"**Total de dispositivos:** {len(equipos)}",
        f"**Disponibles:** {activos}",
        f"**Otros estados:** {otros}",
        "",
        "## Detalle de dispositivos"
    ]

    for equipo in equipos:
        lineas.append(
            f"- **{equipo['nombre']}** | "
            f"IP: {equipo['ip']} | "
            f"Estado: {equipo['estado']}"
        )

    mensaje = "\n".join(lineas)

    carpeta = BASE_DIR / "data" / "reportes"
    carpeta.mkdir(exist_ok=True)

    nombre = datetime.now(timezone.utc).strftime(
        "reporte_%Y%m%d_%H%M%S_%f.md"
    )

    ruta_reporte = carpeta / nombre
    ruta_reporte.write_text(mensaje, encoding="utf-8")
    ruta_reporte.chmod(0o640)

    return mensaje, ruta_reporte


if __name__ == "__main__":
    mensaje, ruta = generar_reporte()
    print(f"Reporte generado: {ruta.name}")

    WebexClient().enviar_mensaje(mensaje)
    print("Reporte enviado correctamente a Webex.")
