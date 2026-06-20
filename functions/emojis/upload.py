import os
import base64
import aiohttp
import asyncio


async def upload_emoji_async(session, name, image_path, app_id, bot_token):
    ext = os.path.splitext(image_path)[1].lower()

    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    tipo = "gif" if ext == ".gif" else "png"
    base64_image = f"data:image/{tipo};base64,{base64.b64encode(image_data).decode()}"

    url = f"https://discord.com/api/v10/applications/{app_id}/emojis"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": name,
        "image": base64_image
    }

    async with session.post(url, headers=headers, json=payload) as response:
        if response.status == 201:
            data = await response.json()
            emoji_id = data["id"]
            print(f"[EmojiUpload] Emoji '{name}' criado com sucesso! ID: {emoji_id}")
            return emoji_id

        elif response.status == 429:
            print(f"[EmojiUpload] Rate limit detectado ao criar '{name}'. Aguardando...")
            await asyncio.sleep(10)
            raise Exception("Rate limit 429")

        else:
            text = await response.text()
            print(f"[EmojiUpload] Erro ao criar '{name}': {response.status} - {text}")
            raise Exception(f"Erro ao criar emoji {name}: {response.status} - {text}")


async def upload_emojis_batch(emojis_data, app_id, bot_token):
    """
    Upload múltiplos emojis de forma segura (anti rate limit)
    emojis_data: lista de tuplas (name, image_path)
    """

    async with aiohttp.ClientSession() as session:
        results = []

        for name, image_path in emojis_data:
            try:
                result = await upload_emoji_async(
                    session,
                    name,
                    image_path,
                    app_id,
                    bot_token
                )

                results.append(result)

                # 🔥 Delay obrigatório
                await asyncio.sleep(6)

            except Exception as e:
                print(f"[EmojiUpload] Erro em '{name}': {e}")
                await asyncio.sleep(12)

        return results


def upload_emoji(name, image_path, app_id, bot_token):
    """Versão síncrona para compatibilidade"""
    return asyncio.run(upload_emojis_batch([(name, image_path)], app_id, bot_token))