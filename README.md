
# Documentação Sistema Integrado de Gestão de Ordens de Serviço (MVP)

## Visão Geral

**Framework:** Django + Django REST Framework  
**Banco de Dados:** PostgreSQL  
**Autenticação:** JWT (com djangorestframework-simplejwt)  
**Arquitetura:** API RESTful  
**LGPD:** Em conformidade com a LGPD.  
**Hashing de Senhas:** As senhas dos usuários são armazenadas usando o sistema de hashing padrão e seguro do Django (PBKDF2).  
**Criptografia de PII:** Dados pessoais identificáveis (PII), como e-mail de usuário, nome de cliente (OS), CPF (OS) e descrição (OS), são criptografados no banco de dados em nível de aplicação.  
**Anonimização de Resposta:** O CPF original nunca é retornado em respostas da API. Apenas uma versão anonimizada (ex: 123.***.***-00) é exibida.

---

## Endpoints da API

**URL Base:** `/api/v1/`

---

### Autenticação e Usuários

#### `POST /api/v1/auth/register/`

**Descrição:** Cadastro de novo usuário.

**Body:**

```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string"
}
````

**Resposta:** `201 Created` + dados do usuário (sem senha).

---

#### `POST /api/v1/auth/login/`

**Descrição:** Login de usuário, retorna tokens JWT.

**Body:**

```json
{
  "username": "string",
  "password": "string"
}
```

**Resposta:** `200 OK` + `access` e `refresh` tokens.

---

#### `GET /api/v1/users/`

**Descrição:** Lista todos os usuários.
**Auth:** Bearer Token (Admin).
**Resposta:** `200 OK` + lista de usuários.

---

#### `GET /api/v1/users/{id}/`

**Descrição:** Detalha um usuário específico.
**Auth:** Bearer Token (Admin ou próprio usuário).
**Resposta:** `200 OK` + dados do usuário.

---

### Ordens de Serviço

#### `GET /api/v1/ordens-servico/`

**Descrição:** Lista todas as ordens de serviço.
**Auth:** Bearer Token (Usuário autenticado).
**Resposta:** `200 OK` + lista de ordens.
A resposta incluirá `cpf_anonimo` (ex: `123.***.***-00`) e não o campo `cpf`.

---

#### `GET /api/v1/ordens-servico/{uuid:id}/`

**Descrição:** Detalha uma ordem de serviço específica (usa UUID como ID).
**Auth:** Bearer Token.
**Resposta:** `200 OK` + dados da ordem.
A resposta incluirá `cpf_anonimo`.

---

#### `POST /api/v1/ordens-servico/`

**Descrição:** Cria nova ordem de serviço.
O campo `criado_por` é definido automaticamente para o usuário autenticado.
**Auth:** Bearer Token.

**Body:**

```json
{
  "protocol": "string",
  "so_number": "string",
  "type": "string",
  "status": "string",
  "provider": "string",
  "priority": "string",
  "recipient_name": "string",
  "cpf": "string (formato: 123.456.789-00)",
  "description": "string"
}
```

**Resposta:** `201 Created` + dados da ordem (com `cpf_anonimo`).

---

#### `PUT / PATCH /api/v1/ordens-servico/{uuid:id}/`

**Descrição:** Atualiza uma ordem de serviço (parcialmente com PATCH ou totalmente com PUT).
**Auth:** Bearer Token.

**Body:** Mesmo do `POST` (campos parciais são aceitos com `PATCH`).
**Resposta:** `200 OK` + dados atualizados (com `cpf_anonimo`).

---

#### `DELETE /api/v1/ordens-servico/{uuid:id}/`

**Descrição:** Remove uma ordem de serviço.
**Auth:** Bearer Token.
**Resposta:** `204 No Content`.

---

#### `POST /api/v1/ordens-servico/importar-csv/`

**Descrição:** Importa uma lista de ordens de serviço via arquivo CSV.
`criado_por` é definido para o usuário que fez o upload.
**Auth:** Bearer Token.

**Body:** `multipart/form-data` com um campo `file` contendo o arquivo CSV.

**Colunas do CSV:**
`protocol,so_number,type,status,recipient_name,cpf,provider,priority,description`

**Resposta:**
`201 Created` + `{"message": "Importado com sucesso X ordens de serviço."}`

---

## Estrutura de Pastas

``` Markdown
projeto/
├── config/                  # Settings, urls, wsgi (Django core)
├── core/                    # App principal
│   ├── models.py            # User e OrdemServico (com campos criptografados)
│   ├── serializers.py       # Serializers DRF (com lógica de anonimização)
│   ├── views.py             # Views (API)
│   ├── urls.py              # Rotas
│   └── ...
├── manage.py
├── requirements.txt
└── .env.example             # Exemplo de variáveis de ambiente
```
