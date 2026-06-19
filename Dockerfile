# Estágio 1: Builder (Construção do Ambiente)
FROM ghcr.io/astral-sh/uv:latest AS uv_setup
FROM python:3.14-slim-bookworm AS builder

# Configurações para otimizar o uv e compilação do python
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copia o binário do uv diretamente da imagem oficial do Astral UV
COPY --from=uv_setup /uv /uvx /bin/

# Usa montagem de cache para acelerar builds subsequentes e sincroniza dependências
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copia o código da aplicação para o container
COPY . .

# Sincroniza o projeto em si (sem dependências de desenvolvimento)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Coleta os arquivos estáticos do Django usando variáveis dummy para passar pelas validações de ambiente do Pydantic
RUN ENVIRONMENT=local SECRET_KEY="build-time-dummy-key" DEBUG=true \
    /app/.venv/bin/python manage.py collectstatic --noinput


# Estágio 2: Runner (Execução em Produção)
FROM python:3.14-slim-bookworm AS runner

# Instala certificados CA para conexões HTTPS externas
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Cria um usuário não-privilegiado por motivos de segurança
RUN groupadd -r django && useradd -r -g django django

WORKDIR /app

# Copia o ambiente virtual criado e otimizado no estágio anterior
COPY --from=builder /app/.venv /app/.venv

# Copia os arquivos do projeto e os arquivos estáticos coletados
COPY --from=builder /app /app

# Ajusta as permissões de arquivos para o novo usuário
RUN chown -R django:django /app

# Adiciona o ambiente virtual ao PATH para que o Python e os pacotes instalados fiquem acessíveis diretamente
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Alterna para o usuário não-privilegiado
USER django

# Expõe a porta padrão do Django
EXPOSE 8000

# Executa migrações de banco e inicia o servidor de desenvolvimento
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
