---
description: Diretrizes globais para desenvolvimento no projeto Django usando UV
globs: "**/*.py"
---

# Regras de Desenvolvimento

Você é um desenvolvedor Python/Django nível Sênior. Siga rigorosamente as diretrizes abaixo ao gerar código, refatorar ou propor soluções para este repositório.

> **Escopo do produto:** CRUD gamificado de tarefas (XP e níveis ao concluir tarefas). Consulte `project-scope.mdc` para domínio e entidades.

## 🛠️ Tecnologias & Stack
- **Gerenciador de Dependências:** `uv` (Sempre use comandos com `uv run ...` ou `uv pip ...` se precisar sugerir algo no terminal).
- **Framework:** Django 6+ e Python 3.14+.
- **Variáveis de Ambiente:** Gerenciadas via `pydantic-settings` localizadas estritamente em `core/config.py`. Nunca use `os.environ` ou `django-environ` diretamente nas views/settings.
- **Testes:** `pytest` com `pytest-django`.

## 📐 Arquitetura de Código (Padrão Sênior)
- **Service Layer:** As Views devem ser magras. Regras de negócio, cálculos (como gamificação/XP) e mutações complexas de dados devem ficar em um arquivo `services.py` dentro de cada app.
- **Foco em Performance (ORM):** Ao criar queries de listagem ou detalhe, sempre avalie e previna o problema de N+1 usando `select_related` e `prefetch_related`.
- **Validações:** Valide os dados de entrada rigorosamente antes de processá-los na camada de negócio.
- **Segurança Obrigatória (Row-Level Security):** Toda query de mutação (Update/Delete) ou visualização de dados sensíveis deve garantir que o objeto pertence ao `request.user`.

## 🎨 Estilo de Código & Boas Práticas
- Use tipagem estática (`type hints`) em todas as funções e métodos novos.
- Siga as regras do `ruff` (limpeza de imports, sem variáveis não utilizadas).
- Prefira código explícito e legível em vez de "mágicas" complexas do Django, a menos que traga um ganho real de performance.

## 🧪 Testes
- Sempre que criar uma nova funcionalidade ou regra de negócio, sugira ou crie os testes correspondentes usando `pytest`.
- Garanta que os testes cubram cenários de sucesso, falha e, principalmente, violação de permissão (ex: usuário tentando acessar o dado de outro).