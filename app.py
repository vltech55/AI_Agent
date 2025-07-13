import streamlit as st
import json
from datetime import datetime
import logging
from typing import Dict, List
import sys
import os

# Add the parent directory to the path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our custom modules
from src.agent import KingArthurBakingAgent
from src.database import MongoDBManager
# Removed AtlasVectorSearchService - using database search methods directly
from src.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="King Arthur Baking AI Assistant",
    page_icon="🍰",
    layout="wide"
)

# Custom CSS for clean UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        color: white;
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #4ECDC4;
    }
    .user-message {
        background-color: #E8F4FD;
        border-left-color: #2E86AB;
    }
    .assistant-message {
        background-color: #F0F8F0;
        border-left-color: #4ECDC4;
    }
    .product-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        border: 1px solid #E0E0E0;
    }
    .product-card h4 {
        color: #2E86AB;
        margin-top: 0;
    }
    .product-card .price {
        color: #FF6B6B;
        font-weight: bold;
        font-size: 1.1rem;
    }
    .stats-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #4ECDC4;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = None
    # Removed vector_service - using database search methods directly

def initialize_components():
    """Initialize all components."""
    try:
        if st.session_state.agent is None:
            with st.spinner("Initializing AI Agent..."):
                st.session_state.agent = KingArthurBakingAgent()
        
        if st.session_state.db_manager is None:
            with st.spinner("Connecting to Database..."):
                st.session_state.db_manager = MongoDBManager()
        
        # Vector search methods are now part of db_manager
        
        return True
    except Exception as e:
        st.error(f"❌ Error initializing components: {str(e)}")
        logger.error(f"Initialization error: {e}")
        return False

def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>🍰 King Arthur Baking AI Assistant</h1>
        <p>Ask me about baking mixes, recipes, and get personalized recommendations!</p>
    </div>
    """, unsafe_allow_html=True)

def render_product_cards(products: List[Dict]):
    """Render product cards in a clean format."""
    if not products:
        return
    
    st.markdown("### 🛍️ Recommended Products")
    
    # Limit to 6 products for better display
    products_to_show = products[:6]
    
    # Display products in columns
    cols = st.columns(min(len(products_to_show), 2))
    
    for i, product in enumerate(products_to_show):
        col = cols[i % 2]
        
        with col:
            st.markdown(f"""
            <div class="product-card">
                <h4>{product.get('name', 'Unknown Product')}</h4>
                <p class="price">{product.get('price', 'Price not available')}</p>
                <p><strong>Description:</strong> {(product.get('description', 'No description')[:120] + '...' if len(product.get('description', '')) > 120 else product.get('description', 'No description'))}</p>
                <p><strong>Ingredients:</strong> {(product.get('ingredients', 'Not available')[:100] + '...' if len(product.get('ingredients', '')) > 100 else product.get('ingredients', 'Not available'))}</p>
                {f'<p><a href="{product.get("url", "#")}" target="_blank">🔗 View Product</a></p>' if product.get('url') else ''}
            </div>
            """, unsafe_allow_html=True)

def render_database_stats():
    """Render simple database statistics."""
    if st.session_state.db_manager:
        try:
            stats = st.session_state.db_manager.get_stats()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="stats-box">
                    <h4>📊 Database Stats</h4>
                    <p><strong>Total Products:</strong> {stats.get('total_products', 0)}</p>
                    <p><strong>Products with Embeddings:</strong> {stats.get('products_with_embeddings', 0)}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("🔄 Update Embeddings"):
                    with st.spinner("Updating embeddings..."):
                        try:
                            updated_count = st.session_state.db_manager.update_embeddings()
                            st.success(f"✅ Updated embeddings for {updated_count} products")
                        except Exception as e:
                            st.error(f"❌ Error updating embeddings: {str(e)}")
                            
        except Exception as e:
            st.error(f"❌ Error getting database stats: {str(e)}")

def render_chat_interface():
    """Render the main chat interface."""
    st.markdown("### 💬 Chat with AI Assistant")
    
    # Create a container for chat messages
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>AI Assistant:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
                
                # Show products if available
                if message.get("products"):
                    render_product_cards(message["products"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about baking mixes, recipes, or get recommendations..."):
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get response from agent
        with st.spinner("🤔 Thinking..."):
            try:
                # Use the agent to get response
                response = st.session_state.agent.chat(prompt)
                
                # Extract response content
                if isinstance(response, dict):
                    content = response.get("response", "I apologize, but I couldn't process your request.")
                    products = response.get("products", [])
                else:
                    content = str(response)
                    products = []
                
                # Add assistant message to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": content,
                    "products": products,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Rerun to update display
                st.rerun()
                
            except Exception as e:
                error_msg = f"❌ Sorry, I encountered an error: {str(e)}"
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": error_msg,
                    "products": [],
                    "timestamp": datetime.now().isoformat()
                })
                logger.error(f"Chat error: {e}")
                st.rerun()

def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Render header
    render_header()
    
    # Initialize components
    if not initialize_components():
        st.stop()
    
    # Create two columns for layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Main chat interface
        render_chat_interface()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
    
    with col2:
        # Database stats and controls
        render_database_stats()
        
        # Help section
        st.markdown("""
        <div class="stats-box">
            <h4>💡 How to Use</h4>
            <p>Ask me about:</p>
            <ul>
                <li>Baking mix recommendations</li>
                <li>Product comparisons</li>
                <li>Ingredient information</li>
                <li>Baking tips and advice</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("🍰 **King Arthur Baking AI Assistant** - Powered by OpenAI and MongoDB Atlas")

if __name__ == "__main__":
    main() 