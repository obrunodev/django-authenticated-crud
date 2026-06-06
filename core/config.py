from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    DEBUG: bool
    ALLOWED_HOSTS: list[str]
    LANGUAGE_CODE: str
    TIME_ZONE: str

settings = Settings(_env_file='.env')
