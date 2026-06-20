from functions.emoji import emoji
from functions.database import database as db
import requests

def change_bio():
    database = db.obter("config.json")
    token = database["bot"]["token"]
    id = database["bot"]["id"]
    api_url = database["apiURL"]

    description = (
        "🌑 Eclipse Store — Compre com segurança, receba com rapidez.\n"
        "Atendimento de qualidade, produtos exclusivos e entrega automática."
    )
    
    url = f"https://discord.com/api/v9/applications/{id}"
    headers = {
        "authorization": f"Bot {token}",
        "content-type": "application/json",
    }
    payload = {
        "description": description
    }

    requests.patch(url, headers=headers, json=payload)
    return