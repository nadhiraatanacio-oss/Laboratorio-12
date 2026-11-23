# Quiniela Mundial

Aplicación web para predecir los resultados del Mundial y acumular puntos.
Django + PostgreSQL, contenerizada con Docker, con 3 réplicas detrás de Nginx.

## Ejecutar

```bash
docker compose up -d --build
```

- Aplicación: http://localhost:8080
- Administración: http://localhost:8080/admin (usuario `admin`, clave `admin12345`)
- Participantes de prueba: ana, luis, carla, diego, sofia, mateo (clave `mundial2026`)

## Escalar

```bash
docker compose up -d --scale web=5
docker compose restart nginx
```

## Pruebas

```bash
docker compose exec web python manage.py test quiniela
pip install locust
locust -f pruebas/locustfile.py --host http://localhost:8080 --headless -u 300 -r 30 -t 60s --html pruebas/reporte.html
```
