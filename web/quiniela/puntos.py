"""Reglas de puntuación de la quiniela.

1. Resultado exacto ........................ 5 puntos
2. Ganador correcto (o empate) ............. 3 puntos
3. Diferencia de goles correcta ............ 2 puntos (se suma al ganador)
4. Bonus por racha ......................... +2 por cada 3 aciertos seguidos
5. Predicción anticipada (> 24 h) .......... +1 si la predicción acertó

Un "acierto" es una predicción que, como mínimo, acertó el ganador.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import timedelta

PUNTOS_EXACTO = 5
PUNTOS_GANADOR = 3
PUNTOS_DIFERENCIA = 2
BONUS_RACHA = 2
PARTIDOS_POR_RACHA = 3
PUNTO_ANTICIPADA = 1
ANTICIPACION = timedelta(hours=24)


def _signo(local, visitante):
    return (local > visitante) - (local < visitante)


def puntos_base(pred_local, pred_visitante, real_local, real_visitante):
    if (pred_local, pred_visitante) == (real_local, real_visitante):
        return PUNTOS_EXACTO
    puntos = 0
    if _signo(pred_local, pred_visitante) == _signo(real_local, real_visitante):
        puntos += PUNTOS_GANADOR
        if pred_local - pred_visitante == real_local - real_visitante:
            puntos += PUNTOS_DIFERENCIA
    return puntos


def es_anticipada(prediccion, partido):
    return partido.fecha - prediccion.registrada > ANTICIPACION


@dataclass
class Detalle:
    partido: object
    prediccion: object
    base: int
    racha: int
    anticipada: int

    @property
    def total(self):
        return self.base + self.racha + self.anticipada


@dataclass
class Fila:
    usuario: object
    base: int = 0
    racha: int = 0
    anticipada: int = 0
    aciertos: int = 0
    exactos: int = 0
    jugados: int = 0
    detalles: list = field(default_factory=list)

    @property
    def total(self):
        return self.base + self.racha + self.anticipada

    @property
    def efectividad(self):
        return round(100 * self.aciertos / self.jugados) if self.jugados else 0


def calcular_fila(usuario, predicciones):
    """predicciones: predicciones del usuario sobre partidos ya jugados."""
    fila = Fila(usuario=usuario)
    seguidos = 0
    for pred in sorted(predicciones, key=lambda p: p.partido.fecha):
        partido = pred.partido
        base = puntos_base(pred.goles_local, pred.goles_visitante, partido.goles_local, partido.goles_visitante)
        racha = anticipada = 0
        if base > 0:
            seguidos += 1
            fila.aciertos += 1
            if seguidos % PARTIDOS_POR_RACHA == 0:
                racha = BONUS_RACHA
            if es_anticipada(pred, partido):
                anticipada = PUNTO_ANTICIPADA
        else:
            seguidos = 0
        if base == PUNTOS_EXACTO:
            fila.exactos += 1
        fila.jugados += 1
        fila.base += base
        fila.racha += racha
        fila.anticipada += anticipada
        fila.detalles.append(Detalle(partido, pred, base, racha, anticipada))
    return fila


def tabla(usuarios):
    from .models import Prediccion

    usuarios = list(usuarios)
    por_usuario = defaultdict(list)
    for pred in (
        Prediccion.objects.filter(usuario__in=usuarios, partido__goles_local__isnull=False, partido__goles_visitante__isnull=False)
        .select_related("partido")
    ):
        por_usuario[pred.usuario_id].append(pred)
    filas = [calcular_fila(u, por_usuario[u.id]) for u in usuarios]
    filas.sort(key=lambda f: (-f.total, -f.exactos, f.usuario.username))
    return filas
