import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OpenAI API Configuration
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    
    # MongoDB Atlas Configuration
    mongodb_uri: str = Field(default="", env="MONGODB_URI")
    mongodb_db_name: str = Field("king_arthur_baking_db", env="MONGODB_DB_NAME")
    mongodb_collection_name: str = Field("mixes", env="MONGODB_COLLECTION_NAME")
    
    # Scraping Configuration
    scraping_delay: int = Field(1, env="SCRAPING_DELAY")
    max_retries: int = Field(3, env="MAX_RETRIES")
    
    # Agent Configuration
    temperature: float = Field(0.1, env="TEMPERATURE")
    max_tokens: int = Field(1000, env="MAX_TOKENS")
    chunk_size: int = Field(1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(200, env="CHUNK_OVERLAP")
    
    # Models
    llm_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"

    # King Arthur Baking URLs
    base_url: str = "https://shop.kingarthurbaking.com"
    mixes_url: str = f"{base_url}/mixes"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()