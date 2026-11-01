
import unittest

from validators import (
    ErrorValidacion,
    validar_opcion,
    obtener_texto,
    validar_ip,
    normalizar_dispositivos,
    resumir_inventario
)


class TestValidadores(unittest.TestCase):

    def test_opcion_valida(self):
        resultado = validar_opcion(" 2 ", {"0", "1", "2"})
        self.assertEqual(resultado, "2")

    def test_opcion_invalida(self):
        with self.assertRaises(ErrorValidacion):
            validar_opcion("9", {"0", "1", "2"})

    def test_opcion_no_texto(self):
        with self.assertRaises(ErrorValidacion):
            validar_opcion(2, {"1", "2"})

    def test_texto_valido(self):
        self.assertEqual(
            obtener_texto("  Router1  "),
            "Router1"
        )

    def test_texto_vacio(self):
        self.assertEqual(
            obtener_texto(""),
            "No disponible"
        )

    def test_texto_incorrecto(self):
        with self.assertRaises(ErrorValidacion):
            obtener_texto(123)

    def test_ipv4_valida(self):
        self.assertEqual(
            validar_ip("192.168.1.1"),
            "192.168.1.1"
        )

    def test_ipv6_valida(self):
        self.assertEqual(
            validar_ip("2001:db8::1"),
            "2001:db8::1"
        )

    def test_ip_no_disponible(self):
        self.assertEqual(
            validar_ip(None),
            "No disponible"
        )

    def test_ip_invalida(self):
        with self.assertRaises(ErrorValidacion):
            validar_ip("999.999.999.999")

    def test_inventario_no_lista(self):
        with self.assertRaises(ErrorValidacion):
            normalizar_dispositivos({"id": "1"})

    def test_dispositivo_invalido(self):
        with self.assertRaises(ErrorValidacion):
            normalizar_dispositivos(["dispositivo_invalido"])

    def test_identificador_duplicado(self):
        dispositivos = [
            {"id": "1", "hostname": "sw1"},
            {"id": "1", "hostname": "sw2"}
        ]

        with self.assertRaises(ErrorValidacion):
            normalizar_dispositivos(dispositivos)

    def test_normalizacion_correcta(self):
        dispositivos = [
            {
                "id": "1",
                "hostname": "sw1",
                "family": "Switches and Hubs",
                "managementIpAddress": "192.0.2.10",
                "reachabilityStatus": "Reachable"
            }
        ]

        resultado = normalizar_dispositivos(dispositivos)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nombre"], "sw1")
        self.assertEqual(resultado[0]["ip"], "192.0.2.10")
        self.assertEqual(resultado[0]["estado"], "Reachable")

    def test_ip_invalida_en_inventario(self):
        dispositivos = [
            {
                "id": "1",
                "hostname": "sw1",
                "managementIpAddress": "direccion-invalida"
            }
        ]

        with self.assertRaises(ErrorValidacion):
            normalizar_dispositivos(dispositivos)

    def test_resumen_correcto(self):
        inventario = [
            {"tipo": "Switch", "estado": "Reachable"},
            {"tipo": "Switch", "estado": "Reachable"},
            {"tipo": "Router", "estado": "Unreachable"}
        ]

        resultado = resumir_inventario(inventario)

        self.assertEqual(resultado["total"], 3)
        self.assertEqual(resultado["por_tipo"]["Switch"], 2)
        self.assertEqual(resultado["por_tipo"]["Router"], 1)
        self.assertEqual(resultado["por_estado"]["Reachable"], 2)
        self.assertEqual(resultado["por_estado"]["Unreachable"], 1)

    def test_resumen_invalido(self):
        with self.assertRaises(ErrorValidacion):
            resumir_inventario("datos_incorrectos")


if __name__ == "__main__":
    unittest.main()
