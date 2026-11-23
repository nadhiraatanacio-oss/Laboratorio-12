from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Partido, Prediccion, Sala
from .puntos import calcular_fila, puntos_base


class ReglasBaseTests(TestCase):
    def test_resultado_exacto(self):
        self.assertEqual(puntos_base(2, 1, 2, 1), 5)

    def test_ganador_y_diferencia(self):
        self.assertEqual(puntos_base(3, 1, 2, 0), 5)  # gana local por 2: 3 + 2

    def test_solo_ganador(self):
        self.assertEqual(puntos_base(1, 0, 3, 0), 3)

    def test_empate_no_exacto(self):
        self.assertEqual(puntos_base(1, 1, 0, 0), 5)  # empate (3) y diferencia 0 (2)

    def test_fallo(self):
        self.assertEqual(puntos_base(0, 1, 2, 0), 0)


class BonusTests(TestCase):
    def setUp(self):
        self.u = User.objects.create_user("ana", password="x")
        base = timezone.now() - timedelta(days=10)
        self.partidos = [
            Partido.objects.create(local=f"L{i}", visitante=f"V{i}", fecha=base + timedelta(days=i), goles_local=1, goles_visitante=0)
            for i in range(4)
        ]

    def _predecir(self, partido, gl, gv, horas_antes):
        return Prediccion.objects.create(
            usuario=self.u, partido=partido, goles_local=gl, goles_visitante=gv,
            registrada=partido.fecha - timedelta(hours=horas_antes),
        )

    def test_racha_de_tres_aciertos(self):
        preds = [self._predecir(p, 2, 0, 1) for p in self.partidos[:3]]  # ganador correcto, último minuto
        fila = calcular_fila(self.u, preds)
        self.assertEqual(fila.base, 9)
        self.assertEqual(fila.racha, 2)
        self.assertEqual(fila.total, 11)

    def test_racha_se_corta_con_un_fallo(self):
        preds = [self._predecir(p, 2, 0, 1) for p in self.partidos[:2]]
        preds.append(self._predecir(self.partidos[2], 0, 2, 1))
        preds.append(self._predecir(self.partidos[3], 2, 0, 1))
        fila = calcular_fila(self.u, preds)
        self.assertEqual(fila.racha, 0)

    def test_prediccion_anticipada(self):
        preds = [self._predecir(self.partidos[0], 1, 0, 30)]
        fila = calcular_fila(self.u, preds)
        self.assertEqual(fila.base, 5)
        self.assertEqual(fila.anticipada, 1)

    def test_ultimo_minuto_sin_bonus(self):
        preds = [self._predecir(self.partidos[0], 1, 0, 2)]
        self.assertEqual(calcular_fila(self.u, preds).anticipada, 0)


class FlujoTests(TestCase):
    def setUp(self):
        self.u = User.objects.create_user("luis", password="clave123")
        self.client.login(username="luis", password="clave123")

    def test_no_se_puede_predecir_a_ultimo_minuto(self):
        p = Partido.objects.create(local="A", visitante="B", fecha=timezone.now() + timedelta(minutes=5))
        self.client.post(f"/partidos/{p.id}/predecir/", {"goles_local": 1, "goles_visitante": 0})
        self.assertFalse(Prediccion.objects.exists())

    def test_prediccion_abierta(self):
        p = Partido.objects.create(local="A", visitante="B", fecha=timezone.now() + timedelta(days=2))
        self.client.post(f"/partidos/{p.id}/predecir/", {"goles_local": 2, "goles_visitante": 1})
        self.assertEqual(Prediccion.objects.get().goles_local, 2)

    def test_crear_sala_e_invitar(self):
        self.client.post("/salas/", {"nombre": "Amigos"})
        sala = Sala.objects.get()
        self.assertIn(self.u, sala.miembros.all())
        otro = User.objects.create_user("carla", password="clave123")
        self.client.login(username="carla", password="clave123")
        self.client.post(f"/salas/unirse/{sala.codigo}/")
        self.assertIn(otro, sala.miembros.all())

    def test_health(self):
        r = self.client.get("/health/")
        self.assertEqual(r.json()["estado"], "ok")
        self.assertIn("X-Contenedor", r)
