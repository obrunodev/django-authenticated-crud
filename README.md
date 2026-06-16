# django-authenticated-crud

Um projeto focado no desenvolvimento de um CRUD utilizando as melhores práticas de engenharia de software e padrões modernos do ecossistema Python. Este repositório serve como um laboratório de estudos focado em arquitetura sênior, integrando testes robustos, validação estrita e automação de ambiente.

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

### 1. Inicializando o Ambiente

O projeto utiliza um fluxo automatizado. Basta executar o comando abaixo para gerar o `.env`, rodar as migrações do banco (SQLite) e criar o superusuário administrador:

```bash
make setup
```

O projeto estará disponível em `http://127.0.0.1:8000/`.

---

## 📌 Comandos Úteis (Makefile)

| Comando | Descrição |
| :--- | :--- |
| `make setup` | Cria o `.env`, aplica `migrate` e gera o superuser padrão |
| `make run` | Inicia o servidor de desenvolvimento do Django |
| `make migrate` | Aplica as migrações pendentes no banco de dados |
