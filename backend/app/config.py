"""
Application configuration.
Loads settings from environment variables / .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+psycopg2://ambient_user:ambient_pass@localhost:5432/ambient_ai"

    # Auth
    jwt_secret_key: str = "change-this-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120

    # ASR
    sarvam_api_key: str = ""
    sarvam_api_url: str = "https://api.sarvam.ai/speech-to-text"

    # LLM
    llm_provider: str = "ollama"  # groq | ollama
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-70b-versatile"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
