from disnake.ext import tasks
import asyncio
import requests
import sys
from functions.database import database as db
from functions.emoji import emoji
import core

def get_expected_bio():
    """Retorna a bio esperada do bot."""
    description = (
        "🌑 Eclipse Store — Compre com segurança, receba com rapidez.\n"
        "Atendimento de qualidade, produtos exclusivos e entrega automática."
    )
    return description

def get_current_bio(token: str, app_id: str) -> str:
    """Obtém a bio atual do bot via API do Discord."""
    try:
        url = f"https://discord.com/api/v9/applications/{app_id}"
        headers = {
            "authorization": f"Bot {token}",
            "content-type": "application/json",
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("description", "")
        return ""
    except Exception as e:
        print(f"Erro ao obter bio atual: {e}")
        return ""

def correct_bio():
    """Corrige a bio do bot para o valor esperado."""
    try:
        core.change_bio()
        return True
    except Exception as e:
        print(f"Erro ao corrigir bio: {e}")
        return False

async def send_alert_dm(bot, user_id: int, current_bio: str, expected_bio: str):
    """Envia uma DM de alerta para um usuário."""
    try:
        user = await bot.fetch_user(user_id)
        if user:
            message = (
                f"# ALERTA\n"
                f"A bio do bot foi alterada por um script externo!\n"
                f"**Bio atual:**\n{current_bio}\n\n"
                f"**Bio esperada:**\n{expected_bio}\n\n"
                f"-# O bot será desligado automaticamente para proteção."
            )
            await user.send(message)
    except Exception as e:
        print(f"Erro ao enviar DM para {user_id}: {e}")

async def shutdown_bot(bot):
    """Desliga o bot de forma segura."""
    try:
        print("⚠️ Desligando o bot devido a alteração não autorizada da bio...")
        await bot.close()
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao desligar bot: {e}")
        sys.exit(1)

# Contador de tentativas de correção consecutivas
correction_attempts = 0
max_correction_attempts = 3  # Número máximo de tentativas antes de desligar

# Variável global para armazenar a referência do bot
_bot_instance = None

@tasks.loop(minutes=1)
async def bio_monitor_task(bot):
    """Monitora e corrige a bio do bot a cada 1 minuto se estiver diferente."""
    global correction_attempts, _bot_instance
    _bot_instance = bot
    
    try:
        database = db.obter("config.json")
        token = database["bot"]["token"]
        app_id = database["bot"]["id"]
        owner_id = int(database["bot"]["owner"]) if database["bot"].get("owner") else None
        perms_ids = [int(perm_id) for perm_id in database["bot"].get("perms", []) if str(perm_id).strip()]
        
        # Obtém a bio atual e esperada
        expected_bio = get_expected_bio()
        loop = asyncio.get_event_loop()
        current_bio = await loop.run_in_executor(None, get_current_bio, token, app_id)
        
        # Compara as bios (remove espaços em branco extras para comparação)
        if current_bio.strip() != expected_bio.strip():
            print(f"⚠️ ALERTA: Bio foi alterada! Atual: {current_bio[:50]}... Esperada: {expected_bio[:50]}...")
            
            # Tenta corrigir a bio automaticamente
            print(f"Tentando corrigir a bio (tentativa {correction_attempts + 1}/{max_correction_attempts})...")
            success = await loop.run_in_executor(None, correct_bio)
            
            if success:
                correction_attempts = 0  # Reset contador se correção foi bem-sucedida
                print("✅ Bio corrigida com sucesso!")
            else:
                correction_attempts += 1
                print(f"❌ Falha ao corrigir bio. Tentativas: {correction_attempts}/{max_correction_attempts}")
                
                # Se excedeu o número máximo de tentativas, envia alertas e desliga
                if correction_attempts >= max_correction_attempts:
                    print("🚨 Número máximo de tentativas de correção atingido. Enviando alertas...")
                    
                    # Envia alertas para o dono e todos os perms
                    all_users = [owner_id] + perms_ids
                    for user_id in all_users:
                        try:
                            await send_alert_dm(bot, user_id, current_bio, expected_bio)
                            await asyncio.sleep(0.5)  # Pequeno delay entre envios
                        except Exception as e:
                            print(f"Erro ao enviar alerta para {user_id}: {e}")
                    
                    # Desliga o bot após um pequeno delay para garantir que as DMs foram enviadas
                    await asyncio.sleep(2)
                    await shutdown_bot(bot)
        else:
            # Bio está correta, reseta o contador
            if correction_attempts > 0:
                correction_attempts = 0
                print("✅ Bio verificada e está correta!")
            
    except Exception as e:
        print(f"Erro no monitoramento de bio: {e}")

@bio_monitor_task.before_loop
async def before_bio_monitor_task():
    """Aguarda o bot estar pronto antes de iniciar a task."""
    if _bot_instance:
        await _bot_instance.wait_until_ready()

