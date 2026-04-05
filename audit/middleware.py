import threading

_thread_local = threading.local()


def get_current_request():
    return getattr(_thread_local, 'request', None)


class AuditMiddleware:
    """Stores the current request in thread-local for audit logging."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_local.request = request
        response = self.get_response(request)
        return response
