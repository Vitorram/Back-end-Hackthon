# SIGTEC API

Backend em FastAPI para o Sistema Integrado de Gestao do Parque Tecnologico. A API usa MySQL, SQLAlchemy, Alembic para migrations e JWT para autenticacao.

## Tecnologias

- FastAPI
- MySQL
- SQLAlchemy
- Alembic
- PyMySQL
- JWT
- Uvicorn
- Docker, opcional para subir o MySQL

## Arquitetura

```text
Route
  v
Service
  v
Repository
  v
MySQL
```

## Modulos

- Auth
- Users
- Equipments
- Movements
- History
- Dashboard

## Pre-requisitos

- Python 3.11 ou superior
- MySQL 8 ou Docker
- Git, opcional

## 1. Entrar na pasta do projeto

```powershell
cd C:\Users\cg3034577\Desktop\Back-end-Hackthon
```

## 2. Criar e ativar o ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativacao, rode uma vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Depois ative novamente:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 3. Instalar as dependencias

```powershell
pip install -r requirements.txt
```

## 4. Configurar o MySQL

Voce pode usar MySQL local ou Docker.

### Opcao A: MySQL via Docker

```powershell
docker run --name sigtec-mysql -e MYSQL_ROOT_PASSWORD=aluno -e MYSQL_DATABASE=sigtec -p 3306:3306 -d mysql:8
```

Comandos uteis:

```powershell
docker ps
docker stop sigtec-mysql
docker start sigtec-mysql
```

### Opcao B: MySQL instalado na maquina

Acesse o MySQL:

```powershell
mysql -u root -p
```

Crie o banco:

```sql
CREATE DATABASE sigtec CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 5. Configurar o `.env`

Crie ou edite o arquivo `.env` na raiz do projeto:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=sigtec
DB_USER=root
DB_PASSWORD=aluno
JWT_SECRET_KEY=troque-por-uma-chave-secreta-grande
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Se voce mudou porta, usuario ou senha no MySQL, ajuste esses valores no `.env`.

## 6. Rodar as migrations

Use Alembic para criar ou atualizar as tabelas:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Para conferir a migration aplicada:

```powershell
.\.venv\Scripts\python.exe -m alembic current
```

Resposta esperada:

```text
20260705_0001 (head)
```

Observacao: se o banco ja tinha tabelas criadas manualmente, a migration inicial ja esta preparada para nao tentar recriar tabelas existentes.

## 7. Rodar a API

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

A API fica disponivel em:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## 8. Testar a conexao com o banco

Com a API rodando, acesse:

```text
http://127.0.0.1:8000/db-test
```

Resposta esperada:

```json
{
  "message": "Conexao com MySQL funcionando",
  "database": "sigtec"
}
```

## Comandos Alembic uteis

Criar uma nova migration depois de alterar models:

```powershell
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "descricao da alteracao"
```

Aplicar migrations pendentes:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Ver historico:

```powershell
.\.venv\Scripts\python.exe -m alembic history
```

Ver migration atual do banco:

```powershell
.\.venv\Scripts\python.exe -m alembic current
```

## Endpoints principais

- `GET /` - health check da API
- `GET /db-test` - testa conexao com o MySQL
- `POST /auth/login` - login
- `POST /auth/refresh` - renova o token
- `POST /auth/logout` - logout
- `GET /auth/me` - dados do usuario autenticado

As demais rotas aparecem no Swagger em `/docs`.

## Problemas comuns

### `Table 'escolas' already exists`

Esse erro acontece quando o banco ja tinha tabelas antes do Alembic. Com a migration atual, rode novamente:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

### `Access denied for user`

Confira `DB_USER` e `DB_PASSWORD` no `.env`.

### `Unknown database 'sigtec'`

Crie o banco no MySQL:

```sql
CREATE DATABASE sigtec CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### `No module named alembic` ou `No module named fastapi`

Instale as dependencias dentro da `.venv`:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Porta 3306 em uso

Se ja existir um MySQL rodando na porta 3306, use outra porta no Docker:

```powershell
docker run --name sigtec-mysql -e MYSQL_ROOT_PASSWORD=aluno -e MYSQL_DATABASE=sigtec -p 3307:3306 -d mysql:8
```

Depois ajuste o `.env`:

```env
DB_PORT=3307
```
