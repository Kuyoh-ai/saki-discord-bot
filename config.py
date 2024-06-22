import yaml
from pathlib import Path


class Config:
    _instance = None

    def __new__(cls, file_path="./config.yaml"):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.load_config(file_path)
        return cls._instance

    def load_config(self, file_path):
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"No config file found at {file_path}")

        with open(path, "r", encoding="utf-8") as file:
            config_data = yaml.safe_load(file)
            for key, value in config_data.items():
                setattr(self, key, value)
        print(f"Config file:{file_path} loaded.")
