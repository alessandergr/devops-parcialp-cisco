import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class WebexClient:
    def __init__(self):
        self.token = os.getenv("WEBEX_BOT_TOKEN", "")
        self.room_name = os.getenv("WEBEX_ROOM_NAME", "")
        self.base_url = "https://webexapis.com/v1"

        if not self.token or not self.room_name:
            raise ValueError("Falta configurar Webex en .env")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def obtener_espacio(self):
        respuesta = requests.get(
            f"{self.base_url}/rooms",
            headers=self.headers,
            timeout=15
        )
        respuesta.raise_for_status()

        espacios = respuesta.json().get("items", [])
        for espacio in espacios:
            if espacio["title"] == self.room_name:
                return espacio["id"]

        raise ValueError("No se encontro el espacio de Webex")

    def enviar_mensaje(self, mensaje):
        room_id = self.obtener_espacio()

        respuesta = requests.post(
            f"{self.base_url}/messages",
            headers=self.headers,
            json={"roomId": room_id, "markdown": mensaje},
            timeout=15
        )
        respuesta.raise_for_status()
        return respuesta.json()


if __name__ == "__main__":
    try:
        cliente = WebexClient()
        cliente.enviar_mensaje(
            "**DevOps Manager - Conexion exitosa**\n\n"
            "Sistema de automatizacion Cisco conectado a Webex.\n"
            "Notificaciones operativas habilitadas."
        )
        print("Mensaje enviado correctamente a Webex.")
    except (requests.RequestException, ValueError) as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)
