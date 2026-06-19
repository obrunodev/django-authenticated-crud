# Guia de Configuração do Docker no Windows (WSL 2)

Este guia fornece o passo a passo para configurar e rodar a aplicação em contêineres Docker em um ambiente Windows 10/11 utilizando o WSL 2 (Windows Subsystem for Linux).

---

## 1. Pré-requisitos e Instalação

### Passo A: Habilitar Recursos do Windows e Instalar o WSL 2
1. Abra o **PowerShell** ou **Prompt de Comando (CMD)** como **Administrador** (botão direito -> Executar como Administrador).
2. Execute o comando para instalar o WSL:
   ```powershell
   wsl --install
   ```
   *Nota: Este comando instalará a distribuição padrão do Linux (Ubuntu) e ativará os recursos de virtualização necessários (Hyper-V/WSL).*
3. **Reinicie o seu computador** para concluir a instalação das atualizações necessárias do Windows.

---

### Passo B: Instalar o Docker Desktop
1. Acesse o site oficial do Docker e baixe o instalador do [Docker Desktop para Windows](https://www.docker.com/products/docker-desktop/).
2. Execute o instalador baixado (`Docker Desktop Installer.exe`).
3. Certifique-se de que a opção **"Use WSL 2 instead of Hyper-V (recommended)"** esteja marcada durante o assistente de instalação.
4. Após o término da instalação, você será solicitado a efetuar logoff ou reiniciar.
5. Inicie o **Docker Desktop** pelo menu iniciar. Aceite o contrato de termos se solicitado.

---

### Passo C: Validar a Integração com o WSL 2
1. No Docker Desktop, vá em **Settings (ícone de engrenagem no topo)** -> **General**.
2. Verifique se a opção **"Use the WSL 2 based engine"** está marcada.
3. Acesse **Settings** -> **Resources** -> **WSL Integration** e garanta que a integração esteja ativa na sua distribuição padrão (geralmente `Ubuntu`).
4. Abra um novo terminal do PowerShell e digite o comando abaixo para testar se o Docker está acessível:
   ```powershell
   docker --version
   docker compose version
   ```

---

## 2. Executando a Aplicação com Docker

A aplicação pode ser executada de duas maneiras usando o Docker configurado neste projeto:

### Opção 1: Usando Docker Compose (Recomendado)
O Docker Compose simplifica a execução gerenciando os comandos de build, criação de rede e carregamento de variáveis de ambiente.

1. **Garantir o arquivo `.env` configurado:**
   Certifique-se de que possui o arquivo `.env` na raiz do projeto configurado corretamente (veja o arquivo [.env.sample](file:///.env.sample) como base).

2. **Subir os contêineres:**
   Na raiz do seu projeto no PowerShell/Terminal, execute:
   ```powershell
   docker compose up --build
   ```
   *Este comando construirá a imagem da aplicação (usando o Dockerfile otimizado com `uv`), executará as migrações automáticas do banco e iniciará o servidor na porta 8000.*

3. **Acessar a Aplicação:**
   Abra o seu navegador e acesse: [http://localhost:8000](http://localhost:8000)

4. **Encerrar a Execução:**
   Pressione `Ctrl + C` no terminal onde o compose está rodando ou use:
   ```powershell
   docker compose down
   ```

---

### Opção 2: Usando Comandos Diretos do Docker CLI

Caso queira buildar e rodar o container do Django de forma independente:

1. **Construir a Imagem Docker:**
   ```powershell
   docker build -t django-authenticated-crud .
   ```
   *(Este comando usará as otimizações do `uv` e criará uma imagem super leve apenas com o ambiente virtual e código do projeto).*

2. **Executar o Contêiner:**
   ```powershell
   docker run -p 8000:8000 --env-file .env django-authenticated-crud
   ```
   *(O parâmetro `--env-file .env` passa todas as configurações locais do projeto diretamente para dentro do contêiner do Django).*

3. **Verificar os Contêineres ativos:**
   ```powershell
   docker ps
   ```

---

## 3. Comandos Úteis e Solução de Problemas

* **Erro de Portas Ocupadas (`port is already allocated`):**
  Certifique-se de que nenhum outro serviço esteja usando a porta 8000 localmente (por exemplo, um servidor do Django rodando diretamente no Windows fora do Docker). Pressione `Ctrl + C` nos terminais ativos ou feche os processos locais antes de rodar o Docker.

* **Rodar Comandos do Django dentro do Contêiner:**
  Para rodar comandos como criar um novo superusuário no contêiner em execução, utilize:
  ```powershell
  docker compose exec web python manage.py createsuperuser
  ```
  Ou se estiver rodando via container independente:
  ```powershell
  docker exec -it <nome_do_container> python manage.py createsuperuser
  ```

* **Limpar Cache e Imagens antigas:**
  Se precisar liberar espaço em disco no Windows:
  ```powershell
  docker system prune -f
  docker builder prune -f
  ```
