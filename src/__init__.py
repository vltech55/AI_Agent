"""
King Arthur Baking AI Assistant - Core Package

This package contains the core components of the AI assistant:
- agent: LangGraph AI agent with reasoning
- scraper: Web scraper for King Arthur Baking website
- database: MongoDB Atlas integration
- embeddings: OpenAI embeddings service
- config: Configuration management
"""

from .agent import KingArthurBakingAgent
from .scraper import KingArthurScraper
from .database import MongoDBManager
from .embeddings import EmbeddingService

__all__ = [
    'KingArthurBakingAgent',
    'KingArthurScraper',
    'MongoDBManager',
    'EmbeddingService'
] 