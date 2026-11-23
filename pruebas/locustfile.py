"""Prueba de estrés de la quiniela.

Ejecutar (con la aplicación levantada en http://localhost:8080):
    locust -f pruebas/locustfile.py --host http://localhost:8080 \
           --headless -u 200 -r 20 -t 1m --html pruebas/reporte.html
"""
import random
import re

from locust import HttpUser, between, task

PARTICIPANTES = ["ana", "luis", "carla", "diego", "sofia", "mateo"]


class Visitante(HttpUser):
    """Navega sin iniciar sesión: inicio, partidos, ranking y estadísticas."""

    weight = 3
    wait_time = between(1, 3)

    @task(3)
    def inicio(self):
        self.client.get("/")

    @task(3)
    def ranking(self):
        self.client.get("/ranking/")

    @task(2)
    def partidos(self):
        self.client.get("/partidos/")

    @task(1)
    def estadisticas(self):
        self.client.get("/estadisticas/")

    @task(1)
    def health(self):
        self.client.get("/health/")


class Participante(HttpUser):
    """Inicia sesión, revisa sus puntos y registra predicciones."""

    weight = 1
    wait_time = between(1, 3)

    def on_start(self):
        pagina = self.client.get("/cuentas/login/")
        token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', pagina.text).group(1)
        self.client.post(
            "/cuentas/login/",
            {"username": random.choice(PARTICIPANTES), "password": "mundial2026", "csrfmiddlewaretoken": token},
            headers={"Referer": self.host + "/cuentas/login/"},
        )

    @task(2)
    def mis_puntos(self):
        self.client.get("/mis-puntos/")

    @task(1)
    def salas(self):
        self.client.get("/salas/")

    @task(2)
    def predecir(self):
        pagina = self.client.get("/partidos/")
        ids = re.findall(r'/partidos/(\d+)/predecir/', pagina.text)
        token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', pagina.text)
        if ids and token:
            self.client.post(
                f"/partidos/{random.choice(ids)}/predecir/",
                {"goles_local": random.randint(0, 3), "goles_visitante": random.randint(0, 3),
                 "csrfmiddlewaretoken": token.group(1)},
                headers={"Referer": self.host + "/partidos/"},
                name="/partidos/[id]/predecir/",
            )
