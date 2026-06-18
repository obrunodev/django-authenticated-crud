from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from tasks.models import Task
from tasks.services import complete_task, reopen_task

User = get_user_model()


class TaskModelTests(TestCase):
    def setUp(self) -> None:
        self.user_a = User.objects.create_user(
            username="usera", email="usera@example.com", password="Password123"
        )
        self.user_b = User.objects.create_user(
            username="userb", email="userb@example.com", password="Password123"
        )

    def test_task_creation_and_defaults(self) -> None:
        """Garante que a tarefa é criada corretamente com os valores padrão."""
        task = Task.objects.create(
            user=self.user_a,
            title="Minha primeira tarefa",
            description="Descrição de teste",
        )
        self.assertEqual(task.title, "Minha primeira tarefa")
        self.assertEqual(task.description, "Descrição de teste")
        self.assertFalse(task.is_completed)
        self.assertEqual(task.xp_reward, 10)
        self.assertIsNotNone(task.created_at)
        self.assertIsNone(task.completed_at)
        self.assertEqual(str(task), "Minha primeira tarefa")

    def test_row_level_security_filtering(self) -> None:
        """Garante que OwnedModel.objects.for_user filtra tarefas por proprietário."""
        task_a = Task.objects.create(
            user=self.user_a,
            title="Tarefa do Usuário A",
        )
        task_b = Task.objects.create(
            user=self.user_b,
            title="Tarefa do Usuário B",
        )

        # Queryset do Usuário A
        qs_a = Task.objects.for_user(self.user_a)
        self.assertIn(task_a, qs_a)
        self.assertNotIn(task_b, qs_a)

        # Queryset do Usuário B
        qs_b = Task.objects.for_user(self.user_b)
        self.assertIn(task_b, qs_b)
        self.assertNotIn(task_a, qs_b)

    def test_task_cannot_have_empty_whitespace_title(self) -> None:
        """Garante que a criação de uma tarefa com título apenas de espaços falha na validação."""
        task = Task(
            user=self.user_a,
            title="   ",
            description="Teste espaço",
        )
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_task_cannot_have_past_due_date_on_creation(self) -> None:
        """Garante que a criação de uma tarefa com prazo no passado falha na validação."""
        yesterday = timezone.localdate() - timezone.timedelta(days=1)
        task = Task(
            user=self.user_a,
            title="Tarefa Atrasada",
            due_date=yesterday,
        )
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_task_can_have_future_due_date_on_creation(self) -> None:
        """Garante que a criação de uma tarefa com prazo no futuro passa na validação."""
        tomorrow = timezone.localdate() + timezone.timedelta(days=1)
        task = Task(
            user=self.user_a,
            title="Tarefa Futura",
            due_date=tomorrow,
        )
        # Não deve lançar erro
        task.full_clean()
        task.save()
        self.assertEqual(task.due_date, tomorrow)

    def test_task_allow_editing_without_changing_expired_due_date(self) -> None:
        """Garante que uma tarefa já salva não falha ao ser editada sem alterar o prazo expirado."""
        # Criamos com data futura
        tomorrow = timezone.localdate() + timezone.timedelta(days=1)
        task = Task.objects.create(
            user=self.user_a,
            title="Tarefa Futura",
            due_date=tomorrow,
        )

        # Agora simulamos que o tempo passou e a data ficou no passado no banco
        yesterday = timezone.localdate() - timezone.timedelta(days=1)
        Task.objects.filter(pk=task.pk).update(due_date=yesterday)

        task.refresh_from_db()
        # Ao salvar editando apenas o título (sem mexer na data), não deve explodir erro
        task.title = "Título Alterado"
        task.save()

    def test_task_edit_past_due_date_fails_validation(self) -> None:
        """Garante que alterar o prazo de uma tarefa existente para o passado falha na validação."""
        tomorrow = timezone.localdate() + timezone.timedelta(days=1)
        task = Task.objects.create(
            user=self.user_a,
            title="Tarefa",
            due_date=tomorrow,
        )

        # Tenta alterar a data limite para o passado
        yesterday = timezone.localdate() - timezone.timedelta(days=1)
        task.due_date = yesterday
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_task_due_status(self) -> None:
        """Garante que a propriedade due_status funciona corretamente."""
        task = Task(user=self.user_a, title="Sem Prazo")
        self.assertEqual(task.due_status, "none")

        today = timezone.localdate()
        task.due_date = today - timezone.timedelta(days=1)
        self.assertEqual(task.due_status, "overdue")

        task.due_date = today
        self.assertEqual(task.due_status, "today")

        task.due_date = today + timezone.timedelta(days=1)
        self.assertEqual(task.due_status, "future")


class TaskServiceTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="Password123"
        )

    def test_complete_task_sets_completed_status(self) -> None:
        """Garante que a conclusão de uma tarefa define o status e completed_at."""
        task = Task.objects.create(
            user=self.user,
            title="Tarefa de teste",
        )
        self.assertFalse(task.is_completed)
        self.assertIsNone(task.completed_at)

        complete_task(task)

        task.refresh_from_db()
        self.assertTrue(task.is_completed)
        self.assertIsNotNone(task.completed_at)
        self.assertTrue((timezone.now() - task.completed_at).total_seconds() < 10)

    def test_complete_task_awards_xp(self) -> None:
        """Garante que a conclusão de uma tarefa recompensa o usuário com XP."""
        task = Task.objects.create(
            user=self.user,
            title="Tarefa de teste",
            xp_reward=25,
        )
        self.assertEqual(self.user.experience_points, 0)
        self.assertEqual(self.user.level, 1)

        complete_task(task)

        self.user.refresh_from_db()
        self.assertEqual(self.user.experience_points, 25)
        self.assertEqual(self.user.level, 1)

    def test_complete_task_triggers_level_up(self) -> None:
        """Garante que o usuário sobe de nível quando acumula 100 XP ou mais."""
        task_1 = Task.objects.create(
            user=self.user,
            title="Tarefa 1",
            xp_reward=60,
        )
        task_2 = Task.objects.create(
            user=self.user,
            title="Tarefa 2",
            xp_reward=50,
        )

        complete_task(task_1)
        self.user.refresh_from_db()
        self.assertEqual(self.user.experience_points, 60)
        self.assertEqual(self.user.level, 1)

        complete_task(task_2)
        self.user.refresh_from_db()
        self.assertEqual(self.user.experience_points, 10)
        self.assertEqual(self.user.level, 2)

    def test_complete_task_triggers_multi_level_up(self) -> None:
        """Garante que o usuário pode subir múltiplos níveis de uma só vez."""
        task = Task.objects.create(
            user=self.user,
            title="Super Tarefa",
            xp_reward=250,
        )
        self.assertEqual(self.user.level, 1)
        self.assertEqual(self.user.experience_points, 0)

        complete_task(task)

        self.user.refresh_from_db()
        self.assertEqual(self.user.level, 3)
        self.assertEqual(self.user.experience_points, 50)

    def test_already_completed_task_does_not_award_xp_again(self) -> None:
        """Garante que concluir uma tarefa que já está concluída não adiciona XP novamente."""
        task = Task.objects.create(
            user=self.user,
            title="Tarefa Reutilizada",
            xp_reward=20,
        )

        complete_task(task)
        self.user.refresh_from_db()
        self.assertEqual(self.user.experience_points, 20)

        complete_task(task)
        self.user.refresh_from_db()
        self.assertEqual(self.user.experience_points, 20)

    def test_reopen_task_deducts_xp_and_levels_down(self) -> None:
        """Garante que a reabertura de uma tarefa deduz XP e diminui nível se necessário."""
        # 1. Caso Simples: perde XP mas continua no mesmo nível
        self.user.experience_points = 50
        self.user.level = 1
        self.user.save()

        task = Task.objects.create(
            user=self.user,
            title="Tarefa XP",
            xp_reward=30,
            is_completed=True,
            completed_at=timezone.now(),
        )

        reopen_task(task)
        self.user.refresh_from_db()
        self.assertEqual(self.user.experience_points, 20)
        self.assertEqual(self.user.level, 1)

        # 2. Caso com redução de nível: volta de nível 2 para nível 1
        self.user.experience_points = 10
        self.user.level = 2
        self.user.save()

        task.is_completed = True
        task.completed_at = timezone.now()
        task.xp_reward = 20
        task.save()

        reopen_task(task)
        self.user.refresh_from_db()
        self.assertEqual(self.user.level, 1)
        self.assertEqual(self.user.experience_points, 90)

        # 3. Caso com limite: nível não pode ficar abaixo de 1
        self.user.experience_points = 10
        self.user.level = 1
        self.user.save()

        task.is_completed = True
        task.completed_at = timezone.now()
        task.xp_reward = 30
        task.save()

        reopen_task(task)
        self.user.refresh_from_db()
        self.assertEqual(self.user.level, 1)
        self.assertEqual(self.user.experience_points, 0)  # Capped at 0

    def test_reopen_active_task_does_nothing(self) -> None:
        """Garante que tentar reabrir uma tarefa que não está concluída não faz nada."""
        task = Task.objects.create(
            user=self.user,
            title="Tarefa Ativa",
            is_completed=False,
        )
        self.assertFalse(task.is_completed)
        reopen_task(task)
        self.assertFalse(task.is_completed)


