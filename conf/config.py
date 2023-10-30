from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    sqlalchemy_database_url: str = 'postgresql+psycopg2://postgres:5671234@localhost:5432/postgres'
    secret_key: str = 'secret_key'
    algorithm: str ='HS256'
    mail_username: str = 'test@mail.com' 
    mail_password: str = 'mailpassword'
    mail_from: str = 'test@mail.com'
    mail_port: int = 465
    mail_server: str = 'smtp.meta.ua'
    redis_host: str = 'localhost'
    redis_port: int = 6379
    cloudinary_name: str = 'cloudinary_name'
    cloudinary_api_key: str = 'cloudinary_api_key'
    cloudinary_api_secret: str = 'cloudinary_api_secret'

    model_config = ConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra='ignore'
    )


settings = Settings()
