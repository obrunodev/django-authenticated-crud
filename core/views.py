import logging

from django.db import connection
from django.http import HttpRequest, JsonResponse

logger = logging.getLogger("critical_actions")


def health_check(request: HttpRequest) -> JsonResponse:
    """Valida a integridade do sistema, checando a conectividade do banco de dados."""
    status = "healthy"
    checks = {"database": "up"}
    status_code = 200

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
    except Exception as e:
        status = "unhealthy"
        checks["database"] = f"down: {e!s}"
        status_code = 503
        logger.critical(
            "Health check failed",
            extra={
                "action": "health_check_failure",
                "error": str(e),
                "checks": checks,
            },
        )

    return JsonResponse({"status": status, "checks": checks}, status=status_code)
