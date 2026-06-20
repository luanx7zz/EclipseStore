from functions.database import database as db
from disnake.ext import commands
import disnake
import requests

def obter_info():
        data = db.obter("config.json")
        headers = {"authorization": data['botToken'], "content-type": "application/json"}
        url = f"{data['apiURL']}/api/bot/{data['botID']}/info"

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        
        print(f"[ObterInfo] Erro na requisição. Status: {response.status_code}")
        exit(1)

def salvar_info(info: dict):
    config_db = db.obter("config.json")
    config_db["bot"] = {k: info[k] for k in ("token", "owner", "id", "perms", "server")}
    if "version" in info:
        config_db["version"] = info["version"]
    db.salvar("config.json", config_db)

def create_bot() -> tuple[commands.Bot, str, str]:
    config_db = db.obter("config.json")
    if config_db["saveConfig"] == True:
        info = obter_info()
        salvar_info(info)
    else:
        info = config_db["bot"]

    intents = disnake.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.guilds = True

    bot = commands.Bot(
        command_prefix=commands.when_mentioned,
        intents=intents,
        help_command=None,
        reload=True
    )
    return bot, info["token"], info["id"]