import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

CIERRE_PREDICCIONES = timedelta(minutes=10)


def generar_codigo():
    return secrets.token_urlsafe(6)[:8].upper()


class Partido(models.Model):
    fase = models.CharField(max_length=40, default="Fase de grupos")
    local = models.CharField(max_length=50)
    visitante = models.CharField(max_length=50)
    fecha = models.DateTimeField()
    goles_local = models.PositiveSmallIntegerField(null=True, blank=True)
    goles_visitante = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["fecha"]

    def __str__(self):
        return f"{self.local} vs {self.visitante}"

    @property
    def jugado(self):
        return self.goles_local is not None and self.goles_visitante is not None

    @property
    def abierto(self):
        """Se aceptan predicciones hasta 10 minutos antes del inicio."""
        return not self.jugado and timezone.now() < self.fecha - CIERRE_PREDICCIONES


class Sala(models.Model):
    nombre = models.CharField(max_length=60)
    codigo = models.CharField(max_length=8, unique=True, default=generar_codigo, editable=False)
    creador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="salas_creadas")
    miembros = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="salas", blank=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creada"]

    def __str__(self):
        return self.nombre


class Prediccion(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="predicciones")
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name="predicciones")
    goles_local = models.PositiveSmallIntegerField()
    goles_visitante = models.PositiveSmallIntegerField()
    registrada = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("usuario", "partido")
        verbose_name_plural = "predicciones"

    def __str__(self):
        return f"{self.usuario} · {self.partido}: {self.goles_local}-{self.goles_visitante}"
