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
  - Use o model abstrato `OwnedModel` (e seu queryset/manager `OwnedQuerySet.for_user()`) definidos em `accounts/models.py` para os models que requerem posse do usuário.
  - Nas views, use o decorator `@owner_required(model_class)` definido em `accounts/decorators.py` para validar a posse de forma limpa e segura, retornando `Http404` se o objeto não pertencer ao usuário.

## 🎨 Estilo de Código & Boas Práticas
- Use tipagem estática (`type hints`) em todas as funções e métodos novos.
- Siga as regras do `ruff` (limpeza de imports, sem variáveis não utilizadas).
- Prefira código explícito e legível em vez de "mágicas" complexas do Django, a menos que traga um ganho real de performance.

## 🧪 Testes
- Sempre que criar uma nova funcionalidade ou regra de negócio, sugira ou crie os testes correspondentes usando `pytest`.
- Garanta que os testes cubram cenários de sucesso, falha e, principalmente, violação de permissão (ex: usuário tentando acessar o dado de outro).

## 🌌 Diretrizes do Antigravity AI Agent
- **Workflow de Planejamento:** Ao receber tarefas complexas, utilize a ferramenta de planejamento (`planning_mode`). Crie o `implementation_plan.md` no diretório do cérebro (`brain`) correspondente, obtenha aprovação antes da execução, gerencie o progresso usando `task.md` e conclua gerando um `walkthrough.md`.
- **Links de Arquivos:** Sempre faça referência a caminhos de arquivos e símbolos de código utilizando links no formato markdown do GitHub com o esquema `file:///` absoluto (ex: `[settings.py](file:///c:/Users/Ariadne/dev/django-authenticated-crud/core/settings/local.py)`), usando caminhos com barras normais (forward slashes) e evitando envolver o texto do link com crases (backticks).
- **Integridade de Documentação:** Preserve os comentários e docstrings existentes nas funções e arquivos modificados.
- **Aparência e Design Visual (Frontend):** Ao desenvolver telas/páginas web, utilize **Tailwind CSS v4** para estilização e **HTMX** para interações dinâmicas (retornando fragmentos de HTML quando apropriado). Aplique um design premium com paletas de cores elegantes, tipografia moderna (ex: Inter/Outfit), transições e micro-animações interativas via utilitários do Tailwind. Não utilize placeholders.
- **SEO & Acessibilidade:** Em toda página web, inclua tags de título descritivas, meta description, cabeçalho `<h1>` único por página, HTML5 semântico e IDs únicos para elementos interativos para facilitar testes de navegador com subagentes.