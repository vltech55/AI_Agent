#!/usr/bin/env python3
"""
Demo script for King Arthur Baking AI Assistant.
This script demonstrates key features without requiring full setup.
"""

import json
import logging
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockKingArthurDemo:
    """Mock demo class to showcase functionality."""
    
    def __init__(self):
        self.sample_products = [
            {
                "name": "Gluten-Free Chocolate Cake Mix",
                "price": "$8.95",
                "description": "Rich, moist chocolate cake that's completely gluten-free. Made with our special blend of gluten-free flours.",
                "ingredients": "Rice flour, sugar, cocoa powder, baking soda, salt, xanthan gum",
                "instructions": "Mix with 3 eggs, 1/3 cup oil, and 1 cup water. Bake at 350°F for 25-30 minutes.",
                "features": ["Gluten-Free", "Easy to Make", "Rich Chocolate Flavor"],
                "category": "Cake Mixes",
                "url": "https://shop.kingarthurbaking.com/items/gluten-free-chocolate-cake-mix"
            },
            {
                "name": "Classic Pancake Mix",
                "price": "$6.95",
                "description": "Fluffy, tender pancakes every time. Just add water and you're ready to go!",
                "ingredients": "Wheat flour, sugar, baking powder, salt, dried buttermilk",
                "instructions": "Mix 1 cup mix with 3/4 cup water. Cook on griddle until bubbles form.",
                "features": ["Quick & Easy", "Fluffy Texture", "Family Favorite"],
                "category": "Pancake Mixes",
                "url": "https://shop.kingarthurbaking.com/items/classic-pancake-mix"
            },
            {
                "name": "Artisan Bread Mix",
                "price": "$9.95",
                "description": "Create bakery-quality artisan bread at home. No kneading required!",
                "ingredients": "Bread flour, whole wheat flour, salt, yeast, dough enhancer",
                "instructions": "Mix with 1 1/4 cups warm water. Let rise 1 hour, shape, rise again, then bake.",
                "features": ["No Kneading", "Artisan Quality", "Crispy Crust"],
                "category": "Bread Mixes",
                "url": "https://shop.kingarthurbaking.com/items/artisan-bread-mix"
            }
        ]
    
    def search_products(self, query: str) -> List[Dict]:
        """Mock search functionality."""
        query_lower = query.lower()
        results = []
        
        for product in self.sample_products:
            # Simple keyword matching
            if (query_lower in product['name'].lower() or 
                query_lower in product['description'].lower() or
                any(query_lower in feature.lower() for feature in product['features'])):
                results.append(product)
        
        return results
    
    def get_recommendations(self, preferences: List[str]) -> List[Dict]:
        """Mock recommendation functionality."""
        # Simple recommendation based on preferences
        recommendations = []
        
        for product in self.sample_products:
            score = 0
            for pref in preferences:
                if pref.lower() in product['description'].lower():
                    score += 1
                if any(pref.lower() in feature.lower() for feature in product['features']):
                    score += 1
            
            if score > 0:
                recommendations.append((score, product))
        
        # Sort by score and return products
        recommendations.sort(key=lambda x: x[0], reverse=True)
        return [product for _, product in recommendations]
    
    def analyze_query(self, query: str) -> Dict:
        """Mock query analysis."""
        query_lower = query.lower()
        
        # Determine intent
        if any(word in query_lower for word in ['recommend', 'suggest', 'best']):
            intent = 'recommendations'
        elif any(word in query_lower for word in ['compare', 'vs', 'versus', 'difference']):
            intent = 'compare'
        else:
            intent = 'search'
        
        # Extract keywords
        keywords = []
        product_keywords = ['chocolate', 'pancake', 'bread', 'cake', 'gluten-free', 'easy']
        for keyword in product_keywords:
            if keyword in query_lower:
                keywords.append(keyword)
        
        return {
            'intent': intent,
            'keywords': keywords,
            'query': query
        }
    
    def generate_response(self, query: str, products: List[Dict]) -> str:
        """Generate a response based on query and products."""
        analysis = self.analyze_query(query)
        
        if not products:
            return "I couldn't find any mixes that match your request. Could you try a different search term?"
        
        response = f"I found {len(products)} great options for you:\n\n"
        
        for i, product in enumerate(products, 1):
            response += f"{i}. **{product['name']}** - {product['price']}\n"
            response += f"   {product['description']}\n"
            response += f"   Features: {', '.join(product['features'])}\n\n"
        
        if analysis['intent'] == 'recommendations':
            response += "These recommendations are based on your preferences. Each one offers something special for your baking needs!"
        elif analysis['intent'] == 'compare':
            response += "Here's a comparison of these options to help you choose the best one for your needs."
        
        return response
    
    def chat(self, query: str) -> Dict:
        """Main chat interface."""
        analysis = self.analyze_query(query)
        
        if analysis['intent'] == 'recommendations':
            products = self.get_recommendations(analysis['keywords'])
        else:
            products = self.search_products(query)
        
        response = self.generate_response(query, products)
        
        return {
            'response': response,
            'products': products,
            'analysis': analysis,
            'intent': analysis['intent']
        }

