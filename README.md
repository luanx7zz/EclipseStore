# 🛒 Eclipse Store Bot — Bot de Vendas Premium para Discord

> Bot de vendas profissional para Discord com carrinho, pagamentos PIX, tickets, estoque automático, cupons, clientes, ranking e muito mais.

---

## 📋 Índice

- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Comandos](#comandos)
- [Sistemas](#sistemas)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Suporte](#suporte)

---

## ✅ Requisitos

| Item | Versão mínima |
|------|--------------|
| Python | 3.11+ |
| MongoDB | Atlas (gratuito) ou auto-hospedado |
| Disnake | conforme requirements.txt |
| Conta Discord | Bot criado no Developer Portal |

---

## 🚀 Instalação

### 1. Clonar / extrair o projeto

```bash
unzip eclipse-store-refatorado.zip
cd eclipse-store-refatorado
```

### 2. Criar ambiente virtual (recomendado)

```bash
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
.venv\Scripts\activate       # Windows
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com seu editor favorito
```

Preencha **obrigatoriamente**:
```env
BOT_TOKEN=seu_token_do_discord
MONGO_URL=mongodb+srv://...
```

### 5. Iniciar o bot

```bash
python start.py
```

---

## ☁️ Instalação no Replit

1. Crie um novo Repl em branco (Python)
2. Faça upload do ZIP ou clone via Git
3. Na aba **Secrets**, adicione:
   - `BOT_TOKEN` → seu token do bot Discord
   - `MONGO_URL` → sua URL do MongoDB Atlas
4. No arquivo `.replit`, configure:
   ```toml
   run = "python start.py"
   ```
5. Clique em **Run** ✅

---

## ⚙️ Configuração

Após iniciar o bot, use os comandos de configuração no Discord:

### Configuração inicial (ordem recomendada)

1. `/setup` — Cria canais e cargos necessários automaticamente
2. `/config pagamentos` — Configure Mercado Pago, EfiBank, PushinPay ou outro gateway
3. `/painel loja` — Configure a loja (nome, imagem, cor)
4. `/produto criar` — Crie seus primeiros produtos
5. `/ticket setup` — Configure o painel de tickets
6. `/diagnostico` — Verifique se tudo está funcionando

### Configuração de Pagamentos

Configure pelo painel admin `/config pagamentos`. Gateways disponíveis:

| Gateway | Status | Tipo |
|---------|--------|------|
| **Mercado Pago** | ✅ Completo | PIX |
| **EfiBank (Gerencianet)** | ✅ Completo | PIX |
| **PushinPay** | ✅ Completo | PIX |
| **PicPay** | ✅ Completo | PIX |
| **PagBank** | ✅ Completo | PIX |
| **PIX Manual** | ✅ Completo | PIX |
| **Stripe** | ⚠️ Checkout link | Internacional |
| **PayPal** | ⚠️ Checkout link | Internacional |
| **Asaas** | ⚠️ Link de cobrança | PIX/Boleto |
| **Coinbase Commerce** | ⚠️ Checkout link | Crypto |
| **NOWPayments** | ⚠️ Invoice link | Crypto |

> **⚠️ Atenção:** Gateways marcados como "Checkout link" redirecionam para uma página externa, não geram QR Code nativo.

---

## 🌐 Variáveis de Ambiente

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `BOT_TOKEN` | ✅ Sim | Token do bot Discord |
| `MONGO_URL` | ✅ Sim | URL de conexão MongoDB |
| `API_URL` | ❌ Não | URL da API de pagamentos (padrão configurado) |
| `LOG_LEVEL` | ❌ Não | DEBUG / INFO / WARNING / ERROR (padrão: INFO) |

---

## 🔧 Comandos

### Vendas & Loja
| Comando | Descrição |
|---------|-----------|
| `/produto criar` | Cria um novo produto |
| `/produto editar` | Edita produto existente |
| `/produto listar` | Lista todos os produtos |
| `/estoque adicionar` | Adiciona itens ao estoque |
| `/estoque visualizar` | Visualiza estoque de um produto |
| `/cupom criar` | Cria cupom de desconto |
| `/cupom em-massa` | Cria cupom para toda a loja |
| `/ranking` | Exibe ranking de compradores |
| `/perfil` | Perfil do cliente |
| `/vip` | Gerencia status VIP |

### Admin & Config
| Comando | Descrição |
|---------|-----------|
| `/painel` | Painel administrativo principal |
| `/setup` | Configuração inicial do servidor |
| `/config` | Configurações avançadas |
| `/backup criar` | Cria backup manual |
| `/backup restaurar` | Restaura um backup |
| `/relatorio` | Relatório de vendas |
| `/manutencao` | Ativa/desativa modo manutenção |
| `/diagnostico` | Diagnóstico completo do sistema |
| `/logs` | Visualiza logs recentes |

### Tickets
| Comando | Descrição |
|---------|-----------|
| `/ticket setup` | Configura painel de tickets |
| `/ticket abrir` | Abre um ticket manualmente |
| `/ticket fechar` | Fecha ticket atual |
| `/ticket transcript` | Gera transcript do ticket |

### Moderação
| Comando | Descrição |
|---------|-----------|
| `/ban` | Bane um membro |
| `/expulsar` | Expulsa um membro |
| `/limpar` | Limpa mensagens do canal |
| `/castigar` | Coloca membro em timeout |
| `/falar` | Bot envia mensagem em um canal |
| `/anunciar` | Cria anúncio formatado |

### Pagamentos (Admin)
| Comando | Descrição |
|---------|-----------|
| `/gerar-pagamento` | Gera pagamento manual para cliente |
| `/entregar` | Entrega produto manualmente |
| `/cargo-temporario` | Gerencia cargos temporários |
| `/sincronizar-clientes` | Sincroniza dados de clientes |

---

## 🏗️ Estrutura do Projeto

```
eclipse-store/
├── start.py                    # Entrypoint principal ← rodar isso
├── bot.py                      # Inicialização do bot
├── requirements.txt            # Dependências Python
├── config.json                 # Config básica (tokens injetados via env)
├── .env.example                # Template de variáveis de ambiente
├── .gitignore                  # Arquivos ignorados pelo git
│
├── configs/                    # Arquivos de configuração
│   ├── config_api.json         # URL da API de pagamentos
│   ├── config_emoji.json       # Configuração de emojis
│   ├── config_mongo.json       # MongoDB (URL injetada via env)
│   ├── config_plan.json        # Configuração do plano
│   └── config_websocket.json   # WebSocket cloud/boost
│
├── core/                       # Núcleo do bot
│   ├── create_bot.py           # Factory do bot
│   ├── enable_intents.py       # Intents Discord
│   ├── log_restart.py          # Log de reinícios
│   ├── server_protection.py    # Proteção de servidor
│   └── connections/            # Conexões (MongoDB, WebSocket)
│       ├── mongo_db.py
│       └── websocket_manager.py
│
├── commands/                   # Slash Commands
│   ├── admin/                  # Comandos de administração
│   ├── mod/                    # Comandos de moderação
│   ├── vendas/                 # Comandos de vendas
│   ├── tickets/                # Comandos de tickets
│   ├── giveaways/              # Comandos de sorteios
│   └── extensions/             # Comandos de extensões
│
├── events/                     # Eventos Discord
│   ├── on_ready.py
│   ├── on_member_join.py
│   ├── on_message_edit.py
│   └── ...
│
├── modules/                    # Módulos principais (Cogs)
│   ├── loja/                   # Sistema de loja completo
│   │   ├── cart/               # Carrinho de compras
│   │   ├── products/           # Produtos
│   │   ├── categories/         # Categorias
│   │   ├── clientes/           # Clientes
│   │   ├── cashback/           # Cashback
│   │   ├── saldo/              # Sistema de saldo
│   │   ├── vips/               # VIPs
│   │   └── preferences/        # Preferências da loja
│   ├── tickets/                # Sistema de tickets
│   ├── automations/            # Automações
│   ├── cloud/                  # Integração cloud
│   ├── giveaways/              # Sorteios
│   └── protection/             # Proteção anti-raid
│
├── functions/                  # Funções utilitárias
│   ├── database.py             # Wrapper MongoDB com cache
│   ├── logger.py               # Sistema de logging centralizado
│   ├── emoji.py                # Gerenciamento de emojis
│   ├── perms.py                # Verificação de permissões
│   ├── utils.py                # Utilitários gerais
│   └── payments/               # Integrações de pagamento
│       ├── _base.py            # Base compartilhada
│       ├── create_payment.py   # Criar pagamentos
│       ├── check_payment.py    # Verificar pagamentos
│       └── ...
│
├── tasks/                      # Tasks assíncronas
│   ├── backup/                 # Backup automático
│   ├── payments/               # Monitor de pagamentos
│   ├── automations/            # Tasks de automação
│   └── ...
│
├── database/                   # Arquivos locais do banco
│   └── backups/                # Backups (gerados automaticamente)
│
├── assets/                     # Recursos estáticos
│   └── fonts/                  # Fontes para imagens
│
└── logs/                       # Logs do bot (gerado automaticamente)
    └── bot.log
```

---

## 🔒 Segurança

- **Tokens** nunca ficam no código — apenas em variáveis de ambiente
- **Permissões** verificadas antes de comandos sensíveis
- **Rate limit** por usuário em comandos de compra
- **Anti-duplicação** no processamento de pagamentos (idempotência)
- **Anti-dupla entrega** com verificação de status antes de entregar
- **Validação de estoque** antes de confirmar pagamento
- **Blacklist** configurável de usuários

---

## 📊 Sistemas

### Carrinho
- Persistente no MongoDB
- Múltiplos produtos/variações
- Expiração automática com liberação de estoque
- Cupons com validação completa
- Anti-duplicação de carrinho por usuário
- Reserva de estoque no checkout

### Pagamentos
- Verificação assíncrona via WebSocket + polling
- Anti-aprovação dupla com lock
- Expiração automática de pagamentos pendentes
- Reprocessamento de pagamentos antigos ao reiniciar
- Logs completos por transação
- Recibo automático pós-compra

### Estoque
- Estoque finito (lista de itens únicos)
- Estoque infinito (valor fixo repetível)
- Notificação automática de reestoque
- Aviso de estoque baixo via DM/canal
- Sincronização com banco central

### Tickets
- Múltiplos painéis configuráveis
- Formulários personalizados por tipo
- Limite de tickets por usuário
- Transcript HTML automático
- Assumir/transferir ticket
- Fechar/reabrir/arquivar
- Avaliação de atendimento
- Logs separados por categoria

---

## 🐛 Bugs Corrigidos nesta Versão

1. **Diretório `connections/` duplicado** — removido, apenas `core/connections/` mantido
2. **Token hardcoded em `config.json`** — removido, injetado via variável de ambiente
3. **Imports quebrados** pós-limpeza do diretório duplicado — corrigidos
4. **Arquivos de teste em produção** (`test_imap_*.py`) — removidos
5. **Pastas mortas com `(fazer do 0)`** — removidas
6. **Backups antigos** (100+ arquivos) — removidos automaticamente
7. **`start.py` sem suporte a `.env`** — adicionado suporte completo
8. **`start.py` sem logging antes de importar bot** — corrigido

---

## ❓ Suporte

Em caso de problemas:
1. Execute `/diagnostico` no Discord para ver o status do sistema
2. Verifique os logs em `logs/bot.log`
3. Confirme que `BOT_TOKEN` e `MONGO_URL` estão corretos nas secrets
