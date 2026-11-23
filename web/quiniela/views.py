from collections import Counter

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import puntos
from .forms import RegistroForm, SalaForm, UnirseForm
from .middleware import CONTENEDOR
from .models import Partido, Prediccion, Sala


def inicio(request):
    proximos = Partido.objects.filter(goles_local__isnull=True, fecha__gte=timezone.now())[:4]
    recientes = Partido.objects.filter(goles_local__isnull=False).order_by("-fecha")[:4]
    tabla = puntos.tabla(User.objects.filter(is_superuser=False))[:5]
    return render(request, "quiniela/inicio.html", {"proximos": proximos, "recientes": recientes, "tabla": tabla})


def registro(request):
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        messages.success(request, "¡Cuenta creada! Ya puedes hacer tus predicciones.")
        return redirect("partidos")
    return render(request, "registration/registro.html", {"form": form})


def partidos(request):
    lista = list(Partido.objects.all())
    mias = {}
    if request.user.is_authenticated:
        mias = {p.partido_id: p for p in request.user.predicciones.all()}
        fila = puntos.calcular_fila(
            request.user, [p for p in mias.values() if p.partido.jugado]
        )
        detalle = {d.partido.id: d for d in fila.detalles}
    else:
        detalle = {}
    filas = [
        {"partido": p, "prediccion": mias.get(p.id), "detalle": detalle.get(p.id)}
        for p in lista
    ]
    return render(request, "quiniela/partidos.html", {"filas": filas})


@login_required
@require_POST
def predecir(request, partido_id):
    partido = get_object_or_404(Partido, pk=partido_id)
    if not partido.abierto:
        messages.error(request, f"Las predicciones para {partido} ya están cerradas.")
        return redirect("partidos")
    try:
        gl = int(request.POST["goles_local"])
        gv = int(request.POST["goles_visitante"])
        if not (0 <= gl <= 20 and 0 <= gv <= 20):
            raise ValueError
    except (KeyError, ValueError):
        messages.error(request, "Ingresa un marcador válido (0 a 20 goles).")
        return redirect("partidos")
    Prediccion.objects.update_or_create(
        usuario=request.user,
        partido=partido,
        defaults={"goles_local": gl, "goles_visitante": gv, "registrada": timezone.now()},
    )
    messages.success(request, f"Predicción guardada: {partido.local} {gl} - {gv} {partido.visitante}")
    return redirect("partidos")


def ranking(request):
    tabla = puntos.tabla(User.objects.filter(is_superuser=False))
    return render(request, "quiniela/ranking.html", {"tabla": tabla, "titulo": "Ranking general"})


@login_required
def mis_puntos(request):
    preds = request.user.predicciones.select_related("partido").filter(partido__goles_local__isnull=False)
    fila = puntos.calcular_fila(request.user, preds)
    return render(request, "quiniela/mis_puntos.html", {"fila": fila})


@login_required
def salas(request):
    form = SalaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        sala = form.save(commit=False)
        sala.creador = request.user
        sala.save()
        sala.miembros.add(request.user)
        messages.success(request, f"Sala «{sala.nombre}» creada. Comparte el enlace de invitación.")
        return redirect("sala", codigo=sala.codigo)
    return render(
        request,
        "quiniela/salas.html",
        {"salas": request.user.salas.all(), "form": form, "unirse": UnirseForm()},
    )


@login_required
def sala(request, codigo):
    sala = get_object_or_404(Sala, codigo=codigo)
    if not sala.miembros.filter(pk=request.user.pk).exists():
        return redirect("unirse", codigo=codigo)
    tabla = puntos.tabla(sala.miembros.all())
    enlace = request.build_absolute_uri(f"/salas/unirse/{sala.codigo}/")
    return render(request, "quiniela/sala.html", {"sala": sala, "tabla": tabla, "enlace": enlace})


@login_required
def unirse(request, codigo=None):
    if codigo is None:
        if request.method != "POST":
            return redirect("salas")
        form = UnirseForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data["codigo"]
        else:
            messages.error(request, form.errors["codigo"][0])
            return redirect("salas")
    sala = get_object_or_404(Sala, codigo=codigo)
    if request.method == "POST":
        sala.miembros.add(request.user)
        messages.success(request, f"Te uniste a «{sala.nombre}».")
        return redirect("sala", codigo=sala.codigo)
    return render(request, "quiniela/unirse.html", {"sala": sala})


@login_required
@require_POST
def salir(request, codigo):
    sala = get_object_or_404(Sala, codigo=codigo)
    if sala.creador_id != request.user.id:
        sala.miembros.remove(request.user)
        messages.success(request, f"Saliste de «{sala.nombre}».")
    return redirect("salas")


def estadisticas(request):
    jugados = Partido.objects.filter(goles_local__isnull=False)
    preds = list(Prediccion.objects.select_related("partido"))
    evaluadas = [p for p in preds if p.partido.jugado]
    aciertos = sum(
        1 for p in evaluadas
        if puntos.puntos_base(p.goles_local, p.goles_visitante, p.partido.goles_local, p.partido.goles_visitante) > 0
    )
    exactos = sum(
        1 for p in evaluadas
        if (p.goles_local, p.goles_visitante) == (p.partido.goles_local, p.partido.goles_visitante)
    )
    marcadores = Counter(f"{p.goles_local}-{p.goles_visitante}" for p in preds).most_common(5)

    tendencias = []
    for partido in Partido.objects.filter(goles_local__isnull=True):
        votos = [puntos._signo(p.goles_local, p.goles_visitante) for p in preds if p.partido_id == partido.id]
        n = len(votos) or 1
        tendencias.append({
            "partido": partido,
            "total": len(votos),
            "local": round(100 * votos.count(1) / n),
            "empate": round(100 * votos.count(0) / n),
            "visitante": round(100 * votos.count(-1) / n),
        })
    return render(request, "quiniela/estadisticas.html", {
        "total_preds": len(preds),
        "jugados": jugados.count(),
        "efectividad": round(100 * aciertos / len(evaluadas)) if evaluadas else 0,
        "exactos": exactos,
        "marcadores": marcadores,
        "tendencias": tendencias,
    })


def health(request):
    return JsonResponse({"estado": "ok", "contenedor": CONTENEDOR, "hora": timezone.now().isoformat()})
