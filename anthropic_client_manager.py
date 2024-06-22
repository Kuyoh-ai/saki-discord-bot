import os
from dotenv import load_dotenv
from anthropic import AsyncAnthropic


class ClientManager:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClientManager, cls).__new__(cls)
        return cls._instance

    def get_client(self):
        if self._client is None:
            load_dotenv()
            ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
            self._client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        return self._client
