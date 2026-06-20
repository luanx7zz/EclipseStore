# Correções aplicadas nesta versão

- Removidos `__pycache__` e arquivos `.pyc`.
- Corrigido `database/extensions/boost.json` vazio para `{}`.
- Removida URL real do MongoDB de `configs/config_mongo.json`.
- Criado `config.json` seguro com placeholders; `start.py` injeta Secrets/ENV ao iniciar.
- Melhorado `start.py` para validar `BOT_TOKEN` e `MONGO_URL` antes de importar o bot.
- Corrigido `functions/payments/api_client.py` para fechar sessão `aiohttp` no shutdown e reduzir erro `Unclosed client session`.
- Atualizado `.env.example` com `BOT_ID`, `OWNER_ID`, `SERVER_ID`, `API_URL` e `PAY_API_URL`.
- Atualizado `.gitignore` para evitar backup de cache, logs, zips e secrets.

## Antes de rodar no Replit novo

Configure em Secrets:
- `BOT_TOKEN`
- `MONGO_URL`
- `BOT_ID`
- `OWNER_ID`
- `SERVER_ID`

Depois rode:

```bash
pip install -r requirements.txt
python start.py
```
