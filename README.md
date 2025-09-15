# Documentação Sistema Integrado de Gestão de Ordens de Serviço (MVP)

## Visão Geral

- **Framework:** Django + Django REST Framework
- **Banco de Dados:** PostgreSQL
- **Autenticação:** JWT (simples, com `djangorestframework-simplejwt`)
- **Arquitetura:** MVC (Model-View-Controller via serializers/views/routers)
- **LGPD:** Sem armazenamento de dados sensíveis além do necessário, senhas com salt fixo

---

## Endpoints da API

### Autenticação e Usuários

#### `POST /api/v1/auth/register/`
- **Descrição:** Cadastro de novo usuário
- **Body:**
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string"
  }
  ```
- **Resposta:** 201 Created + dados do usuário (sem senha)

#### `POST /api/v1/auth/login/`
- **Descrição:** Login de usuário, retorna tokens JWT
- **Body:**
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Resposta:** 200 OK + `access` e `refresh` tokens

#### `GET /api/v1/users/`
- **Descrição:** Lista todos os usuários (apenas admin)
- **Auth:** Bearer Token (admin)
- **Resposta:** 200 OK + lista de usuários

#### `GET /api/v1/users/{id}/`
- **Descrição:** Detalha um usuário específico
- **Auth:** Bearer Token (admin ou próprio usuário)
- **Resposta:** 200 OK + dados do usuário

#### `PUT /api/v1/users/{id}/`
- **Descrição:** Atualiza dados do usuário
- **Auth:** Bearer Token (admin ou próprio usuário)
- **Body:** mesmo do register
- **Resposta:** 200 OK + dados atualizados

#### `DELETE /api/v1/users/{id}/`
- **Descrição:** Remove usuário
- **Auth:** Bearer Token (admin)
- **Resposta:** 204 No Content

---

### Ordens de Serviço

#### `GET /api/v1/ordens-servico/`
- **Descrição:** Lista todas as ordens de serviço
- **Auth:** Bearer Token (usuário autenticado)
- **Resposta:** 200 OK + lista de ordens

#### `GET /api/v1/ordens-servico/{id}/`
- **Descrição:** Detalha uma ordem de serviço
- **Auth:** Bearer Token
- **Resposta:** 200 OK + dados da ordem

#### `POST /api/v1/ordens-servico/`
- **Descrição:** Cria nova ordem de serviço
- **Auth:** Bearer Token
- **Body:**
  ```json
  {
    "cliente": "string",
    "descricao": "string",
    "prioridade": "alta|media|baixa",
    "status": "pendente|em_andamento|concluida"
  }
  ```
- **Resposta:** 201 Created + dados da ordem

#### `PUT /api/v1/ordens-servico/{id}/`
- **Descrição:** Atualiza ordem de serviço
- **Auth:** Bearer Token
- **Body:** mesmo do POST
- **Resposta:** 200 OK + dados atualizados

#### `DELETE /api/v1/ordens-servico/{id}/`
- **Descrição:** Remove ordem de serviço
- **Auth:** Bearer Token (admin ou criador)
- **Resposta:** 204 No Content

#### `POST /api/v1/ordens-servico/importar-csv/`
- **Descrição:** Importa ordens de serviço via CSV
- **Auth:** Bearer Token (admin)
- **Body:** arquivo CSV com colunas: `cliente,descricao,prioridade,status`
- **Resposta:** 201 Created + número de ordens importadas

---

## Estrutura de Pastas (Django MVC)

```
projeto/
├── config/                  # Settings, urls, wsgi (Django core)
├── core/                    # App principal
│   ├── models.py            # User e OrdemServico
│   ├── serializers.py       # Serializers DRF
│   ├── views.py             # Views (API)
│   ├── urls.py              # Rotas
│   └── permissions.py       # Permissões custom (ex: IsAdminOrOwner)
├── manage.py
├── requirements.txt         # Freeze das dependências
└── .github/workflows/test.yml  # GitHub Action
```

---
