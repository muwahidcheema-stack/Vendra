from pydantic_settings import BaseSettings, SettingsConfigDict

class Setting(BaseSettings):
    PROJECT_NAME: str = "Vendra"
    DATABASE_URL: str 
    ALGORITHM: str 
    SECRET_KEY: str 
    ACCESS_TOKEN_EXPIRE_MINIUTES: int

    model_config = SettingsConfigDict(env_file='.env', extra="ignore")

settings = Setting()