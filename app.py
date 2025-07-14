import streamlit as st
import json
from datetime import datetime
import logging
from typing import Dict, List
import sys
import os
import time
import uuid

# Add the parent directory to the path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our custom modules
from src.agent import KingArthurBakingAgent
from src.database import MongoDBManager
from src.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- [ MODERN FACEBOOK-LIKE STYLES ] ---
def apply_professional_styles():
    st.markdown("""
    <style>
        /* Modern fonts - Fallback safe for HF Spaces */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css');
        
        /* Fallback fonts if imports fail */
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }

        /* Modern Light Design System - Simplified for HF Spaces */
        :root {
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --primary-light: #eff6ff;
            --secondary: #059669;
            --accent: #dc2626;
            --background: #f8fafc;
            --surface: #ffffff;
            --surface-elevated: #ffffff;
            --border: #e2e8f0;
            --border-light: #f1f5f9;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-tertiary: #64748b;
            --success: #059669;
            --warning: #d97706;
            --error: #dc2626;
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
            --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 4px 6px rgba(0, 0, 0, 0.1);
            --radius-sm: 4px;
            --radius: 6px;
            --radius-lg: 8px;
            --radius-xl: 12px;
        }

        /* Base layout - Enhanced for Hugging Face Spaces */
        .main {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--background) !important;
            color: var(--text-primary);
        }

        .main .block-container {
            max-width: 1200px;
            padding: 1.5rem;
            margin: 0 auto;
        }

        /* AGGRESSIVE Background Enforcement for HF Spaces */
        * {
            background-color: #f8fafc !important;
        }

        html {
            background: #f8fafc !important;
            background-color: #f8fafc !important;
        }

        body {
            background: #f8fafc !important;
            background-color: #f8fafc !important;
        }

        .stApp {
            background: #f8fafc !important;
            background-color: #f8fafc !important;
        }

        .stApp > div {
            background: #f8fafc !important;
            background-color: #f8fafc !important;
        }

        [data-testid="stAppViewContainer"] {
            background: #f8fafc !important;
            background-color: #f8fafc !important;
        }

        [data-testid="stAppViewContainer"] > .main {
            background: #f8fafc !important;
            background-color: #f8fafc !important;
            min-height: 100vh !important;
        }

        .main {
            background: #f8fafc !important;
            background-color: #f8fafc !important;
        }

        .main .block-container {
            background: #f8fafc !important;
            background-color: #f8fafc !important;
        }

        /* Override any dark themes */
        [data-theme="dark"] {
            background: #f8fafc !important;
            background-color: #f8fafc !important;
        }

        /* Force light background on all containers */
        div, section, article, header, footer, main {
            background-color: #f8fafc !important;
        }

        /* Modern header with explicit colors */
        .app-header {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            color: white !important;
            padding: 2.5rem 2rem !important;
            border-radius: 12px !important;
            text-align: center !important;
            margin-bottom: 2rem !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
            position: relative !important;
            overflow: hidden !important;
        }

        .app-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="1" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
            pointer-events: none;
        }

        .app-header h1 {
            font-size: 2.5rem;
            font-weight: 800;
            margin: 0 0 0.5rem 0;
            position: relative;
            z-index: 1;
        }

        .app-header p {
            font-size: 1.25rem;
            opacity: 0.9;
            margin: 0;
            font-weight: 400;
            position: relative;
            z-index: 1;
        }

        /* Modern chat messages with explicit colors */
        .stChatMessage {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            margin-bottom: 1.5rem !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
            transition: all 0.2s ease !important;
        }

        .stChatMessage:hover {
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
            transform: translateY(-1px) !important;
        }

        /* User messages with blue gradient */
        div[data-testid="stChatMessage"]:has(div[data-testid="stAvatar-user"]) {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            color: white !important;
            border: none !important;
        }

        div[data-testid="stChatMessage"]:has(div[data-testid="stAvatar-user"]) * {
            color: white !important;
        }

        /* Assistant messages with white background */
        div[data-testid="stChatMessage"]:has(div[data-testid="stAvatar-assistant"]) {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
        }

        /* Horizontal image layout in chat messages */
        .stChatMessage div:has(img) {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 0.75rem !important;
            align-items: flex-start !important;
        }

        /* Image size constraints in chat messages */
        .stChatMessage img {
            max-width: 200px !important;
            max-height: 150px !important;
            width: auto !important;
            height: auto !important;
            border-radius: var(--radius) !important;
            box-shadow: var(--shadow) !important;
            object-fit: contain !important;
            flex-shrink: 0 !important;
        }

        /* Responsive image sizing for smaller screens */
        @media (max-width: 768px) {
            .stChatMessage img {
                max-width: 120px !important;
                max-height: 90px !important;
            }
        }

        /* Modern chat input */
        .stChatInputContainer {
            background: var(--surface) !important;
            border: 2px solid var(--border) !important;
            border-radius: var(--radius-xl) !important;
            box-shadow: var(--shadow) !important;
            transition: all 0.2s ease !important;
        }

        .stChatInputContainer:focus-within {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 3px rgba(24, 119, 242, 0.1) !important;
        }

        /* Modern sidebar with white background */
        .stSidebar {
            background: #ffffff !important;
            border-right: 1px solid #e2e8f0 !important;
            padding: 1rem !important;
        }

        .stSidebar > div {
            background: #ffffff !important;
        }

        .stSidebar * {
            background-color: transparent !important;
        }

        /* Simple clean sidebar sections */
        .sidebar-section {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 0.75rem;
            margin-bottom: 0.75rem;
            box-shadow: var(--shadow-sm);
        }

        .sidebar-section h3 {
            color: var(--text-primary);
            font-size: 0.85rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }

        .sidebar-section h3 i {
            font-size: 0.8rem;
            color: var(--primary);
        }

        /* Modern buttons */
        .stButton > button {
            background: var(--primary) !important;
            color: white !important;
            border: none !important;
            border-radius: var(--radius-lg) !important;
            font-weight: 600 !important;
            padding: 0.875rem 1.75rem !important;
            transition: all 0.2s ease !important;
            box-shadow: var(--shadow) !important;
            font-size: 0.95rem !important;
        }

        .stButton > button:hover {
            background: var(--primary-hover) !important;
            transform: translateY(-1px) !important;
            box-shadow: var(--shadow-lg) !important;
        }

        /* Enhanced info cards */
        .info-card {
            background: var(--border-light);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 0.75rem;
            margin: 0.5rem 0;
            transition: all 0.2s ease;
        }

        .info-card:hover {
            background: var(--primary-light);
            border-color: var(--primary);
        }

        .info-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }

        .info-card-title {
            font-weight: 600;
            color: var(--text-primary);
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .info-card-value {
            color: var(--text-secondary);
            font-size: 0.8rem;
            line-height: 1.4;
        }

        .info-card-header i {
            font-size: 0.8rem;
            color: var(--primary);
        }

        .info-card-badge {
            background: var(--primary);
            color: white;
            font-size: 0.7rem;
            padding: 0.25rem 0.5rem;
            border-radius: var(--radius);
            font-weight: 600;
        }

        .info-card-meta {
            color: var(--text-tertiary);
            font-size: 0.7rem;
            margin-top: 0.25rem;
            font-style: italic;
        }

        /* Simple metrics */
        .metric-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 0.75rem;
            text-align: center;
            box-shadow: var(--shadow-sm);
            margin: 0.5rem 0;
        }

        .metric-value {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 0.25rem;
        }

        .metric-label {
            font-size: 0.7rem;
            color: var(--text-secondary);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }

        /* Enhanced product cards with explicit colors */
        .product-card {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            padding: 1.5rem !important;
            margin: 1rem 0 !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
            transition: all 0.3s ease !important;
            position: relative !important;
            overflow: hidden !important;
        }

        .product-card::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            height: 3px !important;
            background: linear-gradient(90deg, #2563eb, #059669) !important;
        }

        .product-card:hover {
            transform: translateY(-4px) !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
            border-color: #2563eb !important;
        }

        .product-title {
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 1rem;
            line-height: 1.4;
        }

        .product-info {
            margin: 0.75rem 0;
            color: var(--text-secondary);
            line-height: 1.6;
        }

        .product-price {
            color: var(--success);
            font-weight: 700;
            font-size: 1.1rem;
        }

        .product-link {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            margin-top: 1rem;
            padding: 0.75rem 1.5rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
            color: white;
            text-decoration: none;
            border-radius: var(--radius-lg);
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: var(--shadow);
        }

        .product-link:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-lg);
            color: white;
        }

        /* Modern welcome card */
        .welcome-card {
            background: linear-gradient(135deg, var(--primary-light) 0%, var(--surface) 100%);
            border: 1px solid var(--border);
            border-radius: var(--radius-xl);
            padding: 3rem 2rem;
            text-align: center;
            margin: 2rem 0;
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }

        .welcome-card::before {
            content: '🍞';
            position: absolute;
            top: -20px;
            right: -20px;
            font-size: 6rem;
            opacity: 0.1;
            transform: rotate(15deg);
        }

        .welcome-card h2 {
            color: var(--text-primary);
            font-weight: 700;
            margin-bottom: 1rem;
            font-size: 1.5rem;
            position: relative;
            z-index: 1;
        }

        .welcome-card p {
            color: var(--text-secondary);
            line-height: 1.6;
            font-size: 1.05rem;
            position: relative;
            z-index: 1;
        }



        /* Enhanced status pills */
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.375rem;
            padding: 0.25rem 0.75rem;
            background: var(--border-light);
            border-radius: var(--radius);
            font-size: 0.7rem;
            font-weight: 600;
            color: var(--text-secondary);
            border: 1px solid var(--border);
        }

        .status-pill.connected {
            background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
            color: var(--success);
            border-color: var(--success);
        }

        .status-pill.warning {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            color: var(--warning);
            border-color: var(--warning);
        }

        .status-pill i {
            font-size: 0.65rem;
        }

        /* Loading states */
        .loading-message {
            background: var(--primary-light);
            color: var(--text-primary);
            padding: 1.5rem;
            border-radius: var(--radius-lg);
            text-align: center;
            font-weight: 500;
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
        }

        /* Hide unnecessary elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* Responsive design */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 1rem 0.5rem;
            }
            .app-header {
                padding: 2rem 1rem;
            }
            .app-header h1 {
                font-size: 2rem;
            }
            .sidebar-section {
                padding: 1rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)

# --- [ SESSION STATE AND COMPONENT INITIALIZATION ] --- (Existing code, largely unchanged)
def initialize_session_state():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = None
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False
    if 'last_query_time' not in st.session_state:
        st.session_state.last_query_time = 0
    if 'initialization_error' not in st.session_state:
        st.session_state.initialization_error = None
    if 'pending_query' not in st.session_state:
        st.session_state.pending_query = None
    if 'processing_started' not in st.session_state:
        st.session_state.processing_started = False
    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = f"session_{st.session_state.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if 'last_processed_message' not in st.session_state:
        st.session_state.last_processed_message = None

def initialize_components():
    try:
        loading_placeholder = st.empty()
        if st.session_state.db_manager is None:
            loading_placeholder.markdown('<div class="loading-message">Connecting to database...</div>', unsafe_allow_html=True)
            st.session_state.db_manager = MongoDBManager()
        
        if st.session_state.agent is None:
            loading_placeholder.markdown('<div class="loading-message">Initializing AI agent...</div>', unsafe_allow_html=True)
            st.session_state.agent = KingArthurBakingAgent(db_manager=st.session_state.db_manager)
        
        loading_placeholder.empty()
        return True
    except Exception as e:
        error_msg = f"Failed to initialize components: {str(e)}"
        logger.error(error_msg)
        st.session_state.initialization_error = error_msg
        st.error(f"⚠️ {error_msg}")
        return False

# --- [ MINIMAL UI RENDERING FUNCTIONS ] ---
def render_sidebar():
    with st.sidebar:
        # Enhanced header
        st.markdown("""
            <div class="sidebar-section">
                <h3><i class="fas fa-bread-slice"></i> King Arthur Baking AI</h3>
                <div class="info-card-value">Professional baking guidance & product recommendations</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.session_state.pending_query = None
                st.session_state.is_processing = False
                st.rerun()
        
        with col2:
            if st.button("📥 Export", use_container_width=True):
                if st.session_state.chat_history:
                    chat_export = json.dumps(st.session_state.chat_history, indent=2)
                    st.download_button(
                        "JSON",
                        chat_export,
                        f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        "application/json",
                        use_container_width=True
                    )
        
        # Enhanced stats
        render_enhanced_stats()
        
        # Enhanced status
        render_enhanced_status()
        
        # Quick tips
        render_quick_tips()

def render_chat_view():
    # Professional header
    st.markdown("""
        <div class="app-header">
            <h1>🍞 King Arthur Baking AI</h1>
            <p>Professional baking guidance and product recommendations</p>
        </div>
    """, unsafe_allow_html=True)

    # Welcome message for new users
    if not st.session_state.chat_history:
        st.markdown("""
            <div class="welcome-card">
                <h2>Welcome to your baking assistant</h2>
                <p>Ask about products, recipes, techniques, or get personalized recommendations for your baking projects.</p>
            </div>
        """, unsafe_allow_html=True)
                
    # Chat history
    for message in st.session_state.chat_history:
        with st.chat_message(name=message["role"]):
            st.markdown(message["content"])
            
            if message.get("products"):
                render_product_cards(message["products"])

def main():
    st.set_page_config(
        page_title="King Arthur Baking AI", 
        layout="centered",
        initial_sidebar_state="expanded",
        page_icon="🍞"
    )
    apply_professional_styles()
    initialize_session_state()
    
    if not initialize_components():
        st.stop()

    render_sidebar()
    render_chat_view()

    # --- Chat Input ---
    prompt = st.chat_input("Ask about King Arthur Baking products or techniques...", key="user_input")

    if prompt:
        # Basic validation
        if len(prompt.strip()) < 3:
            st.error("Please enter a longer question.")
            return
        
        # Update timestamp
        st.session_state.last_query_time = time.time()
        
        # Add user message
        user_message = {"role": "user", "content": prompt}
        st.session_state.chat_history.append(user_message)
        
        # Show user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process response with spinner outside chat message
        with st.spinner("Processing your request..."):
            try:
                response = st.session_state.agent.chat(prompt, thread_id=st.session_state.thread_id)
                
                if isinstance(response, dict):
                    content = response["messages"][-1].content if response["messages"] else "I couldn't process your request."
                    products = response.get("products", [])
                else:
                    content = str(response) if response else "I couldn't generate a response."
                    products = []
                
                # Display response in chat message after processing
                with st.chat_message("assistant"):
                    st.markdown(content)
                    
                    if products:
                        render_product_cards(products)
                
                # Save to session
                assistant_message = {
                    "role": "assistant", 
                    "content": content, 
                    "products": products
                }
                st.session_state.chat_history.append(assistant_message)
                
            except Exception as e:
                error_msg = "Sorry, I encountered an error. Please try again."
                logger.error(f"Chat error: {e}")
                
                # Display error in chat message
                with st.chat_message("assistant"):
                    st.error(error_msg)
                
                error_message = {"role": "assistant", "content": error_msg, "products": []}
                st.session_state.chat_history.append(error_message)

# --- [ EXISTING HELPER FUNCTIONS (UNCHANGED) ] ---
def render_product_cards(products: List[Dict]):
    """Render minimal, professional product cards."""
    if not products:
        return
    
    st.markdown("### 🛍️ Recommended Products")
    
    # Display up to 4 products for cleaner layout
    products_to_show = products[:4]
    cols = st.columns(min(len(products_to_show), 2))
    
    for i, product in enumerate(products_to_show):
        col = cols[i % len(cols)]
        
        with col:
            try:
                name = str(product.get('name', 'Unknown Product')).replace('"', '&quot;').replace("'", "&#39;")
                price = str(product.get('price', 'Price not available'))
                description = str(product.get('description', 'No description available'))
                url = product.get('url', '#')
                
                # Clean truncation
                if len(description) > 100:
                    description = description[:97] + "..."
                
                # Price formatting
                if price != 'Price not available' and not price.startswith('$'):
                    if price.replace('.', '').replace(',', '').isdigit():
                        price = f"${price}"
                
                st.markdown(f"""
                <div class="product-card">
                    <div class="product-title">{name}</div>
                    <div class="product-info"><strong>Price:</strong> <span class="product-price">{price}</span></div>
                    <div class="product-info">{description}</div>
                    <a href="{url}" target="_blank" class="product-link">
                        <i class="fas fa-external-link-alt"></i>
                        View Product
                    </a>
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                logger.error(f"Error rendering product card: {e}")
                col.error("Unable to load product")
                
    # Show additional count
    if len(products) > 4:
        st.caption(f"Showing 4 of {len(products)} products")

def render_enhanced_stats():
    """Display enhanced statistics with more details."""
    st.markdown("""
        <div class="sidebar-section">
            <h3><i class="fas fa-chart-line"></i> Session Analytics</h3>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        if st.session_state.db_manager:
            stats = st.session_state.db_manager.get_stats()
            total_products = stats.get('total_products', 0)
            
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_products:,}</div>
                    <div class="metric-label">Products Available</div>
                </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Could not render stats: {e}")
    
    # Enhanced message analytics
    messages_count = len(st.session_state.chat_history)
    user_messages = len([m for m in st.session_state.chat_history if m["role"] == "user"])
    session_time = datetime.now().strftime("%H:%M")
    
    st.markdown(f"""
        <div class="info-card">
            <div class="info-card-header">
                <div class="info-card-title">
                    <i class="fas fa-comments"></i> Conversation
                </div>
                <div class="info-card-badge">{messages_count}</div>
            </div>
            <div class="info-card-value">{user_messages} questions asked</div>
            <div class="info-card-meta">Session started at {session_time}</div>
        </div>
    """, unsafe_allow_html=True)

def render_enhanced_status():
    """Display enhanced system status with details."""
    st.markdown("""
        <div class="sidebar-section">
            <h3><i class="fas fa-heartbeat"></i> System Health</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Database status with details
    try:
        if st.session_state.db_manager:
            stats = st.session_state.db_manager.get_stats()
            total_products = stats.get('total_products', 0)
            if total_products > 0:
                status_class = "connected"
                status_text = "Connected"
                status_desc = "Database accessible • Fast response"
            else:
                status_class = "warning"
                status_text = "Limited"
                status_desc = "Database accessible • Limited products"
        else:
            status_class = ""
            status_text = "Offline"
            status_desc = "Database not accessible"
    except Exception as e:
        status_class = ""
        status_text = "Error"
        status_desc = "Connection error occurred"
    
    st.markdown(f"""
        <div class="info-card">
            <div class="info-card-header">
                <div class="info-card-title">
                    <i class="fas fa-database"></i> Database
                </div>
                <div class="status-pill {status_class}">
                    <i class="fas fa-circle"></i> {status_text}
                </div>
            </div>
            <div class="info-card-value">{status_desc}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # AI status with details
    ai_status = "Online" if st.session_state.agent else "Offline"
    ai_class = "connected" if st.session_state.agent else ""
    ai_desc = "GPT-4 powered • Ready to help" if st.session_state.agent else "Agent not initialized"
    
    st.markdown(f"""
        <div class="info-card">
            <div class="info-card-header">
                <div class="info-card-title">
                    <i class="fas fa-robot"></i> AI Assistant
                </div>
                <div class="status-pill {ai_class}">
                    <i class="fas fa-circle"></i> {ai_status}
                </div>
            </div>
            <div class="info-card-value">{ai_desc}</div>
        </div>
    """, unsafe_allow_html=True)

def render_quick_tips():
    """Display helpful baking tips and quick actions."""
    st.markdown("""
        <div class="sidebar-section">
            <h3><i class="fas fa-lightbulb"></i> Quick Tips</h3>
        </div>
    """, unsafe_allow_html=True)
    
    tips = [
        {"icon": "fas fa-balance-scale", "tip": "Always measure by weight for consistency"},
        {"icon": "fas fa-thermometer-half", "tip": "Room temperature ingredients mix better"},
        {"icon": "fas fa-fire", "tip": "Preheat oven 20+ minutes for best results"}
    ]
    
    for tip in tips:
        st.markdown(f"""
            <div class="info-card">
                <div class="info-card-header">
                    <div class="info-card-title">
                        <i class="{tip['icon']}"></i> Pro Tip
                    </div>
                </div>
                <div class="info-card-value">{tip['tip']}</div>
            </div>
        """, unsafe_allow_html=True)

def validate_user_input(prompt: str) -> tuple[bool, str]:
    """Validate user input with comprehensive checks."""
    if not prompt or not prompt.strip():
        return False, "Please enter a question or request."
    
    if len(prompt.strip()) < 3:
        return False, "Please enter a longer question (at least 3 characters)."
    
    if len(prompt) > 500:
        return False, "Question is too long. Please keep it under 500 characters."
    
    # More lenient rate limiting for production (0.5 second cooldown)
    current_time = time.time()
    if current_time - st.session_state.last_query_time < 0.5:  # Reduced from 2 seconds
        return False, "Please wait a moment before sending another message."
    
    return True, ""

if __name__ == "__main__":
    main() 