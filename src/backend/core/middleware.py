"""
Middleware for internal n8n ↔ Django communication.

Django validates the HTTP Host header against RFC 1034/1035 before checking
ALLOWED_HOSTS.  Docker container names such as 'cos40005_backend' contain
underscores, which are not valid per RFC 1034/1035, causing a DisallowedHost
exception even when ALLOWED_HOSTS = ['*'].

This middleware runs before SecurityMiddleware and CommonMiddleware and rewrites
any underscore-containing Host header to 'localhost' so the downstream Django
validators accept the request.
"""


class N8NInternalHostMiddleware:
    """Rewrite Docker-internal Host headers that contain underscores."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.META.get("HTTP_HOST", "")
        # Only rewrite if the hostname part (before colon) contains an underscore.
        # This catches 'cos40005_backend:8000' but not 'localhost:8000'.
        hostname = host.split(":")[0]
        if "_" in hostname:
            # Preserve the original for debugging but serve as localhost
            request.META["HTTP_HOST_ORIGINAL"] = host
            request.META["HTTP_HOST"] = "localhost"
        return self.get_response(request)
