# Hospedar na Discloud

Este ZIP já está pronto para upload na Discloud.

## Arquivo principal

A Discloud deve iniciar pelo arquivo:

```txt
start.py
```

O `discloud.config` já está na raiz do projeto:

```txt
NAME=Eclipse Store Bot
TYPE=bot
MAIN=start.py
RAM=512
VERSION=3.11
AUTORESTART=true
```

## Variáveis obrigatórias

Cadastre no painel/Secrets da Discloud antes de iniciar:

```env
BOT_TOKEN=token_novo_do_bot
MONGO_URL=mongodb+srv://usuario:senha@cluster.mongodb.net/sync_bots
BOT_ID=id_da_aplicacao
OWNER_ID=seu_id_discord
SERVER_ID=id_do_servidor_principal
```

## Variáveis opcionais

```env
MONGO_DATABASE=sync_bots
API_URL=http://localhost:22222
PAY_API_URL=http://localhost:22222
WEBSOCKET_JWT_SECRET=troque_essa_chave
LOG_LEVEL=INFO
```

## Importante

- Não suba `.env` com token real.
- Se você já enviou token ou MongoDB público, resete o token no Discord Developer Portal e troque a senha/URL do MongoDB.
- O ZIP precisa ter `discloud.config` na raiz, junto de `start.py` e `requirements.txt`.