def demo_chat():
    """Demonstrate the chat functionality."""
    print("🍰 King Arthur Baking AI Assistant - Demo Mode")
    print("=" * 60)
    print("This is a demo showing how the AI assistant works.")
    print("In the full version, this would use real data and OpenAI.")
    print("=" * 60)
    
    demo = MockKingArthurDemo()
    
    # Demo queries
    demo_queries = [
        "I'm looking for a chocolate cake mix",
        "Can you recommend something easy to make?",
        "What do you have for gluten-free options?",
        "Compare your pancake and bread mixes"
    ]
    
    for query in demo_queries:
        print(f"\n👤 User: {query}")
        print("🤖 AI Assistant: ", end="")
        
        result = demo.chat(query)
        print(result['response'])
        
        print("-" * 60)

def demo_features():
    """Demonstrate key features."""
    print("\n🚀 Key Features of the AI Agent:")
    print("=" * 60)
    
    features = [
        "🕷️  **Web Scraping**: Automatically scrapes King Arthur Baking website",
        "🧠 **AI Embeddings**: Uses OpenAI embeddings for semantic search",
        "🤖 **LangGraph Agent**: Advanced multi-step reasoning and tool use",
        "🗄️  **MongoDB Atlas**: Vector database for efficient product storage",
        "🔍 **Hybrid Search**: Combines semantic and text search",
        "💬 **Natural Language**: Understands complex queries and context",
        "📊 **Analytics**: Provides insights and product comparisons",
        "🎨 **Beautiful UI**: Modern Streamlit interface with visualizations"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print("\n🛠️  Technology Stack:")
    print("=" * 60)
    
    tech_stack = [
        "Frontend: Streamlit with custom CSS",
        "AI: OpenAI GPT-4o + text-embedding-3-small",
        "Framework: LangGraph + LangChain",
        "Database: MongoDB Atlas with vector search",
        "Scraping: BeautifulSoup4 + Requests",
        "Visualization: Plotly for interactive charts",
        "Deployment: Hugging Face Spaces ready"
    ]
    
    for tech in tech_stack:
        print(f"  • {tech}")

def demo_workflow():
    """Demonstrate the agent workflow."""
    print("\n🔄 Agent Workflow:")
    print("=" * 60)
    
    workflow_steps = [
        "1. **Query Analysis**: Analyze user input to determine intent",
        "2. **Route Decision**: Choose search, recommendations, or comparison",
        "3. **Data Retrieval**: Use semantic search or MongoDB queries",
        "4. **Reasoning**: Analyze results and provide insights",
        "5. **Response Generation**: Create helpful, detailed responses"
    ]
    
    for step in workflow_steps:
        print(f"  {step}")
    
    print("\n📈 Search Capabilities:")
    print("=" * 60)
    
    search_types = [
        "🎯 **Semantic Search**: Understands context and meaning",
        "📝 **Text Search**: Traditional keyword matching",
        "🔀 **Hybrid Search**: Combines both approaches",
        "🎯 **Product Recommendations**: Personalized suggestions",
        "⚖️  **Product Comparison**: Side-by-side analysis"
    ]
    
    for search_type in search_types:
        print(f"  {search_type}")

def main():
    """Main demo function."""
    print("🍰 King Arthur Baking AI Assistant - Complete Demo")
    print("=" * 80)
    
    demo_features()
    demo_workflow()
    demo_chat()
    
    print("\n🎉 Demo Complete!")
    print("=" * 80)
    print("To run the full application:")
    print("1. Set up your .env file with API keys")
    print("2. Run: python main.py --setup")
    print("3. Launch: streamlit run app.py")
    print("4. Or run: python main.py --chat for command-line interface")
    print("\nFor deployment to Hugging Face Spaces:")
    print("1. Create a new Space with Streamlit SDK")
    print("2. Upload all files to the Space")
    print("3. Set environment variables in Space settings")
    print("4. The app will automatically deploy!")

if __name__ == "__main__":
    main() 