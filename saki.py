import yaml
import os
import aiohttp
import json
from datetime import datetime
import pytz
from dotenv import load_dotenv
from anthropic import APIConnectionError, RateLimitError, APIStatusError

from config import Config
from anthropic_client_manager import ClientManager
from moderation import Moderator

import asyncio

config = Config()

load_dotenv()
clientManager = ClientManager()
client = clientManager.get_client()

moderator = Moderator()


class Saki:
    def __init__(self):
        self.model = config.bot_settings["model"]
        self.role = config.bot_settings["role"]
        self.max_tokens = config.bot_settings["max_tokens"]
        self.temperature = config.bot_settings["temperature"]
        self.message_templates = config.bot_settings["message_templates"]

    async def isFlagged(self, msg):
        return await moderator.validate_message(msg) is False

    async def create(self, messages):
        try:
            # チャット呼び出し
            response_message = await client.messages.create(
                model=self.model,
                system=self.role,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=messages,
            )
            print("*" * 20)
            print(messages)
            print(response_message)

            response = response_message.content[0].text
            return response
        except APIConnectionError as e:
            print("The server could not be reached")
            print(e.__cause__)  # an underlying Exception, likely raised within httpx.
            return self.message_templates["error"]
        except RateLimitError as e:
            print("A 429 status code was received; we should back off a bit.")
            return self.message_templates["error"]
        except APIStatusError as e:
            print("Another non-200-range status code was received")
            print(e.status_code)
            print(e.response)
            return self.message_templates["error"]

    async def chat(self, user_name, user_message, base64_images):
        # 空の場合
        if not user_message and len(base64_images) == 0:
            return self.message_templates["no_prompt"]

        # prompt構築
        prompt = f"ユーザー名:{user_name}\n{user_message}"

        # モデレーション
        if await self.isFlagged(prompt):
            prompt = f"ユーザー名:{user_name}\n<<検閲されたメッセージ>>"

        # messages構築
        user_content = [
            {"type": "text", "text": prompt},
        ]
        if len(base64_images) > 0:
            for base64_image in base64_images:
                user_content.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_image,
                        },
                    }
                )
        messages = [
            {"role": "user", "content": user_content},
        ]
        # チャット呼び出し
        response = await self.create(messages)
        return response


# 検証用
# async def main() -> None:
#     saki = Saki()
#     await saki.chat("くよう", "こんにちは", [])
#     await saki.chat("終わった人", "nigga", [])


# asyncio.run(main())
