import discord
import aiohttp
import json
import os
import base64
from dotenv import load_dotenv
from PIL import Image, ImageOps
from io import BytesIO

from config import Config
from saki import Saki

config = Config()
load_dotenv()
target_channels = config.discord_settings["target_channels"]
reaction_emoji = config.discord_settings["reaction_emoji"]

saki = Saki()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


async def load_attachments_images(attachments):
    processed_image_count = 0
    images = []
    async with aiohttp.ClientSession() as session:
        for attachment in attachments:
            if processed_image_count >= 2:
                break

            if any(
                attachment.filename.lower().endswith(ext)
                for ext in [".png", ".jpg", ".jpeg", ".gif"]
            ):
                async with session.get(attachment.url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        image = Image.open(BytesIO(data))

                        # 最も長い辺が512px未満の場合、リサイズを行わない
                        if image.width > 512 or image.height > 512:
                            max_size = (512, 512)
                            image.thumbnail(max_size, Image.LANCZOS)

                        # 透過情報がある場合、白色で背景を塗りつぶし
                        if image.mode in ["RGBA", "LA"]:
                            background = Image.new("RGB", image.size, (255, 255, 255))
                            background.paste(
                                image, mask=image.split()[3]
                            )  # 3はアルファチャネル
                            image = background
                        elif image.mode == "P":
                            image = ImageOps.colorize(
                                image.convert("L"), (0, 0, 0), (255, 255, 255)
                            )

                        # JPEG形式で画像を保存し、Base64でエンコード
                        buffered = BytesIO()
                        image.save(buffered, format="JPEG")
                        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                        images.append(img_str)
                        processed_image_count += 1
    return images


async def load_images(attachments, stickers):
    processed_image_count = 0
    images = []
    async with aiohttp.ClientSession() as session:
        # 添付ファイルの処理
        for attachment in attachments:
            if processed_image_count >= 2:
                break
            if any(
                attachment.filename.lower().endswith(ext)
                for ext in [".png", ".jpg", ".jpeg", ".gif"]
            ):
                image_data = await fetch_and_process_image(session, attachment.url)
                if image_data:
                    images.append(image_data)
                    processed_image_count += 1

        # ステッカーの処理
        for sticker in stickers:
            if processed_image_count >= 2:
                break
            image_data = await fetch_and_process_image(session, sticker.url)
            if image_data:
                images.append(image_data)
                processed_image_count += 1

    return images


async def fetch_and_process_image(session, url):
    async with session.get(url) as resp:
        if resp.status == 200:
            data = await resp.read()
            image = Image.open(BytesIO(data))

            if image.width > 512 or image.height > 512:
                max_size = (512, 512)
                image.thumbnail(max_size, Image.LANCZOS)

            if image.mode in ["RGBA", "LA"]:
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            elif image.mode == "P":
                image = ImageOps.colorize(
                    image.convert("L"), (0, 0, 0), (255, 255, 255)
                )

            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return img_str
    return None


@client.event
async def on_ready():
    print(f"初期化かんりょー♡ いつでもいけるよ: {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return

    # チャンネル名による制御
    channel_name = message.channel.name
    if target_channels is not None and len(target_channels) > 0:
        # 対象のチャンネル名をいずれも含まない場合return
        if all(name not in channel_name for name in target_channels):
            return

    if client.user.mentioned_in(message):
        # メッセージにリアクションを付ける
        await message.add_reaction(reaction_emoji or "✔")
        # 入力中...表示
        async with message.channel.typing():
            # ユーザーID, 名前
            user_id = message.author.id
            user_name = message.author.display_name
            # メッセージのコンテンツからメンションを削除します。
            # clean_contentはメンションをユーザー名に置換しますが、ここでは完全に取り除きます。
            content_without_mentions = message.content
            for mention in message.mentions:
                content_without_mentions = content_without_mentions.replace(
                    mention.mention, ""
                ).strip()

            # 画像が添付された場合の前処理
            attachments = message.attachments
            base64_images = []
            if len(attachments) > 0:
                base64_images = await load_attachments_images(attachments)

            response = await saki.chat(
                user_name, content_without_mentions, base64_images
            )
        # サーバーからの応答としてメッセージを送信する
        await message.reply(response)


TOKEN = os.getenv("SAKI_BOT_TOKEN")
client.run(TOKEN)
