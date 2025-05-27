from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB2_HOST: str
    DB2_DB: str
    DB2_PORT: str
    DB2_USER: str
    DB2_PASS: str
