# setup.py
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_setup():
    base_dir = Path(__file__).resolve().parent
    env_file = base_dir / ".env"
    sample_file = base_dir / ".env.sample"

    # 1. Copia o arquivo .env
    print("=> Verificando arquivo .env...")
    if not env_file.exists():
        if sample_file.exists():
            shutil.copy(sample_file, env_file)
            print("   .env criado com sucesso a partir do .env.sample!")
        else:
            print("   Erro: .env.sample não foi encontrado na raiz.")
            sys.exit(1)
    else:
        print("   O arquivo .env já existe. Pulando cópia.")

    # 2. Roda as migrações usando o uv
    print("\n=> Rodando as migrações do banco de dados...")
    try:
        subprocess.run(["uv", "run", "python", "manage.py", "migrate"], check=True)
    except subprocess.CalledProcessError:
        print("   Erro ao rodar as migrações.")
        sys.exit(1)

    # 3. Cria o superusuário de forma automatizada e multiplataforma
    print("\n=> Criando superusuário administrador...")
    env_vars = os.environ.copy()
    env_vars["DJANGO_SUPERUSER_USERNAME"] = "admin"
    env_vars["DJANGO_SUPERUSER_PASSWORD"] = "sample123"
    env_vars["DJANGO_SUPERUSER_EMAIL"] = "admin@example.com"

    try:
        # O argumento --noinput impede o Django de pedir dados no teclado
        subprocess.run(
            ["uv", "run", "python", "manage.py", "createsuperuser", "--noinput"],
            env=env_vars,
            check=True,
        )
        print("   Superusuário 'admin' criado com sucesso!")
    except subprocess.CalledProcessError:
        print("   Aviso: Superusuário já existe ou ocorreu um erro ao criar.")

    print("\n=> Setup concluído com sucesso!")


if __name__ == "__main__":
    run_setup()
