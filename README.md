# SIGTEC API

Backend em **FastAPI** para o Sistema Integrado de Gestão do Parque Tecnológico.

A API utiliza **MySQL**, **SQLAlchemy**, **Alembic** para migrations e **JWT** para autenticação.

---

# Tecnologias

* FastAPI
* SQLAlchemy
* Alembic
* MySQL
* PyMySQL
* JWT
* Uvicorn
* Docker (opcional)

---

# Arquitetura

```text
Route
  ↓
Service
  ↓
Repository
  ↓
MySQL
```

---

# Módulos

* Auth
* Users
* Equipments
* Movements
* History
* Dashboard

---

# Pré-requisitos

* Python 3.11+
* MySQL 8 ou Docker Desktop
* Git (opcional)

---

# 1. Clonar o projeto

```powershell
git clone <url-do-repositorio>
cd Back-end-Hackthon
```

Ou apenas entre na pasta caso o projeto já esteja baixado.

---

# 2. Criar o ambiente virtual

```powershell
python -m venv .venv
```

### Caso a criação demore

A criação da `.venv` pode levar alguns segundos.

**Não interrompa o comando.**

Se aparecer algo como:

```text
KeyboardInterrupt
```

significa que a criação foi cancelada antes do término e a pasta `.venv` ficará incompleta.

Nesse caso execute:

```powershell
Remove-Item -Recurse -Force .venv
python -m venv .venv
```

---

# 3. Ativar o ambiente virtual

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Se aparecer:

```text
(.venv)
```

na frente do terminal, está funcionando.

---

## Caso o PowerShell bloqueie a execução

Execute apenas uma vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Depois:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## Caso apareça

```text
.\.venv\Scripts\Activate.ps1 não é reconhecido
```

Verifique se a pasta foi criada corretamente:

```powershell
dir .\.venv\Scripts
```

O resultado esperado deve conter arquivos semelhantes a:

```text
Activate.ps1
activate.bat
activate
pip.exe
python.exe
pythonw.exe
```

Se aparecer apenas:

```text
python.exe
pythonw.exe
```

A criação da `.venv` falhou.

Apague e recrie:

```powershell
Remove-Item -Recurse -Force .venv
python -m venv .venv
```

---

# 4. Instalar as dependências

```powershell
pip install -r requirements.txt
```

Ou:

```powershell
python -m pip install -r requirements.txt
```

Confira se tudo foi instalado:

```powershell
pip list
```

---

# 5. Configurar o banco

Você pode utilizar MySQL instalado ou Docker.

## Opção A — Docker (recomendado)

```powershell
docker run --name sigtec-mysql ^
-e MYSQL_ROOT_PASSWORD=aluno ^
-e MYSQL_DATABASE=sigtec ^
-p 3306:3306 ^
-d mysql:8
```

Verificar:

```powershell
docker ps
```

Parar:

```powershell
docker stop sigtec-mysql
```

Iniciar novamente:

```powershell
docker start sigtec-mysql
```

---

## Opção B — MySQL instalado

Caso possua MySQL instalado:

```powershell
mysql -u root -p
```

Se aparecer:

```text
mysql não é reconhecido
```

Significa que:

* o MySQL Client não está instalado; ou
* o executável não está no PATH.

Nesse caso utilize Docker ou instale o MySQL Client.

Depois crie o banco:

```sql
CREATE DATABASE sigtec
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

---

# 6. Configurar o arquivo `.env`

Crie um arquivo `.env` na raiz do projeto.

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=sigtec
DB_USER=root
DB_PASSWORD=aluno

JWT_SECRET_KEY=chave_secreta_de_teste_para_o_ambiente_de_desenvolvimento_123!

ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Caso utilize outra porta ou senha, ajuste esses valores.

---

# 7. Executar as migrations

```powershell
python -m alembic upgrade head
```

Verificar migration atual:

```powershell
python -m alembic current
```

Resultado esperado:

```text
20260705_0003 (head)
```

---

# 8. Inserir empresa, gestor e funcionario de teste

Depois de executar as migrations, entre no MySQL:

```powershell
mysql -u root -p sigtec
```

Execute os inserts abaixo para criar a empresa `stgaioro`, um gestor e um funcionario:

```sql
INSERT INTO escolas (nome, codigo, endereco)
VALUES ('STGAIORO', 'stgaioro', 'Empresa STGAIORO')
ON DUPLICATE KEY UPDATE
    nome = VALUES(nome),
    endereco = VALUES(endereco);

