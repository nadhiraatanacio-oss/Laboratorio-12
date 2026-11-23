import socket

CONTENEDOR = socket.gethostname()


class ContenedorMiddleware:
    """Agrega en cada respuesta qué réplica la atendió (evidencia del balanceo)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Contenedor"] = CONTENEDOR
        return response


def contenedor(request):
    return {"contenedor": CONTENEDOR}
