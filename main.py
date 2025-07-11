#!/usr/bin/env python3
"""
Main script for King Arthur Baking AI Assistant.
This script demonstrates the complete workflow from scraping to AI interaction.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any

# Add the parent directory to the path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
from src.scraper import KingArthurScraper
from src.database import MongoDBManager
from src.embeddings import EmbeddingService
from src.agent import KingArthurBakingAgent
from src.config import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set."""
    # Check if API keys are properly configured
    openai_key_set = (settings.openai_api_key and 
                      settings.openai_api_key != "your_openai_api_key_here" and 
                      settings.openai_api_key != "")
    
    mongodb_uri_set = (settings.mongodb_uri and 
                       settings.mongodb_uri != "mongodb+srv://username:password@cluster.mongodb.net/" and
                       settings.mongodb_uri != "")
    
    missing_vars = []
    if not openai_key_set:
        missing_vars.append("OPENAI_API_KEY")
    if not mongodb_uri_set:
        missing_vars.append("MONGODB_URI")
    
    if missing_vars:
        logger.error(f"Missing or invalid environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file")
        logger.info("💡 Run 'python check_config.py' for detailed setup instructions")
        return False
    
    return True

def scrape_data():
    """Scrape data from King Arthur Baking website."""
    logger.info("Starting data scraping...")
    
    try:
        scraper = KingArthurScraper()
        products = scraper.scrape_products()
        
        if products:
            new_count = scraper.save_to_json(products)
            logger.info(f"Successfully scraped {len(products)} products")
            logger.info(f"Added {new_count} new products to JSON file")
            return True
        else:
            logger.warning("No products were scraped")
            return False
            
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        return False

def setup_database():
    """Set up database and load data."""
    logger.info("Setting up database...")
    
    try:
        db_manager = MongoDBManager()
        
        # Load data from JSON file
        inserted_count = db_manager.load_from_json()
        logger.info(f"Inserted {inserted_count} products into database")
        
        # Get database stats
        stats = db_manager.get_stats()
        logger.info(f"Database stats: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return False

def generate_embeddings():
    """Generate embeddings for all products."""
    logger.info("Generating embeddings...")
    
    try:
        embedding_service = EmbeddingService()
        updated_count = embedding_service.update_embeddings()
        logger.info(f"Updated embeddings for {updated_count} products")
        return True
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return False

def test_agent():
    """Test the AI agent with sample queries."""
    logger.info("Testing AI agent...")
    
    try:
        agent = KingArthurBakingAgent()
        
        # Test queries
        test_queries = [
            "I'm looking for a chocolate cake mix",
            "Can you recommend some easy baking mixes for beginners?",
            "Compare different pancake mixes",
            "What ingredients are in your bread mixes?"
        ]
        
        for query in test_queries:
            logger.info(f"Testing query: {query}")
            result = agent.chat(query)
            
            logger.info(f"Response: {result['response'][:100]}...")
            logger.info(f"Found {len(result['products'])} products")
            logger.info(f"Tools used: {result['tool_calls']}")
            print("-" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing agent: {e}")
        return False

def interactive_chat():
    """Start interactive chat session."""
    logger.info("Starting interactive chat...")
    
    try:
        agent = KingArthurBakingAgent()
        
        print("\n" + "="*80)
        print("🍰 King Arthur Baking AI Assistant")
        print("Type 'quit' to exit, 'help' for commands")
        print("="*80)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("Thanks for using King Arthur Baking AI Assistant! Happy baking! 🍰")
                    break
                
                if user_input.lower() == 'help':
                    print("""
Available commands:
- Ask about baking mixes: "I need a chocolate cake mix"
- Get recommendations: "Recommend easy mixes for beginners"
- Compare products: "Compare pancake mixes"
- Ask about ingredients: "What's in the bread mixes?"
- quit/exit: Exit the chat
                    """)
                    continue
                
                if not user_input:
                    continue
                
                print("\nAI Assistant: ", end="")
                result = agent.chat(user_input)
                print(result['response'])
                
                # Show products if found
                if result['products']:
                    print(f"\n📦 Found {len(result['products'])} relevant products:")
                    for i, product in enumerate(result['products'][:3], 1):
                        print(f"{i}. {product.get('name', 'Unknown')} - {product.get('price', 'N/A')}")
                
            except KeyboardInterrupt:
                print("\n\nThanks for using King Arthur Baking AI Assistant! 🍰")
                break
            except Exception as e:
                print(f"\nError: {e}")
                continue
        
        return True
        
    except Exception as e:
        logger.error(f"Error in interactive chat: {e}")
        return False

def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description="King Arthur Baking AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --setup          # Full setup (scrape, database, embeddings)
  python main.py --scrape         # Scrape data only
  python main.py --database       # Setup database only
  python main.py --embeddings     # Generate embeddings only
  python main.py --test           # Test the agent
  python main.py --chat           # Interactive chat
  python main.py --streamlit      # Launch Streamlit app
        """
    )
    
    parser.add_argument('--setup', action='store_true',
                       help='Run complete setup (scrape, database, embeddings)')
    parser.add_argument('--scrape', action='store_true',
                       help='Scrape data from website')
    parser.add_argument('--database', action='store_true',
                       help='Setup database and load data')
    parser.add_argument('--embeddings', action='store_true',
                       help='Generate embeddings for products')
    parser.add_argument('--test', action='store_true',
                       help='Test the AI agent')
    parser.add_argument('--chat', action='store_true',
                       help='Start interactive chat')
    parser.add_argument('--streamlit', action='store_true',
                       help='Launch Streamlit app')
    
    args = parser.parse_args()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    success = True
    
    try:
        if args.setup:
            logger.info("Running complete setup...")
            success &= scrape_data()
            success &= setup_database()
            success &= generate_embeddings()
            if success:
                logger.info("✅ Complete setup successful!")
            else:
                logger.error("❌ Setup failed")
        
        if args.scrape:
            success &= scrape_data()
        
        if args.database:
            success &= setup_database()
        
        if args.embeddings:
            success &= generate_embeddings()
        
        if args.test:
            success &= test_agent()
        
        if args.chat:
            success &= interactive_chat()
        
        if args.streamlit:
            logger.info("Launching Streamlit app...")
            os.system("streamlit run app.py")
    
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 