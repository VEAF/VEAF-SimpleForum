from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATA_PATH: Path = Path("/home/debian/veaf/community/var/data")
    IMAGES_PATH: Path = Path("/home/debian/veaf/community/var/data/images")
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
