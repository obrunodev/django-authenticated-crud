from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import Http404
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.decorators import owner_required
from accounts.models import OwnedQuerySet

User = get_user_model()


class AuthTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
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

    @override_settings(LOGIN_RATELIMIT_LIMIT=3)
    def test_login_rate_limiting_blocks_after_max_attempts(self) -> None:
        """Garante que requisições consecutivas POST acima do limite são bloqueadas."""
        for _ in range(3):
            response = self.client.post(
                reverse("login"),
                {"username": self.username, "password": "wrongpassword"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "accounts/login.html")

        response = self.client.post(
            reverse("login"),
            {"username": self.username, "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 429)
        self.assertTemplateUsed(response, "accounts/login.html")
        self.assertContains(
            response,
            "Muitas tentativas de login. Por favor, tente novamente mais tarde.",
            status_code=429,
        )

    @override_settings(LOGIN_RATELIMIT_LIMIT=3)
    def test_login_rate_limiting_allows_get_requests(self) -> None:
        """Garante que requisições GET ainda são permitidas mesmo sob bloqueio de rate limit."""
        for _ in range(4):
            self.client.post(
                reverse("login"),
                {"username": self.username, "password": "wrongpassword"},
            )

        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    @override_settings(LOGIN_RATELIMIT_LIMIT=3)
    def test_login_rate_limiting_clears_on_success(self) -> None:
        """Garante que o contador de rate limit é reiniciado após um login bem-sucedido."""
        for _ in range(2):
            response = self.client.post(
                reverse("login"),
                {"username": self.username, "password": "wrongpassword"},
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("login"),
            {"username": self.username, "password": self.password},
        )
        self.assertEqual(response.status_code, 302)

        self.client.logout()

        response = self.client.post(
            reverse("login"),
            {"username": self.username, "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)

    @override_settings(LOGIN_RATELIMIT_LIMIT=3)
    def test_login_rate_limiting_with_x_forwarded_for(self) -> None:
        """Garante que o rate limit funciona usando o cabeçalho HTTP_X_FORWARDED_FOR."""
        for _ in range(3):
            response = self.client.post(
                reverse("login"),
                {"username": self.username, "password": "wrongpassword"},
                HTTP_X_FORWARDED_FOR="192.168.1.1, 10.0.0.1",
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("login"),
            {"username": self.username, "password": "wrongpassword"},
            HTTP_X_FORWARDED_FOR="192.168.1.1, 10.0.0.1",
        )
        self.assertEqual(response.status_code, 429)

    def test_authenticated_user_cannot_access_login(self) -> None:
        """Garante que usuário já logado é redirecionado ao tentar acessar tela de login."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse("login"))
        self.assertRedirects(response, reverse("dashboard"))

    def test_authenticated_user_cannot_access_register(self) -> None:
        """Garante que usuário já logado é redirecionado ao tentar acessar tela de registro."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse("register"))
        self.assertRedirects(response, reverse("dashboard"))

    def test_anonymous_user_can_get_register(self) -> None:
        """Garante que usuário anônimo consegue abrir o formulário de registro."""
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")


class RowLevelSecurityTests(TestCase):
    def setUp(self) -> None:
        self.username = "testuser"
        self.email = "testuser@example.com"
        self.password = "SecurePassword123"
        self.user = User.objects.create_user(
            username=self.username, email=self.email, password=self.password
        )

    def test_owned_queryset_unauthenticated_user(self) -> None:
        """Garante que OwnedQuerySet.for_user retorna nenhum resultado para não autenticados."""
        user = MagicMock()
        user.is_authenticated = False

        qs = OwnedQuerySet()
        qs.none = MagicMock(return_value="none_result")
        qs.filter = MagicMock()

        result = qs.for_user(user)
        self.assertEqual(result, "none_result")
        qs.none.assert_called_once()
        qs.filter.assert_not_called()

    def test_owned_queryset_authenticated_user(self) -> None:
        """Garante que OwnedQuerySet.for_user filtra as instâncias pelo usuário logado."""
        user = MagicMock()
        user.is_authenticated = True

        qs = OwnedQuerySet()
        qs.none = MagicMock()
        qs.filter = MagicMock(return_value="filtered_result")

        result = qs.for_user(user)
        self.assertEqual(result, "filtered_result")
        qs.filter.assert_called_once_with(user=user)
        qs.none.assert_not_called()

    def test_owner_required_decorator_success(self) -> None:
        """Garante que o decorator owner_required permite acesso e injeta o objeto correto."""
        mock_model = MagicMock()
        mock_obj = MagicMock()
        mock_model.objects.get.return_value = mock_obj

        @owner_required(mock_model)
        def dummy_view(request, obj):
            return ("success", obj)

        request = MagicMock()
        request.user = self.user

        status, obj = dummy_view(request, pk=42)
        self.assertEqual(status, "success")
        self.assertEqual(obj, mock_obj)
        mock_model.objects.get.assert_called_once_with(pk=42, user=self.user)

    def test_owner_required_decorator_not_found(self) -> None:
        """Garante que o decorator owner_required levanta Http404 se o objeto não pertencer ao usuário."""
        mock_model = MagicMock()
        from django.core.exceptions import ObjectDoesNotExist

        mock_model.DoesNotExist = ObjectDoesNotExist
        mock_model.objects.get.side_effect = ObjectDoesNotExist()

        @owner_required(mock_model)
        def dummy_view(request, obj):
            return "success"  # pragma: no cover

        request = MagicMock()
        request.user = self.user

        with self.assertRaises(Http404):
            dummy_view(request, pk=42)

    def test_owner_required_decorator_positional_arg(self) -> None:
        """Garante que o decorator owner_required funciona quando o ID é passado como argumento posicional."""
        mock_model = MagicMock()
        mock_obj = MagicMock()
        mock_model.objects.get.return_value = mock_obj

        @owner_required(mock_model)
        def dummy_view(request, obj):
            return ("success", obj)

        request = MagicMock()
        request.user = self.user

        # Passa 42 como argumento posicional (args) em vez de kwarg (pk=42)
        status, obj = dummy_view(request, 42)
        self.assertEqual(status, "success")
        self.assertEqual(obj, mock_obj)
        mock_model.objects.get.assert_called_once_with(pk=42, user=self.user)

    def test_owner_required_decorator_missing_id(self) -> None:
        """Garante que o decorator owner_required levanta Http404 se nenhum ID for fornecido nos argumentos."""
        mock_model = MagicMock()

        @owner_required(mock_model)
        def dummy_view(request, obj):
            return "success"  # pragma: no cover

        request = MagicMock()
        request.user = self.user

        with self.assertRaises(Http404) as context:
            dummy_view(request)
        self.assertEqual(str(context.exception), "ID do objeto não fornecido.")
