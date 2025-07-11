import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import pandas as pd
from datetime import datetime
import time
import logging
from typing import Dict, List, Any
import sys
import os

# Add the parent directory to the path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our custom modules
from src.agent import KingArthurBakingAgent
from src.database import MongoDBManager
from src.scraper import KingArthurScraper
from src.embeddings import EmbeddingService
from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="King Arthur Baking AI Assistant",
    page_icon="🍰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
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
        font-size: 3rem;
    }
    .main-header p {
        color: white;
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
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
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border: 1px solid #E0E0E0;
    }
    .product-card h3 {
        color: #2E86AB;
        margin-top: 0;
    }
    .product-card .price {
        color: #FF6B6B;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .stats-card h3 {
        margin: 0;
        font-size: 2rem;
    }
    .stats-card p {
        margin: 0.5rem 0 0 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = None
if 'scraper' not in st.session_state:
    st.session_state.scraper = None

def initialize_components():
    """Initialize all components if not already done."""
    try:
        if st.session_state.agent is None:
            with st.spinner("Initializing AI Agent..."):
                st.session_state.agent = KingArthurBakingAgent()
        
        if st.session_state.db_manager is None:
            with st.spinner("Connecting to Database..."):
                st.session_state.db_manager = MongoDBManager()
        
        if st.session_state.scraper is None:
            st.session_state.scraper = KingArthurScraper()
        
        return True
    except Exception as e:
        st.error(f"Error initializing components: {str(e)}")
        return False

def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>🍰 King Arthur Baking AI Assistant</h1>
        <p>Your intelligent companion for baking mixes and recipes</p>
    </div>
    """, unsafe_allow_html=True)

def render_agent_graph():
    """Render the agent graph visualization."""
    try:
        graph_data = st.session_state.agent.get_graph_visualization()
        
        # Create a network graph using plotly
        fig = go.Figure()
        
        # Node positions (manually set for better visualization)
        positions = {
            "analyze_query": (0, 0),
            "search_products": (-2, -2),
            "get_recommendations": (0, -2),
            "compare_products": (2, -2),
            "reason_about_results": (0, -4),
            "generate_response": (0, -6)
        }
        
        # Colors for different node types
        colors = {
            "process": "#4ECDC4",
            "action": "#FF6B6B",
            "output": "#45B7D1"
        }
        
        # Add edges
        for edge in graph_data.get("edges", []):
            x0, y0 = positions.get(edge["from"], (0, 0))
            x1, y1 = positions.get(edge["to"], (0, 0))
            
            fig.add_trace(go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(color='gray', width=2),
                showlegend=False,
                hoverinfo='none'
            ))
        
        # Add nodes
        for node in graph_data.get("nodes", []):
            x, y = positions.get(node["id"], (0, 0))
            color = colors.get(node["type"], "#4ECDC4")
            
            fig.add_trace(go.Scatter(
                x=[x],
                y=[y],
                mode='markers+text',
                marker=dict(
                    size=30,
                    color=color,
                    line=dict(width=2, color='white')
                ),
                text=node["label"],
                textposition="middle center",
                textfont=dict(size=10, color="white"),
                showlegend=False,
                hoverinfo='text',
                hovertext=f"{node['label']} ({node['type']})"
            ))
        
        fig.update_layout(
            title="AI Agent Workflow",
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            height=400
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating graph: {str(e)}")
        return None

def render_chat_interface():
    """Render the chat interface."""
    st.header("💬 Chat with the AI Assistant")
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
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
    user_input = st.chat_input("Ask me about baking mixes...")
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now()
        })
        
        # Get response from agent
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.agent.chat(user_input)
                
                # Add assistant message to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response["response"],
                    "products": response["products"],
                    "analysis": response["analysis"],
                    "tool_calls": response["tool_calls"],
                    "timestamp": datetime.now()
                })
                
                # Rerun to update display
                st.rerun()
                
            except Exception as e:
                st.error(f"Error getting response: {str(e)}")

def render_product_cards(products: List[Dict]):
    """Render product cards."""
    if not products:
        return
    
    st.subheader("🛍️ Relevant Products")
    
    # Display products in columns
    cols = st.columns(min(len(products), 3))
    
    for i, product in enumerate(products[:6]):  # Show max 6 products
        col = cols[i % 3]
        
        with col:
            st.markdown(f"""
            <div class="product-card">
                <h3>{product.get('name', 'Unknown Product')}</h3>
                <p class="price">{product.get('price', 'Price not available')}</p>
                <p><strong>Description:</strong> {product.get('description', 'No description')[:150]}...</p>
                <p><strong>Ingredients:</strong> {product.get('ingredients', 'Not available')[:100]}...</p>
                <p><strong>Features:</strong> {', '.join(product.get('features', [])[:3])}</p>
                {f'<p><a href="{product.get("url", "#")}" target="_blank">View Product</a></p>' if product.get('url') else ''}
            </div>
            """, unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar with controls and stats."""
    st.sidebar.header("🎛️ Control Panel")
    
    # Database stats
    if st.sidebar.button("🔄 Refresh Stats"):
        if st.session_state.db_manager:
            stats = st.session_state.db_manager.get_stats()
            st.sidebar.markdown(f"""
            <div class="stats-card">
                <h3>{stats.get('total_products', 0)}</h3>
                <p>Total Products</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.sidebar.markdown(f"""
            <div class="stats-card">
                <h3>{stats.get('products_with_embeddings', 0)}</h3>
                <p>Products with AI Embeddings</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Scraping controls
    st.sidebar.subheader("🕷️ Data Scraping")
    
    if st.sidebar.button("🔍 Scrape New Data"):
        with st.spinner("Scraping data from King Arthur Baking..."):
            try:
                products = st.session_state.scraper.scrape_all_mixes()
                new_count = st.session_state.scraper.save_to_json(products)
                
                # Load into database
                if st.session_state.db_manager:
                    inserted_count = st.session_state.db_manager.load_from_json()
                    st.sidebar.success(f"Scraped {len(products)} products, added {new_count} new ones to JSON, inserted {inserted_count} into database")
                else:
                    st.sidebar.success(f"Scraped {len(products)} products, added {new_count} new ones to JSON")
                    
            except Exception as e:
                st.sidebar.error(f"Error scraping data: {str(e)}")
    
    # Embedding controls
    st.sidebar.subheader("🧠 AI Embeddings")
    
    if st.sidebar.button("⚡ Update Embeddings"):
        with st.spinner("Updating AI embeddings..."):
            try:
                embedding_service = EmbeddingService()
                updated_count = embedding_service.update_embeddings()
                st.sidebar.success(f"Updated embeddings for {updated_count} products")
            except Exception as e:
                st.sidebar.error(f"Error updating embeddings: {str(e)}")
    
    # Clear chat history
    if st.sidebar.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()
    
    # Agent settings
    st.sidebar.subheader("⚙️ Agent Settings")
    st.sidebar.text(f"Model: {settings.llm_model}")
    st.sidebar.text(f"Temperature: {settings.temperature}")
    st.sidebar.text(f"Embedding Model: {settings.embedding_model}")

def render_analytics():
    """Render analytics and insights."""
    st.header("📊 Analytics & Insights")
    
    if st.session_state.db_manager:
        try:
            # Get all products for analysis
            products = st.session_state.db_manager.get_all_products(limit=1000)
            
            if products:
                # Create DataFrame for analysis
                df = pd.DataFrame(products)
                
                # Price analysis
                if 'price' in df.columns:
                    prices = []
                    for price_str in df['price'].dropna():
                        # Extract numeric value from price string
                        import re
                        price_match = re.search(r'[\d.]+', str(price_str))
                        if price_match:
                            prices.append(float(price_match.group()))
                    
                    if prices:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig = px.histogram(
                                x=prices,
                                title="Price Distribution",
                                labels={'x': 'Price ($)', 'y': 'Number of Products'}
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            avg_price = sum(prices) / len(prices)
                            min_price = min(prices)
                            max_price = max(prices)
                            
                            st.markdown(f"""
                            <div class="stats-card">
                                <h3>${avg_price:.2f}</h3>
                                <p>Average Price</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="stats-card">
                                <h3>${min_price:.2f} - ${max_price:.2f}</h3>
                                <p>Price Range</p>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Product features analysis
                all_features = []
                for product in products:
                    if product.get('features'):
                        all_features.extend(product['features'])
                
                if all_features:
                    feature_counts = pd.Series(all_features).value_counts().head(10)
                    
                    fig = px.bar(
                        x=feature_counts.values,
                        y=feature_counts.index,
                        orientation='h',
                        title="Top Product Features"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info("No products found in database. Try scraping data first.")
                
        except Exception as e:
            st.error(f"Error generating analytics: {str(e)}")

def main():
    """Main application function."""
    render_header()
    
    # Initialize components
    if not initialize_components():
        st.stop()
    
    # Render sidebar
    render_sidebar()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "🔄 Agent Graph", "📊 Analytics"])
    
    with tab1:
        render_chat_interface()
    
    with tab2:
        st.header("🤖 AI Agent Workflow")
        st.write("This diagram shows how the AI agent processes your queries:")
        
        if st.session_state.agent:
            fig = render_agent_graph()
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        # Agent capabilities
        st.subheader("🎯 Agent Capabilities")
        st.markdown("""
        - **Product Search**: Find specific baking mixes by name or description
        - **Semantic Search**: Understand context and find related products
        - **Recommendations**: Get personalized suggestions based on preferences
        - **Product Comparison**: Compare different mixes side by side
        - **Baking Advice**: Get expert tips and guidance
        - **Ingredient Analysis**: Understand what's in each mix
        """)
    
    with tab3:
        render_analytics()
    
    # Footer
    st.markdown("---")
    st.markdown("🍰 **King Arthur Baking AI Assistant** - Built with Streamlit, LangGraph, and OpenAI")

if __name__ == "__main__":
    main() 