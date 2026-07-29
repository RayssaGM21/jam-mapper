# AWS Jam Performance Hub

Aplicacao para acompanhar treinos de AWS Jam com foco em WorldSkills.

O projeto combina catalogo de challenges, progresso pessoal, tempo gasto,
tentativas, dificuldade percebida, notas e recomendacoes de treino.

## Funcionalidades

- Dashboard com progresso geral, tempo treinado e challenges restantes.
- Catalogo pesquisavel por nome, tag, servico, dificuldade e status.
- Registro pessoal por challenge: status, dificuldade, tentativas, tempo, revisao e notas.
- Analise de gargalos por tema, tempo e complexidade.
- Plano de treino semanal exportavel em CSV.
- Notas persistentes no SQLite.
- Documentacao de resolucao em Markdown por challenge.
- Classificacao de correcao por task: campo de resposta, Lambda e IA quando detectada.
- Sincronizacao com API AWS Jam quando o token estiver configurado.

## Rodar o app

```powershell
streamlit run jam_mapper\web\streamlit_app.py
```

Se a `.venv` local estiver apontando para um Python antigo, use um Python instalado
na maquina e reinstale as dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run jam_mapper\web\streamlit_app.py
```

## Backend opcional

```powershell
uvicorn jam_mapper.api.main:app --reload --port 8000
```

## Configuracao

Crie ou edite `.env`:

```env
JAM_API_BASE=https://core.proxy.prod.us-west-2.prod.jam.training.aws.dev
JAM_API_JWT=seu_token
SQLITE_PATH=./jam_mapper.db
EXPORT_PATH=./exports
```

## Controle de acesso

O painel inicia fechado por padrao. Somente enderecos em
`APP_ALLOWED_EMAILS` passam pela autenticacao, e nao existe cadastro publico.

Para um deploy pequeno, use o modo local:

```powershell
python scripts/configure_local_auth.py
```

Esse comando pede e-mail e senha no terminal e cria
`.streamlit/secrets.toml`. A senha nao e salva: somente o hash e gravado. Para
adicionar outras pessoas depois, gere hashes adicionais com
`python scripts/hash_password.py` e edite o arquivo usando como base
`.streamlit/secrets.toml.example`:

```toml
APP_AUTH_MODE = "local"
APP_ALLOWED_EMAILS = "voce@exemplo.com,professora@exemplo.com"
APP_USERS_JSON = '''{"professora@exemplo.com":{"name":"Professora","password_hash":"HASH_GERADO"}}'''
```

Para producao, o modo recomendado e OIDC (`APP_AUTH_MODE = "oidc"`) com Google
ou outro provedor OpenID Connect. Nesse modo, o provedor valida a identidade e a
aplicacao apenas confere se o e-mail retornado esta na lista autorizada. Configure
a secao `[auth]` mostrada no arquivo de exemplo e cadastre a URL de callback
`https://SEU-APP.streamlit.app/oauth2callback` no provedor.

O valor de `JAM_API_JWT` deve ser o conteudo usado no header `authorization`.

### Refresh de token

O app evita bater repetidamente na API quando o token expira. Se receber `401`,
ele tenta usar dados locais e, se configurado, tenta renovar o token respeitando
`JAM_TOKEN_REFRESH_MIN_INTERVAL_SECONDS`.

Como o endpoint de token pode depender de cookies/headers/body do seu navegador,
preencha essas variaveis somente depois de confirmar o formato do request:

```env
JAM_TOKEN_REFRESH_ENABLED=true
JAM_TOKEN_REFRESH_URL=https://vs.aws.amazon.com/token
JAM_TOKEN_REFRESH_METHOD=POST
JAM_TOKEN_REFRESH_MIN_INTERVAL_SECONDS=900
JAM_TOKEN_REFRESH_COOKIE=cole_o_cookie_do_request_aqui
JAM_TOKEN_REFRESH_HEADERS_JSON={"content-type":"application/json"}
JAM_TOKEN_REFRESH_BODY_JSON={}
```

O token renovado fica em cache no SQLite e nao e escrito no `.env`.
Nao compartilhe esse cookie em chats, prints ou commits: ele funciona como
credencial temporaria da sua sessao.

Depois do login autorizado, o backend renova o token uma vez por sessao do
Streamlit. O navegador da professora nunca recebe cookie, token ou credenciais
AWS; todas as chamadas passam pelo `JamClient` no servidor. Uma resposta `401`
tambem dispara nova tentativa de renovacao respeitando o intervalo configurado.

