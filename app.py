import streamlit as st
import json
from datetime import datetime
import logging
from typing import Dict, List, Optional
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
        
        /* Simple fonts */
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }

        /* Simple Design System */
        :root {
            --primary: #1877f2;
            --primary-hover: #166fe5;
            --background: #f0f2f5;
            --surface: #ffffff;
            --border: #e4e6ea;
            --text-primary: #1c1e21;
            --text-secondary: #65676b;
            --success: #42b883;
            --shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            --radius: 8px;
        }

        /* Base layout */
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

        /* Fixed chat input at bottom of screen */
        .stChatFloatingInputContainer {
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            z-index: 1000 !important;
            background: var(--background) !important;
            border-top: 1px solid var(--border) !important;
            padding: 1rem !important;
            margin: 0 !important;
        }
        
        /* Adjust for sidebar on desktop */
        @media (min-width: 769px) {
            .stChatFloatingInputContainer {
                left: 336px !important; /* Standard Streamlit sidebar width */
            }
        }
        
        /* Ensure chat input styling */
        .stChatInputContainer {
            margin-left: 0 !important;
            margin-right: 0 !important;
            max-width: 100% !important;
        }
        
        /* Add padding to main content so last message isn't hidden */
        .stMainBlockContainer {
            padding-bottom: 160px !important;
        }
        
        /* Ensure messages don't get hidden behind fixed input */
        .stChatMessageContainer {
            margin-bottom: 1rem !important;
        }

        /* Chat messages container */
        .stChatMessageContainer {
            max-height: calc(100vh - 200px) !important;
            overflow-y: auto !important;
            padding-bottom: 120px !important;
        }

        /* Ensure proper scrolling */
        .stApp {
            overflow-y: auto !important;
        }

        /* Simple Background */
        .stApp {
            background: var(--background) !important;
        }

        .main {
            background: var(--background) !important;
        }

        /* Simple header */
        .app-header {
            background: var(--primary);
            color: white;
            padding: 2rem;
            border-radius: var(--radius);
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: var(--shadow);
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

        /* Chat messages */
        .stChatMessage {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius) !important;
            margin-bottom: 1rem !important;
            box-shadow: var(--shadow) !important;
        }

        /* User messages */
        div[data-testid="stChatMessage"]:has(div[data-testid="stAvatar-user"]) {
            background: var(--primary) !important;
            color: white !important;
            border: none !important;
        }

        div[data-testid="stChatMessage"]:has(div[data-testid="stAvatar-user"]) * {
            color: white !important;
        }

        /* Assistant messages */
        div[data-testid="stChatMessage"]:has(div[data-testid="stAvatar-assistant"]) {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
        }

        /* Chat input */
        .stChatInputContainer {
            background: var(--surface) !important;
            border: 2px solid var(--border) !important;
            border-radius: var(--radius) !important;
            box-shadow: var(--shadow) !important;
            transition: all 0.2s ease !important;
        }

        .stChatInputContainer:focus-within {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 3px rgba(24, 119, 242, 0.1) !important;
        }

        /* Horizontal image layout in chat messages */
        .stChatMessage div:has(img) {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 0.5rem !important;
            align-items: flex-start !important;
        }

        /* Small image size constraints in chat messages */
        .stChatMessage img {
            max-width: 120px !important;
            max-height: 90px !important;
            width: auto !important;
            height: auto !important;
            border-radius: var(--radius) !important;
            box-shadow: var(--shadow) !important;
            object-fit: cover !important;
            flex-shrink: 0 !important;
        }

        /* Responsive image sizing for smaller screens */
        @media (max-width: 768px) {
            .stChatMessage img {
                max-width: 80px !important;
                max-height: 60px !important;
            }
        }

        /* Sidebar */
        .stSidebar {
            background: var(--surface) !important;
            border-right: 1px solid var(--border) !important;
            padding: 1rem !important;
        }

        .stSidebar > div {
            background: transparent !important;
        }

        /* Sidebar sections */
        .sidebar-section {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 0.75rem;
            margin-bottom: 0.75rem;
            box-shadow: var(--shadow);
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

        /* Buttons */
        .stButton > button {
            background: var(--primary) !important;
            color: white !important;
            border: none !important;
            border-radius: var(--radius) !important;
            font-weight: 600 !important;
            padding: 0.75rem 1.5rem !important;
            box-shadow: var(--shadow) !important;
            font-size: 0.9rem !important;
        }

        .stButton > button:hover {
            background: var(--primary-hover) !important;
        }

        /* Info cards */
        .info-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 0.75rem;
            margin: 0.5rem 0;
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
            color: var(--text-secondary);
            font-size: 0.7rem;
            margin-top: 0.25rem;
            font-style: italic;
        }

        /* Metrics */
        .metric-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 0.75rem;
            text-align: center;
            box-shadow: var(--shadow);
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

        /* Product cards */
        .product-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }

        .product-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary), var(--success));
        }

        .product-card:hover {
            box-shadow: var(--shadow);
            border-color: var(--primary);
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
            border-radius: var(--radius);
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: var(--shadow);
        }

        .product-link:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-lg);
            color: white;
        }

        /* Welcome card */
        .welcome-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 2rem;
            text-align: center;
            margin: 2rem 0;
            box-shadow: var(--shadow);
        }

        .welcome-card h2 {
            color: var(--text-primary);
            font-weight: 700;
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }

        .welcome-card p {
            color: var(--text-secondary);
            line-height: 1.6;
            font-size: 1rem;
        }

        /* Status pills */
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.375rem;
            padding: 0.25rem 0.75rem;
            background: var(--surface);
            border-radius: var(--radius);
            font-size: 0.7rem;
            font-weight: 600;
            color: var(--text-secondary);
            border: 1px solid var(--border);
        }

        .status-pill.connected {
            background: #d1fae5;
            color: var(--success);
            border-color: var(--success);
        }

        .status-pill.warning {
            background: #fef3c7;
            color: orange;
            border-color: orange;
        }

        .status-pill i {
            font-size: 0.65rem;
        }

        /* Loading message */
        .loading-message {
            background: var(--surface);
            color: var(--text-primary);
            padding: 1.5rem;
            border-radius: var(--radius);
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
            .stChatFloatingInputContainer {
                padding: 0.5rem !important;
                left: 0 !important; /* Full width on mobile */
                right: 0 !important;
            }
            .stMainBlockContainer {
                padding-bottom: 140px !important; /* Less padding on mobile */
            }
        }
    </style>
    
    <script>
        // Auto-scroll to show latest message above fixed input
        function scrollToLatestMessage() {
            setTimeout(() => {
                // Try to get actual input container height
                const inputContainer = document.querySelector('.stChatFloatingInputContainer');
                let inputHeight = 160; // Default fallback
                
                if (inputContainer) {
                    const rect = inputContainer.getBoundingClientRect();
                    inputHeight = rect.height;
                }
                
                const additionalPadding = 30; // Extra space for comfort
                const totalOffset = inputHeight + additionalPadding;
                
                // Scroll to bottom but leave space for input bar
                const scrollPosition = document.body.scrollHeight - window.innerHeight - totalOffset;
                
                window.scrollTo({
                    top: Math.max(0, scrollPosition),
                    behavior: 'smooth'
                });
            }, 500); // Increased timeout for better reliability
        }
        
        // Enhanced observer for new messages
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    // Check if new chat messages were added
                    const newNodes = Array.from(mutation.addedNodes);
                    const hasChatMessage = newNodes.some(node => 
                        node.nodeType === Node.ELEMENT_NODE && 
                        (node.querySelector('[data-testid="stChatMessage"]') || 
                         node.getAttribute && node.getAttribute('data-testid') === 'stChatMessage')
                    );
                    
                    if (hasChatMessage) {
                        scrollToLatestMessage();
                    }
                }
            });
        });
        
        // Start observing when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {
            const targetNode = document.body;
            observer.observe(targetNode, {
                childList: true,
                subtree: true
            });
        });
    </script>
    """, unsafe_allow_html=True)

@st.cache_resource
def initialize_components():
    """Initialize the database manager and agent (cached for performance)."""
    try:
        db_manager = MongoDBManager()
        agent = KingArthurBakingAgent(db_manager=db_manager)
        return db_manager, agent
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        st.error(f"⚠️ Failed to initialize components: {str(e)}")
        return None, None

def render_sidebar(db_manager: Optional[MongoDBManager]):
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
                # Clear chat history and reset conversation thread
                st.session_state.messages = []
                if "thread_id" in st.session_state:
                    del st.session_state.thread_id
                st.rerun()
        
        with col2:
            if st.button("📥 Export", use_container_width=True):
                if "messages" in st.session_state and st.session_state.messages:
                    chat_export = json.dumps(st.session_state.messages, indent=2)
                    st.download_button(
                        "JSON",
                        chat_export,
                        f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        "application/json",
                        use_container_width=True
                    )
        
        # Enhanced stats
        render_enhanced_stats(db_manager)
        
        # Enhanced status
        render_enhanced_status(db_manager)
        
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

    # Initialize chat history and thread_id in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Initialize thread_id for conversation memory
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"conversation_{str(uuid.uuid4())[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Welcome message for new users
    if not st.session_state.messages:
        st.markdown("""
            <div class="welcome-card">
                <h2>Welcome to your baking assistant</h2>
                <p>Ask about products, recipes, techniques, or get personalized recommendations for your baking projects.</p>
            </div>
        """, unsafe_allow_html=True)
                
    # Chat history
    for message in st.session_state.messages:
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
    
    # Initialize components (cached)
    db_manager, agent = initialize_components()
    
    if not db_manager or not agent:
        st.stop()

    render_sidebar(db_manager)
    render_chat_view()

    # --- Chat Input ---
    prompt = st.chat_input("Ask about King Arthur Baking products or techniques...")

    if prompt:
        # Basic validation
        if len(prompt.strip()) < 3:
            st.error("Please enter a longer question.")
            return
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process response with spinner
        with st.spinner("Processing your request..."):
            try:
                # Pass thread_id for conversation memory
                response = agent.chat(prompt, thread_id=st.session_state.thread_id)
                
                if isinstance(response, dict):
                    # Try to get content from the formatted response first
                    content = response.get("response", "")
                    
                    # Fallback to extracting from messages if response field is empty
                    if not content and response.get("messages"):
                        try:
                            last_message = response["messages"][-1]
                            content = getattr(last_message, 'content', str(last_message))
                        except (IndexError, AttributeError):
                            content = "I couldn't process your request."
                    
                    # Get products from the response
                    products = response.get("products", [])
                    
                    # Ensure content is not empty
                    if not content:
                        content = "I processed your request successfully."
                        
                else:
                    content = str(response) if response else "I couldn't generate a response."
                    products = []
                
                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(content)
                    
                    if products:
                        render_product_cards(products)
                
                # Save to session
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": content, 
                    "products": products
                })
                
                # Auto-scroll to show latest message above fixed input
                st.markdown(
                    '<script>setTimeout(() => { if (typeof scrollToLatestMessage !== "undefined") { scrollToLatestMessage(); } else { window.scrollTo(0, document.body.scrollHeight - 180); } }, 300);</script>', 
                    unsafe_allow_html=True
                )
                
            except Exception as e:
                error_msg = "Sorry, I encountered an error. Please try again."
                logger.error(f"Chat error: {e}")
                
                # Display error in chat message
                with st.chat_message("assistant"):
                    st.error(error_msg)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": error_msg, 
                    "products": []
                })
                
                # Auto-scroll to show latest message above fixed input
                st.markdown(
                    '<script>setTimeout(() => { if (typeof scrollToLatestMessage !== "undefined") { scrollToLatestMessage(); } else { window.scrollTo(0, document.body.scrollHeight - 180); } }, 300);</script>', 
                    unsafe_allow_html=True
                )

# --- [ HELPER FUNCTIONS ] ---
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

def render_enhanced_stats(db_manager: Optional[MongoDBManager]):
    """Display enhanced statistics with more details."""
    st.markdown("""
        <div class="sidebar-section">
            <h3><i class="fas fa-chart-line"></i> Statistics</h3>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        if db_manager:
            stats = db_manager.get_stats()
            total_products = stats.get('total_products', 0)
            
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_products:,}</div>
                    <div class="metric-label">Products Available</div>
                </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Could not render stats: {e}")
    
    # Message analytics
    if "messages" in st.session_state:
        messages_count = len(st.session_state.messages)
        user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
        
        st.markdown(f"""
            <div class="info-card">
                <div class="info-card-header">
                    <div class="info-card-title">
                        <i class="fas fa-comments"></i> Conversation
                    </div>
                    <div class="info-card-badge">{messages_count}</div>
                </div>
                <div class="info-card-value">{user_messages} questions asked</div>
            </div>
        """, unsafe_allow_html=True)

def render_enhanced_status(db_manager: Optional[MongoDBManager]):
    """Display enhanced system status with details."""
    st.markdown("""
        <div class="sidebar-section">
            <h3><i class="fas fa-heartbeat"></i> System Health</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Database status with details
    try:
        if db_manager:
            stats = db_manager.get_stats()
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
    db_manager, agent = initialize_components()
    ai_status = "Online" if agent else "Offline"
    ai_class = "connected" if agent else ""
    ai_desc = "GPT-4 powered • Ready to help" if agent else "Agent not initialized"
    
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

if __name__ == "__main__":
    main() 