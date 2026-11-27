import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import cargar_reporte_router


class TestRouterPanel(unittest.TestCase):

    def test_reporte_valido(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio)
            (base / "data").mkdir()
            reporte = {"router": "CSR1000v", "total": 4}
            (base / "data/router.json").write_text(json.dumps(reporte))

            with patch("app.__file__", str(base / "app.py")):
                self.assertEqual(
                    cargar_reporte_router()["router"], reporte
                )

    def test_reporte_ausente(self):
        with tempfile.TemporaryDirectory() as directorio:
            with patch("app.__file__", str(Path(directorio) / "app.py")):
                self.assertIsNone(cargar_reporte_router()["router"])

    def test_reporte_invalido(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio)
            (base / "data").mkdir()
            (base / "data/router.json").write_text("JSON invalido")

            with patch("app.__file__", str(base / "app.py")):
                self.assertIsNone(cargar_reporte_router()["router"])
