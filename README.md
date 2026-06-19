# django-authenticated-crud

CRUD autenticado de **lista de tarefas gamificada**: usuários gerenciam suas tarefas e evoluem em **nível** ao ganhar **XP** ao concluí-las. Laboratório de estudos com arquitetura sênior, testes robustos, validação estrita e automação de ambiente.

### Domínio

- **Usuário customizado** (`accounts.User`): autenticação + campos de gamificação (`experience_points`, `level`).
- **Tarefas** (próximas entregas): CRUD com isolamento por usuário; conclusão dispara cálculo de XP/nível na camada de serviços.

---

## 🚀 Tecnologias e Ferramentas

* **Framework:** [Django 6.x](https://docs.djangoproject.com/) (Uso híbrido de Class-Based Views e Function-Based Views)
* **Gerenciador de Pacotes:** [uv](https://github.com/astral-sh/uv) (Alternativa ultrarrápida ao pip/poetry)
* **Gerenciamento de Ambiente:** [Pydantic Settings v2](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) (Validação de tipos em tempo de execução para o `settings.py`)
* **Qualidade de Código:** [Ruff](https://github.com/astral-sh/ruff) (Linter e Formatter integrado)
* **Suíte de Testes:** [Pytest](https://docs.pytest.org/) & `pytest-django`

---

## 🛠️ Arquitetura do Setup

Para elevar o nível do projeto, a estrutura de configuração foi desacoplada do padrão tradicional:
* **`core/`**: Pasta raiz do projeto Django (contendo `settings.py`, `urls.py`, etc).
* **`core/config.py`**: Centraliza a classe `Settings` do Pydantic. Ela lê o arquivo `.env` e valida os tipos nativamente (como listas reais do Python via JSON nativo para o `ALLOWED_HOSTS`).
* **Script de Onboarding (`setup.py`)**: Automação multiplataforma em Python que resolve o provisionamento do banco e criação de credenciais sem depender de shell específico (Windows/Linux).

---

## 🏁 Como Rodar o Projeto

### Pré-requisitos
* Python 3.14+
* **uv** instalado na máquina ([Guia de instalação do uv](https://github.com/astral-sh/uv))
* Ferramenta `make` (opcional, para atalhos de comando)
* **Docker & Docker Compose** (opcional, para rodar em contêineres. Se estiver no Windows, siga o [Guia de Configuração do Docker no Windows](file:///c:/Users/Ariadne/dev/django-authenticated-crud/DOCKER_GUIDE.md))

### 1. Inicializando o Ambiente Local (Sem Docker)

O projeto utiliza um fluxo automatizado. Basta executar o comando abaixo para gerar o `.env`, rodar as migrações do banco (SQLite) e criar o superusuário administrador:

```bash
make setup
```

O projeto estará disponível em `http://127.0.0.1:8000/`.

---

### 2. Inicializando o Ambiente com Docker (Recomendado)

Caso prefira rodar o projeto de forma isolada usando Docker, compile a imagem e suba a aplicação com um único comando:

```bash
make docker-run
```

Este comando usa a imagem otimizada com `uv` multi-stage, aplica as migrações automaticamente e disponibiliza o projeto em `http://localhost:8000/`.

---

## 📌 Comandos Úteis (Makefile)

| Comando | Descrição |
| :--- | :--- |
| `make setup` | Cria o `.env`, aplica `migrate` e gera o superuser padrão |
| `make run` | Inicia o servidor de desenvolvimento do Django |
| `make migrate` | Aplica as migrações pendentes no banco de dados |
| `make lint` | Executa o linter (`ruff check`) |
| `make format` | Formata o código (`ruff format`) |
| `make check` | Valida lint e formatação (mesmo fluxo do CI) |
| `make docker-run` | Builda e sobe a aplicação utilizando o Docker Compose |
| `make docker-down` | Para e remove os contêineres ativos do Docker Compose |
| `make docker-shell` | Abre o terminal interativo (sh) dentro do contêiner do Django |
| `make docker-migrate` | Executa as migrações de banco diretamente no contêiner |
| `make docker-createsuperuser` | Cria um superusuário administrador dentro do contêiner |