class TaskViewTests(TestCase):
    def setUp(self) -> None:
        self.username = "testuser"
        self.password = "Password123"
        self.user = User.objects.create_user(
            username=self.username, email="test@example.com", password=self.password
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password=self.password
        )

        # Tarefa padrão para o usuário
        self.task = Task.objects.create(
            user=self.user,
            title="Tarefa Padrão",
            description="Descrição",
            xp_reward=15,
        )

    def test_views_require_authentication(self) -> None:
        """Garante que as rotas de tarefas exigem autenticação do usuário."""
        urls = [
            reverse("tasks:list"),
            reverse("tasks:create"),
            reverse("tasks:toggle", kwargs={"pk": self.task.pk}),
            reverse("tasks:edit", kwargs={"pk": self.task.pk}),
            reverse("tasks:detail", kwargs={"pk": self.task.pk}),
            reverse("tasks:delete", kwargs={"pk": self.task.pk}),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, f"Falhou em: {url}")

            # Para métodos POST, tenta requisição anônima também
            if url not in [
                reverse("tasks:list"),
                reverse("tasks:detail", kwargs={"pk": self.task.pk}),
                reverse("tasks:edit", kwargs={"pk": self.task.pk}),
            ]:
                response = self.client.post(url)
                self.assertEqual(response.status_code, 302, f"Falhou POST em: {url}")

    def test_list_view_htmx_vs_standard(self) -> None:
        """Garante que a visualização de lista retorna o template correto com e sem HTMX."""
        self.client.login(username=self.username, password=self.password)

        # Requisição padrão
        response = self.client.get(reverse("tasks:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/task_list_page.html")

        # Requisição HTMX
        response = self.client.get(reverse("tasks:list"), HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/partials/task_list.html")
        self.assertTemplateNotUsed(response, "tasks/task_list_page.html")

    def test_list_view_search_filtering(self) -> None:
        """Garante que a busca textual filtra os objetivos de forma correta."""
        self.client.login(username=self.username, password=self.password)

        # Cria tarefa específica
        match_task = Task.objects.create(user=self.user, title="Comprar Abacaxi")

        response = self.client.get(
            reverse("tasks:list"), {"q": "Abacaxi"}, HTTP_HX_REQUEST="true"
        )
        self.assertIn(match_task, response.context["page_obj"])
        self.assertNotIn(self.task, response.context["page_obj"])

    def test_list_view_status_filtering(self) -> None:
        """Garante que o filtro de status (pendente vs concluído) retorna os itens corretos."""
        self.client.login(username=self.username, password=self.password)

        completed_task = Task.objects.create(
            user=self.user, title="Concluída", is_completed=True
        )

        # Filtro de concluídos
        response = self.client.get(
            reverse("tasks:list"), {"status": "completed"}, HTTP_HX_REQUEST="true"
        )
        self.assertIn(completed_task, response.context["page_obj"])
        self.assertNotIn(self.task, response.context["page_obj"])

        # Filtro de pendentes
        response = self.client.get(
            reverse("tasks:list"), {"status": "pending"}, HTTP_HX_REQUEST="true"
        )
        self.assertIn(self.task, response.context["page_obj"])
        self.assertNotIn(completed_task, response.context["page_obj"])

    def test_list_view_pagination(self) -> None:
        """Garante que a paginação exibe a quantidade configurada e preserva query params."""
        self.client.login(username=self.username, password=self.password)

        # Cria mais 10 tarefas (total 11)
        for i in range(10):
            Task.objects.create(user=self.user, title=f"Tarefa {i}")

        # Página 1 deve ter 5 tarefas (paginação definida para 5 por página)
        response = self.client.get(reverse("tasks:list"), HTTP_HX_REQUEST="true")
        self.assertEqual(len(response.context["page_obj"]), 5)

        # Página 3 deve ter o restante (1 item)
        response = self.client.get(
            reverse("tasks:list"), {"page": 3}, HTTP_HX_REQUEST="true"
        )
        self.assertEqual(len(response.context["page_obj"]), 1)

    def test_create_view_success(self) -> None:
        """Garante que a criação cria a tarefa no banco e envia o trigger htmx."""
        self.client.login(username=self.username, password=self.password)

        payload = {
            "title": "Aprender Django",
            "description": "Muito divertido",
            "xp_reward": 30,
        }
        response = self.client.post(
            reverse("tasks:create"), payload, HTTP_HX_REQUEST="true"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Task.objects.filter(title="Aprender Django", user=self.user).exists()
        )
        self.assertEqual(response["HX-Trigger"], "task-updated")

    def test_toggle_view_not_owned_returns_404(self) -> None:
        """Garante que tentar alternar o status de uma tarefa que não pertence ao usuário retorna 404 (RLS)."""
        self.client.login(username=self.username, password=self.password)

        other_task = Task.objects.create(user=self.other_user, title="De outro user")

        response = self.client.post(
            reverse("tasks:toggle", kwargs={"pk": other_task.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_edit_view_get_not_owned_returns_404(self) -> None:
        """Garante que tentar obter o formulário de edição de uma tarefa que não pertence ao usuário retorna 404."""
        self.client.login(username=self.username, password=self.password)
        other_task = Task.objects.create(user=self.other_user, title="Tarefa Alheia")
        response = self.client.get(reverse("tasks:edit", kwargs={"pk": other_task.pk}))
        self.assertEqual(response.status_code, 404)

    def test_edit_view_post_not_owned_returns_404(self) -> None:
        """Garante que tentar atualizar uma tarefa que não pertence ao usuário retorna 404."""
        self.client.login(username=self.username, password=self.password)
        other_task = Task.objects.create(user=self.other_user, title="Tarefa Alheia")
        payload = {
            "title": "Hackeada",
            "xp_reward": 50,
            "description": "Tentativa de injeção",
        }
        response = self.client.post(
            reverse("tasks:edit", kwargs={"pk": other_task.pk}),
            payload,
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 404)

    def test_detail_view_not_owned_returns_404(self) -> None:
        """Garante que tentar visualizar os detalhes de uma tarefa que não pertence ao usuário retorna 404."""
        self.client.login(username=self.username, password=self.password)
        other_task = Task.objects.create(user=self.other_user, title="Tarefa Alheia")
        response = self.client.get(
            reverse("tasks:detail", kwargs={"pk": other_task.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_view_not_owned_returns_404(self) -> None:
        """Garante que tentar deletar uma tarefa que não pertence ao usuário retorna 404."""
        self.client.login(username=self.username, password=self.password)
        other_task = Task.objects.create(user=self.other_user, title="Tarefa Alheia")
        response = self.client.post(
            reverse("tasks:delete", kwargs={"pk": other_task.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_list_view_does_not_leak_other_user_tasks(self) -> None:
        """Garante que a listagem de tarefas não vaza registros de outros usuários."""
        self.client.login(username=self.username, password=self.password)
        other_task = Task.objects.create(
            user=self.other_user, title="Tarefa Confidencial de B"
        )

        # Requisição padrão
        response = self.client.get(reverse("tasks:list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(other_task, response.context["page_obj"])
        self.assertNotContains(response, "Tarefa Confidencial de B")

        # Requisição HTMX
        response = self.client.get(reverse("tasks:list"), HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(other_task, response.context["page_obj"])
        self.assertNotContains(response, "Tarefa Confidencial de B")

    def test_toggle_view_success_and_trigger(self) -> None:
        """Garante que alternar o status ativa o serviço e emite o trigger de atualização de stats."""
        self.client.login(username=self.username, password=self.password)

        self.assertFalse(self.task.is_completed)
        response = self.client.post(
            reverse("tasks:toggle", kwargs={"pk": self.task.pk}), HTTP_HX_REQUEST="true"
        )

        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)
        self.assertEqual(response["HX-Trigger"], "task-updated")

        # Reabre
        response = self.client.post(
            reverse("tasks:toggle", kwargs={"pk": self.task.pk}), HTTP_HX_REQUEST="true"
        )
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_completed)
        self.assertEqual(response["HX-Trigger"], "task-updated")

    def test_edit_view_success(self) -> None:
        """Garante que a rota de edição altera os dados no banco e atualiza os stats."""
        self.client.login(username=self.username, password=self.password)

        payload = {
            "title": "Novo Título",
            "xp_reward": 50,
            "description": "Nova descrição",
        }
        response = self.client.post(
            reverse("tasks:edit", kwargs={"pk": self.task.pk}),
            payload,
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Novo Título")
        self.assertEqual(self.task.xp_reward, 50)
        self.assertEqual(response["HX-Trigger"], "task-updated")

    def test_delete_view_success_and_deducts_xp(self) -> None:
        """Garante que a rota de deleção apaga a tarefa, remove XP se ela estava concluída e emite trigger."""
        self.client.login(username=self.username, password=self.password)

        # 1. Deletar tarefa pendente (não afeta XP)
        self.assertEqual(self.user.experience_points, 0)
        response = self.client.post(
            reverse("tasks:delete", kwargs={"pk": self.task.pk}), HTTP_HX_REQUEST="true"
        )
        self.assertEqual(response.status_code, 200)

        # Verifica se a tarefa sumiu da busca padrão (está inativa)
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())
        # Mas continua existindo logicamente como excluída no banco
        soft_deleted_task = Task.objects.all_with_deleted().get(pk=self.task.pk)
        self.assertTrue(soft_deleted_task.is_deleted)
        self.assertIsNotNone(soft_deleted_task.deleted_at)

        self.assertEqual(response["HX-Trigger"], "task-updated")
        self.user.refresh_from_db()
        self.assertEqual(self.user.experience_points, 0)

        # 2. Deletar tarefa concluída (deduz XP)
        self.user.experience_points = 50
        self.user.save()

        completed_task = Task.objects.create(
            user=self.user,
            title="Concluída",
            xp_reward=20,
            is_completed=True,
            completed_at=timezone.now(),
        )

        response = self.client.post(
            reverse("tasks:delete", kwargs={"pk": completed_task.pk}),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)

        # Verifica se sumiu da busca padrão
        self.assertFalse(Task.objects.filter(pk=completed_task.pk).exists())
        # Mas continua existindo como excluída no banco
        soft_deleted_completed = Task.objects.all_with_deleted().get(
            pk=completed_task.pk
        )
        self.assertTrue(soft_deleted_completed.is_deleted)
        self.assertIsNotNone(soft_deleted_completed.deleted_at)

        self.assertEqual(response["HX-Trigger"], "task-updated")

        self.user.refresh_from_db()
        # XP deve cair de 50 para 30
        self.assertEqual(self.user.experience_points, 30)

    def test_stats_partial_view_response(self) -> None:
        """Garante que a stats view do accounts renderiza os valores atuais do usuário."""
        self.client.login(username=self.username, password=self.password)

        self.user.experience_points = 75
        self.user.level = 4
        self.user.save()

        response = self.client.get(reverse("stats"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "75 XP")
        self.assertContains(response, "4")

    def test_list_view_status_all(self) -> None:
        """Garante que a visualização de lista com status 'all' funciona e retorna ordenação correta."""
        self.client.login(username=self.username, password=self.password)
        completed_task = Task.objects.create(
            user=self.user,
            title="Concluída",
            is_completed=True,
            completed_at=timezone.now(),
        )
        # Solicita listagem com status 'all'
        response = self.client.get(
            reverse("tasks:list"), {"status": "all"}, HTTP_HX_REQUEST="true"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.task, response.context["page_obj"])
        self.assertIn(completed_task, response.context["page_obj"])

    def test_create_view_invalid_form(self) -> None:
        """Garante que enviar um formulário de criação inválido retorna o formulário com erros."""
        self.client.login(username=self.username, password=self.password)
        # Título em branco é inválido
        payload = {
            "title": "   ",
            "description": "Incorreta",
            "xp_reward": 10,
        }
        response = self.client.post(
            reverse("tasks:create"), payload, HTTP_HX_REQUEST="true"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/partials/task_list.html")
        # Deve retornar o formulário na resposta contendo erros
        self.assertFalse(response.context["form"].is_valid())

    def test_edit_view_invalid_form(self) -> None:
        """Garante que enviar um formulário de edição inválido retorna a view de edição com erros."""
        self.client.login(username=self.username, password=self.password)
        # Título em branco é inválido
        payload = {
            "title": "   ",
            "description": "Editada",
            "xp_reward": 10,
        }
        response = self.client.post(
            reverse("tasks:edit", kwargs={"pk": self.task.pk}),
            payload,
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/partials/task_edit.html")
        self.assertFalse(response.context["form"].is_valid())

    def test_detail_view_success(self) -> None:
        """Garante que obter detalhes da tarefa retorna o template parcial de linha correspondente."""
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse("tasks:detail", kwargs={"pk": self.task.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/partials/task_row.html")
        self.assertContains(response, self.task.title)


class TaskAdminTests(TestCase):
    def setUp(self) -> None:
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="Password123"
        )
        self.client.login(username="admin", password="Password123")

    def test_admin_changelist_no_n_plus_one_queries(self) -> None:
        """Garante que o número de queries para listar tarefas no admin não cresce linearmente com a quantidade de tarefas."""
        url = reverse("admin:tasks_task_changelist")

        # Criar 1 tarefa
        u1 = User.objects.create_user(username="u1", password="Password123")
        Task.objects.create(user=u1, title="T1")

        # Medir queries com 1 tarefa
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as ctx_1:
            self.client.get(url)
        queries_with_one = len(ctx_1.captured_queries)

        # Criar mais 10 tarefas de usuários diferentes
        for i in range(10):
            u = User.objects.create_user(username=f"user_{i}", password="Password123")
            Task.objects.create(user=u, title=f"T_{i}")

        with CaptureQueriesContext(connection) as ctx_10:
            self.client.get(url)
        queries_with_many = len(ctx_10.captured_queries)

        # Se houver N+1, queries_with_many será maior que queries_with_one em pelo menos 10 queries.
        # Sem N+1, o número de queries deve ser o mesmo (ou quase o mesmo).
        self.assertLessEqual(
            queries_with_many - queries_with_one,
            1,
            f"N+1 detectado: queries com 1 task = {queries_with_one}, com 11 tasks = {queries_with_many}",
        )


class TaskSoftDeleteTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="testuser", password="Password123"
        )
        self.task1 = Task.objects.create(user=self.user, title="Task 1")
        self.task2 = Task.objects.create(user=self.user, title="Task 2")

    def test_model_delete_performs_soft_delete(self) -> None:
        """Garante que deletar a model via task.delete() marca a tarefa como excluída no banco."""
        self.task1.delete()

        # Não deve ser encontrada no manager padrão
        self.assertFalse(Task.objects.filter(pk=self.task1.pk).exists())

        # Deve ser encontrada com all_with_deleted
        task = Task.objects.all_with_deleted().get(pk=self.task1.pk)
        self.assertTrue(task.is_deleted)
        self.assertIsNotNone(task.deleted_at)

        # A outra tarefa deve continuar ativa
        self.assertTrue(Task.objects.filter(pk=self.task2.pk).exists())

    def test_queryset_delete_performs_soft_delete(self) -> None:
        """Garante que a deleção em lote no QuerySet marca as tarefas como excluídas."""
        Task.objects.all().delete()

        # Nenhuma tarefa deve estar ativa no manager padrão
        self.assertEqual(Task.objects.count(), 0)

        # Ambas devem estar excluídas logicamente
        all_tasks = Task.objects.all_with_deleted()
        self.assertEqual(all_tasks.count(), 2)
        for task in all_tasks:
            self.assertTrue(task.is_deleted)
            self.assertIsNotNone(task.deleted_at)


class TaskCRUDIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.username = "cruduser"
        self.password = "SecurePassword123"
        self.user = User.objects.create_user(
            username=self.username,
            email="cruduser@example.com",
            password=self.password,
        )
        self.client.login(username=self.username, password=self.password)

    def test_full_crud_lifecycle(self) -> None:
        """Testa o fluxo completo do CRUD (Create, Read, Update, Delete) de uma tarefa."""

        # 1. CREATE
        create_url = reverse("tasks:create")
        payload = {
            "title": "Tarefa de Integração",
            "description": "Uma tarefa criada durante o teste de integração",
            "xp_reward": 50,
            "due_date": (timezone.localdate() + timezone.timedelta(days=2)).strftime(
                "%Y-%m-%d"
            ),
        }

        # O formulário de criação retorna o template parcial tasks/partials/task_list.html sob HTMX
        response = self.client.post(create_url, payload, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/partials/task_list.html")
        self.assertEqual(response["HX-Trigger"], "task-updated")

        # Verifica se o objeto foi criado no banco
        task = Task.objects.filter(title="Tarefa de Integração", user=self.user).first()
        self.assertIsNotNone(task)
        self.assertEqual(
            task.description, "Uma tarefa criada durante o teste de integração"
        )
        self.assertEqual(task.xp_reward, 50)

        # Verifica se o título da tarefa aparece no HTML renderizado
        self.assertContains(response, "Tarefa de Integração")

        # 2. READ
        list_url = reverse("tasks:list")

        # Requisição normal (não-HTMX) para listagem
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/task_list_page.html")
        self.assertIn(task, response.context["page_obj"])
        self.assertContains(response, "Tarefa de Integração")

        # Requisição HTMX para listagem com busca (q="Integração")
        response = self.client.get(
            list_url, {"q": "Integração"}, HTTP_HX_REQUEST="true"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/partials/task_list.html")
        self.assertIn(task, response.context["page_obj"])
        self.assertContains(response, "Tarefa de Integração")

        # Busca por algo que não existe
        response = self.client.get(
            list_url, {"q": "Inexistente"}, HTTP_HX_REQUEST="true"
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(task, response.context["page_obj"])
        self.assertNotContains(response, "Tarefa de Integração")

        # 3. UPDATE
        edit_url = reverse("tasks:edit", kwargs={"pk": task.pk})

        # GET na view de edição deve retornar o template do formulário inline
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/partials/task_edit.html")

        # POST para atualizar os dados da tarefa
        update_payload = {
            "title": "Tarefa de Integração Atualizada",
            "description": "Descrição atualizada no teste de integração",
            "xp_reward": 75,
            "due_date": (timezone.localdate() + timezone.timedelta(days=3)).strftime(
                "%Y-%m-%d"
            ),
        }
        response = self.client.post(edit_url, update_payload, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/partials/task_row.html")
        self.assertEqual(response["HX-Trigger"], "task-updated")

        # Valida alteração no banco de dados
        task.refresh_from_db()
        self.assertEqual(task.title, "Tarefa de Integração Atualizada")
        self.assertEqual(
            task.description, "Descrição atualizada no teste de integração"
        )
        self.assertEqual(task.xp_reward, 75)

        # Valida retorno no HTML do fragmento da linha
        self.assertContains(response, "Tarefa de Integração Atualizada")
        self.assertContains(response, "75 XP")

        # 4. DELETE
        delete_url = reverse("tasks:delete", kwargs={"pk": task.pk})

        response = self.client.post(delete_url, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/partials/task_list.html")
        self.assertEqual(response["HX-Trigger"], "task-updated")

        # Verifica soft delete no banco
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())
        soft_deleted_task = Task.objects.all_with_deleted().get(pk=task.pk)
        self.assertTrue(soft_deleted_task.is_deleted)
        self.assertIsNotNone(soft_deleted_task.deleted_at)

        # Verifica se o item não aparece mais na listagem retornada
        self.assertNotContains(response, "Tarefa de Integração Atualizada")
