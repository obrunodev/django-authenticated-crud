from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AuthTests(TestCase):
    def setUp(self) -> None:
        self.username = "testuser"
        self.email = "testuser@example.com"
        self.password = "SecurePassword123"
        self.user = User.objects.create_user(
            username=self.username, email=self.email, password=self.password
        )

    def test_dashboard_requires_login(self) -> None:
        """Garante que o dashboard redireciona usuários não autenticados."""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_dashboard_accessible_when_logged_in(self) -> None:
        """Garante que o dashboard carrega se o usuário estiver autenticado."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/dashboard.html")

    def test_login_post_valid_credentials(self) -> None:
        """Garante que credenciais válidas autenticam e redirecionam para o dashboard."""
        response = self.client.post(
            reverse("login"), {"username": self.username, "password": self.password}
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("dashboard"))

    def test_login_post_invalid_credentials(self) -> None:
        """Garante que credenciais inválidas falham na validação do formulário."""
        response = self.client.post(
            reverse("login"), {"username": self.username, "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")
        self.assertFalse(response.context["form"].is_valid())

    def test_user_registration(self) -> None:
        """Garante que o registro cria um novo usuário no banco e faz login."""
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "AnotherPassword123!",
                "password2": "AnotherPassword123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_logout(self) -> None:
        """Garante que requisição POST de logout tradicional limpa a sessão e redireciona."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login"))

    def test_logout_htmx(self) -> None:
        """Garante que requisição POST de logout via HTMX retorna cabeçalho HX-Redirect."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse("logout"), HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["HX-Redirect"], reverse("login"))
