import json
from pathlib import Path
from flask import Flask, render_template

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent

@app.route("/")
def inicio():
    ruta = BASE_DIR / "data" / "inventario.json"

    with ruta.open(encoding="utf-8") as archivo:
        inventario = json.load(archivo)

    dispositivos = inventario["dispositivos"]

    return render_template(
        "index.html",
        dispositivos=dispositivos,
        total=len(dispositivos)
    )


@app.context_processor
def cargar_reporte_router():
    ruta = Path(__file__).resolve().parent / "data" / "router.json"
    try:
        reporte = json.loads(ruta.read_text())
    except (OSError, ValueError):
        reporte = None
    return {"router": reporte}

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=False)
