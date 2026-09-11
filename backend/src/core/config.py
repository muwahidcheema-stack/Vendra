from pydantic_settings import BaseSettings, SettingsConfigDict

class Setting(BaseSettings):
    PROJECT_NAME: str = "Vendra"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:301060@localhost:5432/vendra_db"
    ALGORITHM: str = "HS256"
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ACCESS_TOKEN_EXPIRE_MINIUTES: int =  60*24

    model_config = SettingsConfigDict(env_file='.env', extra="ignore")

settings = Setting()