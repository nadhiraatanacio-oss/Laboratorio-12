from django.contrib import admin

from .models import Partido, Prediccion, Sala


@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):
    list_display = ("local", "visitante", "fecha", "fase", "goles_local", "goles_visitante")
    list_editable = ("goles_local", "goles_visitante")
    list_filter = ("fase",)


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "creador", "creada")
    filter_horizontal = ("miembros",)


@admin.register(Prediccion)
class PrediccionAdmin(admin.ModelAdmin):
    list_display = ("usuario", "partido", "goles_local", "goles_visitante", "registrada")
    list_filter = ("usuario",)
