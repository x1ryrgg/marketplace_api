import logging

logger = logging.getLogger(__name__)


class LoggerMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = request.user.username if hasattr(request, 'user') else 'AnonymousUser'
        logger.info(f"Request: {request.method} {request.path} | User: {user}")
        return response