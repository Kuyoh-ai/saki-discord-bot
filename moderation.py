from config import Config
from anthropic_client_manager import ClientManager

import asyncio

config = Config()
clientManager = ClientManager()
client = clientManager.get_client()


class Moderator:
    def __init__(self) -> None:
        self.model = config.moderation_settings["model"]
        self.role = config.moderation_settings["role"]
        self.max_tokens = config.moderation_settings["max_tokens"]
        self.temperature = config.moderation_settings["temperature"]

    async def validate_message(self, msg):
        if not msg:
            return True

        message = await client.messages.create(
            model=self.model,
            system=self.role,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": f"{msg}"}],
        )
        response = message.content[0].text
        validation_result = not response == "Y"
        print(f"[{response}]: {msg}")
        return validation_result


# 検証用
# async def main() -> None:
#     mod = Moderator()
#     await mod.validate_message("こんにちは")
#     await mod.validate_message("nigga")


# asyncio.run(main())
