from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("registro/", views.registro, name="registro"),
    path("partidos/", views.partidos, name="partidos"),
    path("partidos/<int:partido_id>/predecir/", views.predecir, name="predecir"),
    path("ranking/", views.ranking, name="ranking"),
    path("mis-puntos/", views.mis_puntos, name="mis_puntos"),
    path("salas/", views.salas, name="salas"),
    path("salas/unirse/", views.unirse, name="unirse_codigo"),
    path("salas/unirse/<str:codigo>/", views.unirse, name="unirse"),
    path("salas/<str:codigo>/", views.sala, name="sala"),
    path("salas/<str:codigo>/salir/", views.salir, name="salir"),
    path("estadisticas/", views.estadisticas, name="estadisticas"),
    path("health/", views.health, name="health"),
]
