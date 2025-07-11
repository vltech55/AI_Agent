#!/usr/bin/env python3
"""
Simple script to check configuration and guide users through environment setup.
"""

import os
from src.config import settings

def check_environment():
    """Check and display environment variable status."""
    print("🍰 King Arthur Baking AI Assistant - Configuration Check")
    print("=" * 60)
    
    # Check if .env file exists
    env_file_exists = os.path.exists('.env')
    print(f"📄 .env file exists: {'✅ Yes' if env_file_exists else '❌ No'}")
    
    if not env_file_exists:
        print("\n❌ You need to create a .env file!")
        print("💡 I've created an 'env_template' file for you.")
        print("📋 Steps to set up:")
        print("   1. Copy env_template to .env: copy env_template .env")
        print("   2. Edit .env with your actual API keys")
        return False
    
    print("\n🔧 Environment Variables Status:")
    print("-" * 40)
    
    # Check OpenAI API Key
    openai_key_set = (settings.openai_api_key and 
                      settings.openai_api_key != "your_openai_api_key_here" and 
                      settings.openai_api_key != "")
    print(f"🔑 OPENAI_API_KEY: {'✅ Set' if openai_key_set else '❌ Not set'}")
    
    # Check MongoDB URI
    mongodb_uri_set = (settings.mongodb_uri and 
                       settings.mongodb_uri != "mongodb+srv://username:password@cluster.mongodb.net/" and
                       settings.mongodb_uri != "")
    print(f"🗄️  MONGODB_URI: {'✅ Set' if mongodb_uri_set else '❌ Not set'}")
    
    # Optional settings
    print(f"📊 Database Name: {settings.mongodb_db_name}")
    print(f"📁 Collection Name: {settings.mongodb_collection_name}")
    print(f"🤖 LLM Model: {settings.llm_model}")
    print(f"🧠 Embedding Model: {settings.embedding_model}")
    print(f"🌡️  Temperature: {settings.temperature}")
    
    if not openai_key_set or not mongodb_uri_set:
        print("\n" + "=" * 60)
        print("❌ SETUP REQUIRED")
        print("=" * 60)
        
        if not openai_key_set:
            print("\n🔑 OpenAI API Key Setup:")
            print("   1. Go to: https://platform.openai.com/api-keys")
            print("   2. Sign in or create an account")
            print("   3. Click 'Create new secret key'")
            print("   4. Copy the key and replace 'your_openai_api_key_here' in .env")
        
        if not mongodb_uri_set:
            print("\n🗄️  MongoDB Atlas Setup:")
            print("   1. Go to: https://cloud.mongodb.com/")
            print("   2. Sign in or create an account")
            print("   3. Create a new cluster (free tier available)")
            print("   4. Create a database user with username/password")
            print("   5. Allow your IP address in Network Access")
            print("   6. Get connection string and replace the URI in .env")
        
        print("\n📝 Your .env file should look like:")
        print("   OPENAI_API_KEY=sk-your-actual-key-here")
        print("   MONGODB_URI=mongodb+srv://youruser:yourpass@cluster.mongodb.net/")
        
        return False
    
    print("\n" + "=" * 60)
    print("✅ CONFIGURATION COMPLETE!")
    print("=" * 60)
    print("🎉 All required environment variables are set!")
    print("🚀 You can now run the full application:")
    print("   • python tests/demo.py (demo mode)")
    print("   • python tests/test_setup.py (validate setup)")
    print("   • streamlit run app.py (launch app)")
    print("   • python main.py --setup (full setup)")
    
    return True

def main():
    """Main function."""
    try:
        check_environment()
    except Exception as e:
        print(f"\n❌ Error checking configuration: {e}")
        print("💡 Make sure you have all required dependencies installed:")
        print("   pip install -r requirements.txt")

if __name__ == "__main__":
    main() 