Importante: isso renova uma sessao AWS Jam existente. Nao e correto armazenar
usuario, senha ou MFA da conta AWS para automatizar o login do Console. Se o
cookie/refresh token de origem expirar, o administrador deve gerar um novo secret,
a menos que a AWS Jam disponibilize um fluxo OAuth oficial para essa integracao.

## Sincronizacao completa

Use `Sync full` na barra lateral do app para buscar detalhes de cada challenge,
incluindo tasks e tipo de correcao. Pela linha de comando:

```powershell
.\.venv\Scripts\activate
python scripts\sync.py
```

Use `--no-full` apenas para atualizar rapidamente o catalogo sem tasks:

```powershell
python scripts\sync.py --no-full
```

## Reports de eventos

Na pagina `Eventos`, cole IDs como:

```txt
3968ed16-8162-451e-af2e-43a380614a8c
```

O app busca `/game/participant/event/{eventId}/report` e cruza o resultado com
o catalogo para mostrar seu comportamento: resolvidos, tentativas, dicas, tempo
ate primeira tentativa e tempo ate concluir.

## Resolucoes em Markdown

Na pagina `Resolucao`, selecione um challenge e clique em
`Criar/abrir arquivo Markdown`. O arquivo sera criado em:

```txt
exports/solutions/
```

Cada arquivo vem com template por task, tipo de correcao, checklist e espaco
para comandos, evidencias e erros encontrados.

### Salvar resolucoes no GitHub

Para deploy, configure GitHub storage nos secrets/env:

```env
GITHUB_TOKEN=github_pat_...
GITHUB_REPO=usuario/repositorio
GITHUB_BRANCH=main
GITHUB_SOLUTIONS_DIR=solutions
```

O token precisa ter permissao `Contents: Read and write` no repositorio. Quando
essas variaveis existem, a pagina `Resolucao` salva os Markdown no GitHub via
Contents API. Sem elas, o app usa armazenamento local.

## Deploy rapido no Streamlit Community Cloud

1. Crie um repositorio privado no GitHub.
2. Suba o projeto sem `.env`, sem `.venv`, sem tokens e sem cookies.
3. Entre em `https://share.streamlit.io`.
4. Clique em `Create app`.
5. Selecione o repositorio, branch `main` e arquivo:

```txt
jam_mapper/web/streamlit_app.py
```

6. Em `Advanced settings` ou `Secrets`, cole:

```toml
JAM_API_BASE = "https://core.proxy.prod.us-west-2.prod.jam.training.aws.dev"
APP_AUTH_MODE = "oidc"
APP_ALLOWED_EMAILS = "voce@exemplo.com,professora@exemplo.com"
JAM_TOKEN_REFRESH_ENABLED = true
JAM_TOKEN_REFRESH_URL = "https://vs.aws.amazon.com/token"
JAM_TOKEN_REFRESH_METHOD = "POST"
JAM_TOKEN_REFRESH_COOKIE = "cookie_da_sessao"
JAM_TOKEN_REFRESH_HEADERS_JSON = '''{"content-type":"application/json"}'''
JAM_TOKEN_REFRESH_BODY_JSON = '''{}'''
SQLITE_PATH = "./jam_mapper.db"
EXPORT_PATH = "./exports"

GITHUB_TOKEN = "github_pat_..."
GITHUB_REPO = "usuario/repositorio"
GITHUB_BRANCH = "main"
GITHUB_SOLUTIONS_DIR = "solutions"

[auth]
redirect_uri = "https://SEU-APP.streamlit.app/oauth2callback"
cookie_secret = "SEGREDO_ALEATORIO_FORTE"
client_id = "CLIENT_ID"
client_secret = "CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

7. Publique o app.
8. Abra a tela `Resolucao`, escolha um challenge e clique em
`Criar/abrir Markdown`.
9. Salve a resolucao. Ela sera commitada em `solutions/<challenge>.md`.

Se o app abrir sem dados, clique em `Sync full` uma vez para popular o catalogo
a partir da API AWS Jam. O banco local do Streamlit Cloud nao deve ser tratado
como armazenamento permanente; as resolucoes ficam persistidas no GitHub.

## Banco local

O SQLite usa estas tabelas principais:

- `challenges`: catalogo vindo da AWS Jam.
- `events`: eventos sincronizados.
- `event_reports`: reports por evento.
- `jam_progress`: seu acompanhamento pessoal.
- `app_settings`: preferencias e notas globais.