INSERT INTO usuarios (
    nome,
    matricula,
    email,
    senha_hash,
    perfil,
    escola_id,
    ativo,
    aprovado,
    aprovado_em,
    pode_ver_dashboard,
    pode_transferir,
    pode_criar_equipamento,
    pode_editar_equipamento,
    pode_abrir_chamado,
    pode_gerenciar_usuarios
)
VALUES (
    'Gestor STGAIORO',
    'GESTOR-STGAIORO',
    'gestor@stgaioro.com',
    'gestor123',
    'MANAGER',
    (SELECT id FROM escolas WHERE codigo = 'stgaioro'),
    1,
    1,
    NOW(),
    1,
    1,
    1,
    1,
    1,
    1
)
ON DUPLICATE KEY UPDATE
    nome = VALUES(nome),
    senha_hash = VALUES(senha_hash),
    perfil = VALUES(perfil),
    escola_id = VALUES(escola_id),
    ativo = VALUES(ativo),
    aprovado = VALUES(aprovado),
    pode_ver_dashboard = VALUES(pode_ver_dashboard),
    pode_transferir = VALUES(pode_transferir),
    pode_criar_equipamento = VALUES(pode_criar_equipamento),
    pode_editar_equipamento = VALUES(pode_editar_equipamento),
    pode_abrir_chamado = VALUES(pode_abrir_chamado),
    pode_gerenciar_usuarios = VALUES(pode_gerenciar_usuarios);

INSERT INTO usuarios (
    nome,
    matricula,
    email,
    senha_hash,
    perfil,
    escola_id,
    ativo,
    aprovado,
    aprovado_em,
    pode_ver_dashboard,
    pode_transferir,
    pode_criar_equipamento,
    pode_editar_equipamento,
    pode_abrir_chamado,
    pode_gerenciar_usuarios
)
VALUES (
    'Funcionario STGAIORO',
    'FUNC-STGAIORO',
    'funcionario@stgaioro.com',
    'funcionario123',
    'COMMON',
    (SELECT id FROM escolas WHERE codigo = 'stgaioro'),
    1,
    1,
    NOW(),
    0,
    0,
    0,
    0,
    1,
    0
)
ON DUPLICATE KEY UPDATE
    nome = VALUES(nome),
    senha_hash = VALUES(senha_hash),
    perfil = VALUES(perfil),
    escola_id = VALUES(escola_id),
    ativo = VALUES(ativo),
    aprovado = VALUES(aprovado),
    pode_ver_dashboard = VALUES(pode_ver_dashboard),
    pode_transferir = VALUES(pode_transferir),
    pode_criar_equipamento = VALUES(pode_criar_equipamento),
    pode_editar_equipamento = VALUES(pode_editar_equipamento),
    pode_abrir_chamado = VALUES(pode_abrir_chamado),
    pode_gerenciar_usuarios = VALUES(pode_gerenciar_usuarios);
```

Logins criados:

| Perfil | Login | Senha |
| ------ | ----- | ----- |
| Gestor | `gestor@stgaioro.com` | `gestor123` |
| Funcionario | `funcionario@stgaioro.com` | `funcionario123` |

---

# 9. Executar a API

```powershell
python -m uvicorn main:app --reload
```

---

# 10. Acessar a aplicação

API:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

# 11. Testar conexão com o banco

```text
GET /db-test
```

Resposta esperada:

```json
{
  "message": "Conexao com MySQL funcionando",
  "database": "sigtec"
}
```

---

# Comandos úteis do Alembic

Nova migration:

```powershell
python -m alembic revision --autogenerate -m "descricao"
```

Aplicar migrations:

```powershell
python -m alembic upgrade head
```

Migration atual:

```powershell
python -m alembic current
```

Histórico:

```powershell
python -m alembic history
```

---

# Endpoints principais

| Método | Endpoint        | Descrição               |
| ------ | --------------- | ----------------------- |
| GET    | `/`             | Health Check            |
| GET    | `/db-test`      | Testa conexão com MySQL |
| POST   | `/auth/login`   | Login                   |
| POST   | `/auth/refresh` | Renovar Token           |
| POST   | `/auth/logout`  | Logout                  |
| GET    | `/auth/me`      | Usuário autenticado     |

Os demais endpoints podem ser consultados em:

```text
/docs
```

---

# Problemas comuns

## `.venv\Scripts\Activate.ps1 não é reconhecido`

A criação da `.venv` falhou.

Execute:

```powershell
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

## `KeyboardInterrupt`

Você interrompeu a criação da `.venv`.

Apague a pasta e recrie.

---

## `No module named fastapi`

Instale as dependências:

```powershell
pip install -r requirements.txt
```

---

## `No module named alembic`

```powershell
pip install -r requirements.txt
```

---

## `Unknown database 'sigtec'`

Crie o banco:

```sql
CREATE DATABASE sigtec;
```

---

## `Access denied for user`

Confira:

* `DB_USER`
* `DB_PASSWORD`

no arquivo `.env`.

---

## `mysql não é reconhecido`

O MySQL Client não está instalado ou não está no PATH.

Utilize Docker ou instale o cliente do MySQL.

---

## Porta 3306 ocupada

Suba o container em outra porta:

```powershell
docker run --name sigtec-mysql ^
-e MYSQL_ROOT_PASSWORD=aluno ^
-e MYSQL_DATABASE=sigtec ^
-p 3307:3306 ^
-d mysql:8
```

Atualize o `.env`:

```env
DB_PORT=3307
```
