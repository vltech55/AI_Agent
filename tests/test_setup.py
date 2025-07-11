#!/usr/bin/env python3
"""
Test script to validate the King Arthur Baking AI Assistant setup.
"""

import sys
import os
import importlib
import logging
from typing import Dict, List, Any

# Add the parent directory to the path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported."""
    logger.info("Testing imports...")
    
    required_modules = [
        'streamlit',
        'langchain',
        'langgraph',
        'langchain_openai',
        'langchain_mongodb',
        'pymongo',
        'requests',
        'beautifulsoup4',
        'selenium',
        'webdriver_manager',
        'python-dotenv',
        'pydantic',
        'openai',
        'plotly',
        'pandas',
        'numpy'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            # Handle special cases
            if module == 'beautifulsoup4':
                importlib.import_module('bs4')
            elif module == 'python-dotenv':
                importlib.import_module('dotenv')
            elif module == 'webdriver_manager':
                importlib.import_module('webdriver_manager')
            else:
                importlib.import_module(module)
            
            logger.info(f"✅ {module}")
        except ImportError as e:
            logger.error(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        logger.error(f"Failed to import: {', '.join(failed_imports)}")
        return False
    
    logger.info("All required modules imported successfully!")
    return True

def test_environment():
    """Test environment variables."""
    logger.info("Testing environment variables...")
    
    required_vars = ['OPENAI_API_KEY', 'MONGODB_URI']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            logger.warning(f"⚠️  {var} not set")
        else:
            logger.info(f"✅ {var} is set")
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Some features may not work without these variables")
        return False
    
    return True

def test_custom_modules():
    """Test our custom modules."""
    logger.info("Testing custom modules...")
    
    modules = ['config', 'src.scraper', 'src.database', 'src.embeddings', 'src.agent']
    
    for module in modules:
        try:
            importlib.import_module(module)
            logger.info(f"✅ {module}")
        except ImportError as e:
            logger.error(f"❌ {module}: {e}")
            return False
    
    logger.info("All custom modules imported successfully!")
    return True

def test_config():
    """Test configuration settings."""
    logger.info("Testing configuration...")
    
    try:
        from config import settings
        
        # Test required settings
        required_settings = [
            'llm_model',
            'embedding_model',
            'temperature',
            'max_tokens',
            'chunk_size',
            'chunk_overlap'
        ]
        
        for setting in required_settings:
            if hasattr(settings, setting):
                value = getattr(settings, setting)
                logger.info(f"✅ {setting}: {value}")
            else:
                logger.error(f"❌ Missing setting: {setting}")
                return False
        
        logger.info("Configuration test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Configuration test failed: {e}")
        return False

def test_openai_connection():
    """Test OpenAI API connection."""
    logger.info("Testing OpenAI connection...")
    
    try:
        import openai
        from config import settings
        
        if not hasattr(settings, 'openai_api_key') or not settings.openai_api_key:
            logger.warning("⚠️  OpenAI API key not configured")
            return False
        
        # Test with a simple request
        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # Test embedding
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="test embedding"
        )
        
        if response.data and len(response.data[0].embedding) > 0:
            logger.info("✅ OpenAI embedding API working")
        else:
            logger.error("❌ OpenAI embedding API failed")
            return False
        
        # Test chat completion
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        
        if response.choices and response.choices[0].message.content:
            logger.info("✅ OpenAI chat API working")
        else:
            logger.error("❌ OpenAI chat API failed")
            return False
        
        logger.info("OpenAI connection test passed!")
        return True
        
    except Exception as e:
        logger.error(f"OpenAI connection test failed: {e}")
        return False

def test_mongodb_connection():
    """Test MongoDB connection."""
    logger.info("Testing MongoDB connection...")
    
    try:
        from pymongo import MongoClient
        from config import settings
        
        if not hasattr(settings, 'mongodb_uri') or not settings.mongodb_uri:
            logger.warning("⚠️  MongoDB URI not configured")
            return False
        
        client = MongoClient(settings.mongodb_uri)
        
        # Test connection
        client.admin.command('ping')
        logger.info("✅ MongoDB connection successful")
        
        # Test database access
        db = client[settings.mongodb_db_name]
        collection = db[settings.mongodb_collection_name]
        
        # Test basic operations
        test_doc = {"test": "document", "timestamp": "2024-01-01"}
        result = collection.insert_one(test_doc)
        
        if result.inserted_id:
            logger.info("✅ MongoDB write test successful")
            # Clean up
            collection.delete_one({"_id": result.inserted_id})
        else:
            logger.error("❌ MongoDB write test failed")
            return False
        
        client.close()
        logger.info("MongoDB connection test passed!")
        return True
        
    except Exception as e:
        logger.error(f"MongoDB connection test failed: {e}")
        return False

def test_scraper():
    """Test web scraper functionality."""
    logger.info("Testing web scraper...")
    
    try:
        from scraper import KingArthurScraper
        
        scraper = KingArthurScraper()
        
        # Test basic HTTP request
        from config import MIXES_URL
        soup = scraper.get_page(MIXES_URL)
        
        if soup:
            logger.info("✅ Web scraper can fetch pages")
        else:
            logger.error("❌ Web scraper failed to fetch pages")
            return False
        
        logger.info("Web scraper test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Web scraper test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("🍰 King Arthur Baking AI Assistant - Setup Test")
    logger.info("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Environment", test_environment),
        ("Custom Modules", test_custom_modules),
        ("Configuration", test_config),
        ("OpenAI Connection", test_openai_connection),
        ("MongoDB Connection", test_mongodb_connection),
        ("Web Scraper", test_scraper)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Your setup is ready!")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 