import logging

logger = logging.getLogger(__name__)


class LoggerMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info('Request: %s %s | %s', request.method, request.path, request.user)
        response = self.get_response(request)
        return response