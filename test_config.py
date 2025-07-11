#!/usr/bin/env python3
"""
Simple script to demonstrate config import and usage.
"""

# Different ways to import config
print("🍰 King Arthur Baking AI Assistant - Config Import Demo")
print("=" * 60)

# Method 1: Import settings object
print("📥 Method 1: Import settings object")
from src.config import settings
print(f"✅ LLM Model: {settings.llm_model}")
print(f"✅ Embedding Model: {settings.embedding_model}")
print(f"✅ Temperature: {settings.temperature}")
print(f"✅ Database Name: {settings.mongodb_db_name}")

# Method 2: Import URLs
print("\n📥 Method 2: Import URLs")
from src.config import BASE_URL, MIXES_URL
print(f"✅ Base URL: {BASE_URL}")
print(f"✅ Mixes URL: {MIXES_URL}")

# Method 3: Check API keys are loaded (without showing them)
print("\n🔑 Method 3: API Keys Status")
openai_loaded = bool(settings.openai_api_key and len(settings.openai_api_key) > 10)
mongodb_loaded = bool(settings.mongodb_uri and "mongodb" in settings.mongodb_uri)
print(f"✅ OpenAI API Key: {'✅ Loaded' if openai_loaded else '❌ Missing'}")
print(f"✅ MongoDB URI: {'✅ Loaded' if mongodb_loaded else '❌ Missing'}")

print("\n🎉 Config import working perfectly!")
print("🚀 You can now use these in your applications:")
print("   from src.config import settings")
print("   from src.config import BASE_URL, MIXES_URL") 