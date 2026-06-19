import json
import logging

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tasks.models import Task
from tasks.services import complete_task, reopen_task

User = get_user_model()


class StructuredLoggingTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            email="test@example.com",
        )
        self.task = Task.objects.create(
            user=self.user,
            title="Tarefa de Teste",
            description="Descrição do teste",
            xp_reward=15,
        )
        self.logger = logging.getLogger("critical_actions")

    def test_json_formatter(self) -> None:
        from core.logging import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="critical_actions",
            level=logging.INFO,
            pathname="test_logging.py",
            lineno=10,
            msg="Mensagem de teste",
            args=(),
            exc_info=None,
        )
        record.action = "test_action"
        record.user_id = 999
        record.custom_field = "custom_value"

        formatted_message = formatter.format(record)
        log_data = json.loads(formatted_message)

        self.assertEqual(log_data["level"], "INFO")
        self.assertEqual(log_data["logger"], "critical_actions")
        self.assertEqual(log_data["message"], "Mensagem de teste")
        self.assertEqual(log_data["action"], "test_action")
        self.assertEqual(log_data["user_id"], 999)
        self.assertEqual(log_data["custom_field"], "custom_value")
        self.assertIn("timestamp", log_data)

    def test_task_delete_emits_structured_log(self) -> None:
        with self.assertLogs("critical_actions", level="INFO") as cm:
            self.task.delete()

        delete_logs = [
            r for r in cm.records if getattr(r, "action", None) == "task_deleted"
        ]
        self.assertEqual(len(delete_logs), 1)
        log_record = delete_logs[0]
        self.assertEqual(log_record.task_id, self.task.id)
        self.assertEqual(log_record.task_title, "Tarefa de Teste")
        self.assertEqual(log_record.user_id, self.user.id)
        self.assertEqual(log_record.username, "testuser")

    def test_queryset_delete_emits_structured_logs(self) -> None:
        task2 = Task.objects.create(user=self.user, title="Outra Tarefa", xp_reward=10)
        with self.assertLogs("critical_actions", level="INFO") as cm:
            Task.objects.all().delete()

        delete_logs = [
            r for r in cm.records if getattr(r, "action", None) == "task_deleted"
        ]
        self.assertEqual(len(delete_logs), 2)
        task_ids = {r.task_id for r in delete_logs}
        self.assertEqual(task_ids, {self.task.id, task2.id})

    def test_complete_task_emits_structured_log(self) -> None:
        with self.assertLogs("critical_actions", level="INFO") as cm:
            complete_task(self.task)

        xp_logs = [r for r in cm.records if getattr(r, "action", None) == "xp_gained"]
        self.assertEqual(len(xp_logs), 1)
        log_record = xp_logs[0]
        self.assertEqual(log_record.xp_change, 15)
        self.assertEqual(log_record.previous_xp, 0)
        self.assertEqual(log_record.new_xp, 15)
        self.assertEqual(log_record.previous_level, 1)
        self.assertEqual(log_record.new_level, 1)
        self.assertEqual(log_record.task_id, self.task.id)

    def test_reopen_task_emits_structured_log(self) -> None:
        complete_task(self.task)
        self.task.refresh_from_db()

        with self.assertLogs("critical_actions", level="INFO") as cm:
            reopen_task(self.task)

        xp_logs = [r for r in cm.records if getattr(r, "action", None) == "xp_lost"]
        self.assertEqual(len(xp_logs), 1)
        log_record = xp_logs[0]
        self.assertEqual(log_record.xp_change, -15)
        self.assertEqual(log_record.previous_xp, 15)
        self.assertEqual(log_record.new_xp, 0)
        self.assertEqual(log_record.previous_level, 1)
        self.assertEqual(log_record.new_level, 1)
        self.assertEqual(log_record.task_id, self.task.id)

    def test_login_success_logging(self) -> None:
        with self.assertLogs("critical_actions", level="INFO") as cm:
            self.client.post(
                reverse("login"),
                {"username": "testuser", "password": "testpassword"},
            )

        login_logs = [
            r for r in cm.records if getattr(r, "action", None) == "login_success"
        ]
        self.assertEqual(len(login_logs), 1)
        log_record = login_logs[0]
        self.assertEqual(log_record.username, "testuser")
        self.assertEqual(log_record.user_id, self.user.id)

    def test_login_failed_logging(self) -> None:
        with self.assertLogs("critical_actions", level="WARNING") as cm:
            self.client.post(
                reverse("login"),
                {"username": "nonexistent", "password": "wrongpassword"},
            )

        failed_logs = [
            r for r in cm.records if getattr(r, "action", None) == "login_failed"
        ]
        self.assertEqual(len(failed_logs), 1)
        log_record = failed_logs[0]
        self.assertEqual(log_record.username, "nonexistent")

    def test_register_logging(self) -> None:
        with self.assertLogs("critical_actions", level="INFO") as cm:
            self.client.post(
                reverse("register"),
                {
                    "username": "newuser",
                    "email": "new@example.com",
                    "password1": "newpassword123",
                    "password2": "newpassword123",
                },
            )

        actions = [getattr(r, "action", None) for r in cm.records]
        self.assertIn("user_registered", actions)
        self.assertIn("login_success", actions)

    def test_logout_logging(self) -> None:
        self.client.login(username="testuser", password="testpassword")
        with self.assertLogs("critical_actions", level="INFO") as cm:
            self.client.post(reverse("logout"))

        logout_logs = [
            r for r in cm.records if getattr(r, "action", None) == "logout_success"
        ]
        self.assertEqual(len(logout_logs), 1)
        log_record = logout_logs[0]
        self.assertEqual(log_record.username, "testuser")
        self.assertEqual(log_record.user_id, self.user.id)
