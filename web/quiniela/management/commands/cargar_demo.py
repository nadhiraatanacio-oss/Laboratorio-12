import os
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from quiniela.models import Partido, Prediccion, Sala

EQUIPOS = [
    ("Grupo A", "México", "Sudáfrica"), ("Grupo A", "Corea del Sur", "Dinamarca"),
    ("Grupo B", "Canadá", "Suiza"), ("Grupo B", "Qatar", "Italia"),
    ("Grupo C", "Brasil", "Marruecos"), ("Grupo C", "Escocia", "Haití"),
    ("Grupo D", "Estados Unidos", "Paraguay"), ("Grupo D", "Australia", "Turquía"),
    ("Grupo E", "Alemania", "Curazao"), ("Grupo E", "Costa de Marfil", "Ecuador"),
    ("Grupo F", "Países Bajos", "Japón"), ("Grupo F", "Túnez", "Suecia"),
    ("Grupo G", "Bélgica", "Egipto"), ("Grupo G", "Irán", "Nueva Zelanda"),
    ("Grupo H", "España", "Cabo Verde"), ("Grupo H", "Arabia Saudita", "Uruguay"),
]
PARTICIPANTES = ["ana", "luis", "carla", "diego", "sofia", "mateo"]


class Command(BaseCommand):
    help = "Carga partidos, participantes, predicciones y una sala de prueba."

    def handle(self, *args, **opts):
        if Partido.objects.exists():
            self.stdout.write("Los datos de prueba ya estaban cargados.")
            return
        rnd = random.Random(2026)
        ahora = timezone.now().replace(minute=0, second=0, microsecond=0)

        admin_pass = os.environ.get("ADMIN_PASSWORD", "admin12345")
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "", admin_pass)

        usuarios = []
        for nombre in PARTICIPANTES:
            u, _ = User.objects.get_or_create(username=nombre)
            u.set_password("mundial2026")
            u.save()
            usuarios.append(u)

        partidos = []
        for i, (fase, local, visit) in enumerate(EQUIPOS):
            # 10 partidos ya jugados (días anteriores) y 6 por jugar
            fecha = ahora + timedelta(days=i - 10, hours=rnd.choice([0, 3, 6]))
            p = Partido(fase=fase, local=local, visitante=visit, fecha=fecha)
            if i < 10:
                p.goles_local, p.goles_visitante = rnd.randint(0, 3), rnd.randint(0, 3)
            p.save()
            partidos.append(p)

        for u in usuarios:
            for p in partidos:
                if rnd.random() < 0.15:
                    continue  # algunos participantes no predicen todos los partidos
                if p.jugado and rnd.random() < 0.35:
                    gl, gv = p.goles_local, p.goles_visitante  # simula un acierto exacto
                elif p.jugado and rnd.random() < 0.4:
                    gl, gv = p.goles_local + 1, p.goles_visitante + 1  # misma diferencia
                else:
                    gl, gv = rnd.randint(0, 3), rnd.randint(0, 3)
                antes = timedelta(hours=rnd.choice([2, 12, 30, 48, 72]))
                Prediccion.objects.create(usuario=u, partido=p, goles_local=gl, goles_visitante=gv, registrada=p.fecha - antes)

        sala = Sala.objects.create(nombre="Tecsup 5C24", creador=usuarios[0])
        sala.miembros.add(*usuarios[:4])
        sala2 = Sala.objects.create(nombre="Familia", creador=usuarios[4])
        sala2.miembros.add(usuarios[4], usuarios[5], usuarios[0])

        self.stdout.write(self.style.SUCCESS(
            f"Datos de prueba: {len(partidos)} partidos, {len(usuarios)} participantes, "
            f"{Prediccion.objects.count()} predicciones, 2 salas. Usuarios: {', '.join(PARTICIPANTES)} (clave mundial2026)."
        ))
