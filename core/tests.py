from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


class HealthCheckTests(TestCase):
    def test_health_check_healthy(self) -> None:
        """Garante que o health check retorna 200 e status healthy quando o banco está saudável."""
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["checks"]["database"], "up")

    @patch("core.views.connection.cursor")
    def test_health_check_unhealthy(self, mock_cursor) -> None:
        """Garante que o health check retorna 503 e status unhealthy quando o banco falha."""
        mock_cursor.side_effect = Exception("Banco de dados indisponível")

        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertIn("down: Banco de dados indisponível", data["checks"]["database"])
