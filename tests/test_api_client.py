
import unittest
from unittest.mock import Mock, patch

import requests

from config import ConfiguracionCisco
from api_client import (
    ErrorAPI,
    RUTA_INVENTARIO,
    consultar_inventario,
    obtener_token,
    realizar_solicitud,
    validar_json
)


def crear_respuesta(estado=200, datos=None, tipo="application/json"):
    respuesta = Mock()
    respuesta.status_code = estado
    respuesta.headers = {"Content-Type": tipo}
    respuesta.json.return_value = datos
    return respuesta


class TestClienteAPI(unittest.TestCase):

    def setUp(self):
        self.configuracion = ConfiguracionCisco(
            url_base="https://sandboxdnac.cisco.com",
            usuario="USUARIO_PRUEBA",
            clave="CLAVE_PRUEBA",
            verificar_tls=True,
            tiempo_espera=5
        )

    def test_obtener_token_correcto(self):
        respuesta = crear_respuesta(datos={"Token": "TOKEN_PRUEBA"})

        with patch("api_client.requests.request", return_value=respuesta) as solicitud:
            token = obtener_token(self.configuracion)

        self.assertEqual(token, "TOKEN_PRUEBA")
        argumentos, opciones = solicitud.call_args
        self.assertEqual(argumentos[0], "POST")
        self.assertTrue(argumentos[1].endswith("/auth/token"))
        self.assertEqual(opciones["auth"].username, "USUARIO_PRUEBA")
        self.assertEqual(opciones["auth"].password, "CLAVE_PRUEBA")
        self.assertTrue(opciones["verify"])

    def test_consultar_inventario_correcto(self):
        respuestas = [
            crear_respuesta(datos={"Token": "TOKEN_PRUEBA"}),
            crear_respuesta(datos={"response": []})
        ]

        with patch("api_client.requests.request", side_effect=respuestas) as solicitud:
            inventario = consultar_inventario(self.configuracion)

        self.assertEqual(inventario, [])
        self.assertEqual(solicitud.call_count, 2)

        argumentos, opciones = solicitud.call_args_list[1]
        self.assertEqual(argumentos[0], "GET")
        self.assertTrue(argumentos[1].endswith(RUTA_INVENTARIO))
        self.assertEqual(
            opciones["headers"]["X-Auth-Token"],
            "TOKEN_PRUEBA"
        )

    def test_errores_http_cliente(self):
        for codigo in (400, 401, 403, 404, 429):
            with self.subTest(codigo=codigo):
                with patch(
                    "api_client.requests.request",
                    return_value=crear_respuesta(estado=codigo)
                ):
                    with self.assertRaisesRegex(ErrorAPI, "HTTP {}".format(codigo)):
                        realizar_solicitud(
                            "GET", RUTA_INVENTARIO, self.configuracion
                        )

    def test_errores_http_servidor(self):
        for codigo in (500, 502, 503):
            with self.subTest(codigo=codigo):
                with patch(
                    "api_client.requests.request",
                    return_value=crear_respuesta(estado=codigo)
                ):
                    with self.assertRaisesRegex(ErrorAPI, "HTTP {}".format(codigo)):
                        realizar_solicitud(
                            "GET", RUTA_INVENTARIO, self.configuracion
                        )

    def test_redireccion_inesperada(self):
        with patch(
            "api_client.requests.request",
            return_value=crear_respuesta(estado=302)
        ):
            with self.assertRaisesRegex(ErrorAPI, "Redireccion inesperada"):
                realizar_solicitud(
                    "GET", RUTA_INVENTARIO, self.configuracion
                )

    def test_estado_http_no_esperado(self):
        with patch(
            "api_client.requests.request",
            return_value=crear_respuesta(estado=201)
        ):
            with self.assertRaisesRegex(ErrorAPI, "no esperada"):
                realizar_solicitud(
                    "GET", RUTA_INVENTARIO, self.configuracion
                )

    def test_json_correcto(self):
        datos = {"response": []}
        resultado = validar_json(crear_respuesta(datos=datos))
        self.assertEqual(resultado, datos)

    def test_contenido_no_json(self):
        respuesta = crear_respuesta(
            datos=None,
            tipo="text/html"
        )

        with self.assertRaisesRegex(ErrorAPI, "contenido JSON"):
            validar_json(respuesta)

    def test_json_malformado(self):
        respuesta = crear_respuesta()
        respuesta.json.side_effect = ValueError("JSON incorrecto")

        with self.assertRaisesRegex(ErrorAPI, "JSON invalido"):
            validar_json(respuesta)

    def test_json_no_es_objeto(self):
        with self.assertRaisesRegex(ErrorAPI, "estructura JSON"):
            validar_json(crear_respuesta(datos=[]))

    def test_token_invalido(self):
        for datos in ({}, {"Token": ""}, {"Token": 123}):
            with self.subTest(datos=datos):
                with patch(
                    "api_client.requests.request",
                    return_value=crear_respuesta(datos=datos)
                ):
                    with self.assertRaisesRegex(ErrorAPI, "token valido"):
                        obtener_token(self.configuracion)

    def test_inventario_sin_lista_valida(self):
        for datos in ({}, {"response": "incorrecto"}):
            with self.subTest(datos=datos):
                respuestas = [
                    crear_respuesta(datos={"Token": "TOKEN_PRUEBA"}),
                    crear_respuesta(datos=datos)
                ]

                with patch(
                    "api_client.requests.request",
                    side_effect=respuestas
                ):
                    with self.assertRaisesRegex(ErrorAPI, "lista valida"):
                        consultar_inventario(self.configuracion)

    def test_dispositivo_con_estructura_invalida(self):
        respuestas = [
            crear_respuesta(datos={"Token": "TOKEN_PRUEBA"}),
            crear_respuesta(datos={"response": [None]})
        ]

        with patch("api_client.requests.request", side_effect=respuestas):
            with self.assertRaisesRegex(ErrorAPI, "dispositivos invalidos"):
                consultar_inventario(self.configuracion)

    def test_error_certificado_ssl(self):
        with patch(
            "api_client.requests.request",
            side_effect=requests.exceptions.SSLError("Error SSL")
        ):
            with self.assertRaisesRegex(ErrorAPI, "certificado HTTPS"):
                realizar_solicitud(
                    "GET", RUTA_INVENTARIO, self.configuracion
                )

    def test_error_tiempo_espera(self):
        with patch(
            "api_client.requests.request",
            side_effect=requests.exceptions.Timeout("Timeout")
        ):
            with self.assertRaisesRegex(ErrorAPI, "no respondio a tiempo"):
                realizar_solicitud(
                    "GET", RUTA_INVENTARIO, self.configuracion
                )

    def test_error_conexion(self):
        with patch(
            "api_client.requests.request",
            side_effect=requests.exceptions.ConnectionError("Sin conexion")
        ):
            with self.assertRaisesRegex(ErrorAPI, "conectar"):
                realizar_solicitud(
                    "GET", RUTA_INVENTARIO, self.configuracion
                )

    def test_error_solicitud_general(self):
        with patch(
            "api_client.requests.request",
            side_effect=requests.exceptions.RequestException("Fallo HTTP")
        ):
            with self.assertRaisesRegex(ErrorAPI, "solicitud HTTP"):
                realizar_solicitud(
                    "GET", RUTA_INVENTARIO, self.configuracion
                )


if __name__ == "__main__":
    unittest.main()
