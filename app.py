import streamlit as st
import json
from datetime import datetime
import logging
from typing import Dict, List
import sys
import os
import time

# Add the parent directory to the path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our custom modules
from src.agent import KingArthurBakingAgent
from src.database import MongoDBManager
from src.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="King Arthur Baking Assistant",
    page_icon="🥖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced CSS with clean, modern design focused on usability
st.markdown("""
<style>
    /* Import professional fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
    
    /* Clean, modern color scheme */
    :root {
        --primary-color: #2563eb;
        --primary-hover: #1d4ed8;
        --secondary-color: #f59e0b;
        --success-color: #059669;
        --warning-color: #dc2626;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
        --text-muted: #9ca3af;
        --bg-primary: #ffffff;
        --bg-secondary: #f8fafc;
        --bg-tertiary: #f1f5f9;
        --border-color: #e5e7eb;
        --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --radius: 8px;
        --radius-lg: 12px;
    }

    /* Dark mode */
    @media (prefers-color-scheme: dark) {
        :root {
            --text-primary: #f9fafb;
            --text-secondary: #d1d5db;
            --text-muted: #9ca3af;
            --bg-primary: #1f2937;
            --bg-secondary: #111827;
            --bg-tertiary: #374151;
            --border-color: #4b5563;
            --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px 0 rgba(0, 0, 0, 0.2);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2);
        }
    }

    .stApp[data-theme="dark"] {
        --text-primary: #f9fafb;
        --text-secondary: #d1d5db;
        --text-muted: #9ca3af;
        --bg-primary: #1f2937;
        --bg-secondary: #111827;
        --bg-tertiary: #374151;
        --border-color: #4b5563;
        --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px 0 rgba(0, 0, 0, 0.2);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2);
    }

    /* Force dark mode styles for Streamlit dark theme */
    [data-theme="dark"] {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
    }
    
    [data-theme="dark"] .main {
        background-color: var(--bg-secondary) !important;
    }
    
    [data-theme="dark"] .stApp > header {
        background-color: transparent !important;
    }
    
    [data-theme="dark"] .stApp {
        background-color: var(--bg-secondary) !important;
    }

    /* Global styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    .stApp {
        background-color: var(--bg-secondary);
    }

    /* Clean header */
    .main-header {
        background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
        padding: 2rem;
        border-radius: var(--radius-lg);
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: var(--shadow-lg);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
        font-weight: 400;
    }

    /* Clean cards */
    .stats-box, .info-box {
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow);
    }
    
    .stats-box h4, .info-box h4 {
        color: var(--text-primary);
        margin: 0 0 1rem 0;
        font-size: 1rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .stats-box p, .info-box p {
        color: var(--text-secondary);
        margin: 0.5rem 0;
        font-size: 0.875rem;
        line-height: 1.5;
    }

    /* Clean chat messages */
    .chat-message {
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow);
    }
    
    .chat-message.user-message {
        border-left: 3px solid var(--primary-color);
    }
    
    .chat-message.assistant-message {
        border-left: 3px solid var(--success-color);
    }
    
    .chat-message strong {
        color: var(--text-primary);
        font-weight: 600;
        font-size: 0.875rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .chat-message p {
        color: var(--text-secondary);
        margin: 0.5rem 0;
        line-height: 1.6;
    }

    /* Clean product cards */
    .product-card {
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow);
        transition: all 0.2s ease;
    }
    
    .product-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }
    
    .product-card h5 {
        color: var(--text-primary);
        margin: 0 0 1rem 0;
        font-size: 1.125rem;
        font-weight: 600;
    }
    
    .product-card p {
        color: var(--text-secondary);
        margin: 0.5rem 0;
        font-size: 0.875rem;
        line-height: 1.5;
    }
    
    .product-card strong {
        color: var(--text-primary);
        font-weight: 600;
    }

    /* Modern form styling */
    .stForm > div {
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1rem;
        background: var(--bg-primary);
        margin-bottom: 1rem;
        box-shadow: var(--shadow);
    }
    
    .stForm button {
        height: 2.5rem;
        border-radius: var(--radius);
        background: var(--primary-color);
        color: white;
        font-weight: 600;
        border: none;
        transition: all 0.2s ease;
        font-size: 0.875rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }
    
    .stForm button:hover {
        background: var(--primary-hover);
        transform: translateY(-1px);
    }
    
    .stForm button:disabled {
        background: var(--bg-tertiary);
        color: var(--text-muted);
        cursor: not-allowed;
        transform: none;
    }
    
    /* Professional button styling for main buttons */
    .stButton button {
        border-radius: var(--radius);
        border: 1px solid var(--border-color);
        background: var(--bg-primary);
        color: var(--text-primary);
        font-weight: 500;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease;
        font-size: 0.875rem;
        height: 2.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }
    
    .stButton button:hover {
        background: var(--bg-secondary);
        border-color: var(--primary-color);
        transform: translateY(-1px);
    }
    
    .stButton button:disabled {
        background: var(--bg-tertiary);
        color: var(--text-muted);
        cursor: not-allowed;
        transform: none;
    }
    
    /* Add icons to buttons using CSS */
    .stButton button[data-testid="baseButton-secondary"]:nth-of-type(1)::before {
        content: "\\f1f8";
        font-family: "Font Awesome 5 Free";
        font-weight: 900;
        margin-right: 0.5rem;
    }
    
    .stButton button[data-testid="baseButton-secondary"]:nth-of-type(2)::before {
        content: "\\f2f1";
        font-family: "Font Awesome 5 Free";
        font-weight: 900;
        margin-right: 0.5rem;
    }
    
    /* Send button styling */
    .stForm button[type="submit"]::before {
        content: "\\f1d8";
        font-family: "Font Awesome 5 Free";
        font-weight: 900;
        margin-right: 0.5rem;
    }
    
    .stForm button[type="submit"]:disabled::before {
        content: "\\f110";
        font-family: "Font Awesome 5 Free";
        font-weight: 900;
        margin-right: 0.5rem;
        animation: spin 1s linear infinite;
    }
    
    /* Professional heading icons */
    h1 i, h2 i, h3 i, h4 i, h5 i, h6 i {
        margin-right: 0.5rem;
        opacity: 0.8;
    }
    
    /* List item icons */
    li i {
        margin-right: 0.5rem;
        color: var(--primary-color);
        width: 1rem;
        text-align: center;
    }
    
    /* Professional message styling */
    .chat-message strong i {
        margin-right: 0.5rem;
        opacity: 0.8;
    }
    
    /* Product card icon styling */
    .product-card h5 i {
        margin-right: 0.5rem;
        color: var(--primary-color);
    }
    
    .product-card p strong i {
        margin-right: 0.5rem;
        color: var(--primary-color);
        width: 1rem;
        text-align: center;
    }
    
    /* Status icons with animations */
    .stats-box i.fa-spinner {
        animation: spin 1s linear infinite;
    }
    
    .stats-box i.fa-check-circle {
        color: var(--success-color);
    }
    
    .stats-box i.fa-exclamation-triangle {
        color: var(--warning-color);
    }
    
    /* Link icons */
    a i {
        margin-right: 0.5rem;
    }
    
    /* Responsive icon sizes */
    @media (max-width: 768px) {
        h1 i, h2 i, h3 i {
            font-size: 0.9em;
        }
        
        .stButton button {
            font-size: 0.8rem;
        }
    }

    /* Clean input styling */
    .stTextInput input {
        border-radius: var(--radius);
        border: 1px solid var(--border-color);
        padding: 0.75rem;
        font-size: 0.875rem;
        background: var(--bg-primary);
        color: var(--text-primary);
        transition: border-color 0.2s ease;
    }
    
    .stTextInput input:focus {
        border-color: var(--primary-color);
        outline: none;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }

    /* Status messages */
    .loading-message {
        text-align: center;
        padding: 1.5rem;
        color: var(--text-secondary);
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        margin: 1rem 0;
    }
    
    .error-message {
        background: rgba(220, 38, 38, 0.1);
        border: 1px solid var(--warning-color);
        border-radius: var(--radius);
        padding: 1rem;
        margin: 1rem 0;
        color: var(--warning-color);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.5rem;
        }
        
        .stats-box, .info-box, .chat-message, .product-card {
            padding: 1rem;
        }
    }
    
    /* Improved layout and spacing */
    .main > div {
        padding-top: 1rem;
    }
    
    .stForm {
        margin-top: 1rem;
    }
    
    /* Better button spacing */
    .stButton {
        margin-bottom: 0.5rem;
    }
    
    /* Stable side panel layout */
    .stContainer {
        min-height: 100vh;
    }
    
    /* Prevent layout shifts during form submission */
    .stats-box, .info-box {
        min-height: 120px;
        position: relative;
    }
    
    /* Stable form layout */
    .stForm > div {
        min-height: 80px;
    }
    
    /* Prevent sidebar content jumping */
    [data-testid="stSidebar"] {
        position: sticky;
        top: 0;
    }
    
    /* Column stability */
    .element-container {
        position: relative;
    }
    
    /* Better responsive layout */
    @media (min-width: 769px) {
        .main .block-container {
            max-width: none;
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    
    /* Loading state stability */
    .loading-message {
        min-height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Improved link styling */
    .product-card a {
        color: var(--primary-color);
        text-decoration: none;
        font-weight: 500;
    }
    
    .product-card a:hover {
        text-decoration: underline;
    }
    
    /* Clean scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-tertiary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }
    
    /* Dark mode specific fixes */
    [data-theme="dark"] .stTextInput input {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        border-color: var(--border-color) !important;
    }
    
    [data-theme="dark"] .stForm button {
        background-color: var(--primary-color) !important;
        color: white !important;
    }
    
    [data-theme="dark"] .stButton button {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        border-color: var(--border-color) !important;
    }
    
    [data-theme="dark"] .stButton button:hover {
        background-color: var(--bg-secondary) !important;
        border-color: var(--primary-color) !important;
    }
    
    /* Chat message improvements for dark mode */
    [data-theme="dark"] .chat-message {
        background-color: var(--bg-primary) !important;
        border-color: var(--border-color) !important;
        color: var(--text-primary) !important;
    }
    
    [data-theme="dark"] .stats-box, 
    [data-theme="dark"] .info-box {
        background-color: var(--bg-primary) !important;
        border-color: var(--border-color) !important;
        color: var(--text-primary) !important;
    }

    /* Scroll position preservation */
    .stForm {
        position: relative;
    }
    
    .stForm > div {
        position: relative;
    }
    
    /* Prevent auto-scroll on form submit */
    .stForm button[type="submit"] {
        position: relative;
        z-index: 1;
    }
    
    /* Stable chat container */
    .chat-message {
        position: relative;
        margin-bottom: 1rem;
        animation: fadeIn 0.3s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Prevent layout shifts during processing */
    .stats-box {
        position: relative;
        min-height: 140px;
    }
    
    /* Stable right panel layout */
    .main > div > div:last-child {
        position: sticky;
        top: 1rem;
        height: fit-content;
    }
    
    /* Form stability */
    .stForm {
        position: relative;
        min-height: 100px;
    }
    
    /* Better column stability */
    .stColumns {
        position: relative;
        min-height: 400px;
    }
    
    /* Scroll preservation for containers */
    .stContainer {
        scroll-behavior: smooth;
    }
    
    /* Prevent flash of unstyled content */
    .main {
        opacity: 1;
        transition: opacity 0.1s ease;
    }
    
    /* Loading animation improvements */
    .loading-message i {
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Better error message display */
    .error-message {
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from { transform: translateX(-10px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Stable button layout */
    .stButton {
        position: relative;
        min-height: 38px;
    }
    
    /* Prevent text selection on buttons */
    .stButton button, .stForm button {
        user-select: none;
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
    }
    
    /* Better focus management */
    .stTextInput input:focus {
        outline: none;
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }
    
    /* Stable form inputs */
    .stTextInput {
        position: relative;
        min-height: 38px;
    }
    
    /* Prevent content jumping */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Better mobile stability */
    @media (max-width: 768px) {
        .stColumns {
            min-height: auto;
        }
        
        .main > div > div:last-child {
            position: relative;
            top: auto;
        }
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables with better error handling and unique session ID."""
    try:
        # Create unique session ID for this user session
        if 'session_id' not in st.session_state:
            import uuid
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
    except Exception as e:
        logger.error(f"Error initializing session state: {e}")

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

def initialize_components():
    """Initialize all components with better error handling and loading states."""
    try:
        # Show loading state
        loading_placeholder = st.empty()
        
        # Initialize database manager first
        if st.session_state.db_manager is None:
            loading_placeholder.markdown('<div class="loading-message">Connecting to database...</div>', unsafe_allow_html=True)
            st.session_state.db_manager = MongoDBManager()
        
        # Initialize agent with existing database manager
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

def render_header():
    """Render the application header with session info for production debugging."""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="color: #2c3e50; margin-bottom: 0.5rem;">
            <i class="fas fa-bread-slice"></i> King Arthur Baking AI Assistant
        </h1>
        <p style="color: #7f8c8d; margin-bottom: 0;">
            Your intelligent companion for baking product recommendations and advice
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Production debugging info (can be removed for final deployment)
    if st.session_state.get('session_id'):
        with st.expander("🔍 Session Info (Debug)", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Session ID:** `{st.session_state.session_id}`")
            with col2:
                st.write(f"**Processing:** `{st.session_state.is_processing}`")
            with col3:
                st.write(f"**Messages:** `{len(st.session_state.chat_history)}`")

def render_product_cards(products: List[Dict]):
    """Render product cards with improved layout and error handling."""
    if not products:
        return
    
    st.markdown("### <i class='fas fa-shopping-cart'></i> Recommended Products", unsafe_allow_html=True)
    
    # Limit to 6 products for better display
    products_to_show = products[:6]
    
    # Display products in responsive columns
    cols = st.columns(min(len(products_to_show), 3))
    
    for i, product in enumerate(products_to_show):
        col = cols[i % len(cols)]
        
        with col:
            # Safe string handling with proper escaping
            try:
                name = str(product.get('name', 'Unknown Product')).replace('"', '&quot;').replace("'", "&#39;")
                price = str(product.get('price', 'Price not available'))
                description = str(product.get('description', 'No description available'))
                ingredients = str(product.get('ingredients', 'Ingredients not available'))
                url = product.get('url', '#')
                
                # Truncate long text safely
                if len(description) > 120:
                    description = description[:117] + "..."
                if len(ingredients) > 100:
                    ingredients = ingredients[:97] + "..."
                
                # Format price nicely
                if price != 'Price not available' and not price.startswith('$'):
                    price = f"${price}" if price.replace('.', '').replace(',', '').isdigit() else price
                
                st.markdown(f"""
                <div class="product-card">
                    <h5><i class="fas fa-box"></i> {name}</h5>
                    <p><strong><i class="fas fa-dollar-sign"></i> Price:</strong> <span style="color: var(--success-color); font-weight: 600;">{price}</span></p>
                    <p><strong><i class="fas fa-info-circle"></i> Description:</strong> {description}</p>
                    <p><strong><i class="fas fa-list"></i> Ingredients:</strong> {ingredients}</p>
                    <p><a href="{url}" target="_blank" rel="noopener noreferrer" style="color: var(--primary-color); text-decoration: none; font-weight: 600;"><i class="fas fa-external-link-alt"></i> View Product</a></p>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                logger.error(f"Error rendering product card: {e}")
                st.markdown(f"""
                <div class="product-card">
                    <h5><i class="fas fa-box"></i> Product Information</h5>
                    <p><strong><i class="fas fa-exclamation-triangle"></i> Error:</strong> Unable to display product details</p>
                    <p><strong><i class="fas fa-info-circle"></i> Details:</strong> Product information could not be loaded</p>
                </div>
                """, unsafe_allow_html=True)

def render_database_stats():
    """Render database statistics with stable layout and proper formatting."""
    # Database stats container - always stable
    try:
        if not st.session_state.db_manager:
            st.markdown("""
            <div class="stats-box">
                <h4><i class="fas fa-database"></i> Database</h4>
                <p><strong><i class="fas fa-box"></i> Products:</strong> <span style="color: var(--warning-color);">Not connected</span></p>
                <p><strong><i class="fas fa-search"></i> Searchable:</strong> <span style="color: var(--warning-color);">Unavailable</span></p>
                <p><strong><i class="fas fa-shield-alt"></i> Status:</strong> <span style="color: var(--warning-color);">Connection failed</span></p>
            </div>
            """, unsafe_allow_html=True)
        else:
            stats = st.session_state.db_manager.get_stats()
            total_products = stats.get('total_products', 0)
            indexed_products = stats.get('products_with_embeddings', 0)
            
            st.markdown(f"""
            <div class="stats-box">
                <h4><i class="fas fa-database"></i> Database</h4>
                <p><strong><i class="fas fa-box"></i> Products:</strong> <span style="color: var(--success-color);">{total_products:,}</span></p>
                <p><strong><i class="fas fa-search"></i> Searchable:</strong> <span style="color: var(--success-color);">{indexed_products:,}</span></p>
                <p><strong><i class="fas fa-shield-alt"></i> Status:</strong> <span style="color: var(--success-color);">Connected</span></p>
            </div>
            """, unsafe_allow_html=True)
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        st.markdown("""
        <div class="stats-box">
            <h4><i class="fas fa-database"></i> Database</h4>
            <p><strong><i class="fas fa-box"></i> Products:</strong> <span style="color: var(--warning-color);">Error loading</span></p>
            <p><strong><i class="fas fa-search"></i> Searchable:</strong> <span style="color: var(--warning-color);">Error loading</span></p>
            <p><strong><i class="fas fa-shield-alt"></i> Status:</strong> <span style="color: var(--warning-color);">Error occurred</span></p>
        </div>
        """, unsafe_allow_html=True)
    
    # Status panel - always stable and visible
    try:
        if st.session_state.is_processing:
            status_content = f"""
            <div class="stats-box">
                <h4><i class="fas fa-chart-line"></i> Status</h4>
                <p><strong><i class="fas fa-spinner fa-spin"></i> System:</strong> <span style="color: var(--secondary-color);">Processing...</span></p>
                <p><strong><i class="fas fa-comments"></i> Messages:</strong> <span style="color: var(--text-primary);">{len(st.session_state.chat_history)}</span></p>
                <p><strong><i class="fas fa-clock"></i> State:</strong> <span style="color: var(--secondary-color);">Please wait...</span></p>
            </div>
            """
        else:
            status_content = f"""
            <div class="stats-box">
                <h4><i class="fas fa-chart-line"></i> Status</h4>
                <p><strong><i class="fas fa-check-circle"></i> System:</strong> <span style="color: var(--success-color);">Ready</span></p>
                <p><strong><i class="fas fa-comments"></i> Messages:</strong> <span style="color: var(--text-primary);">{len(st.session_state.chat_history)}</span></p>
                <p><strong><i class="fas fa-clock"></i> State:</strong> <span style="color: var(--success-color);">Ready for input</span></p>
            </div>
            """
        
        st.markdown(status_content, unsafe_allow_html=True)
        
    except Exception as e:
        logger.error(f"Error rendering status: {e}")
        st.markdown("""
        <div class="stats-box">
            <h4><i class="fas fa-chart-line"></i> Status</h4>
            <p><strong><i class="fas fa-exclamation-triangle"></i> System:</strong> <span style="color: var(--warning-color);">Error</span></p>
            <p><strong><i class="fas fa-comments"></i> Messages:</strong> <span style="color: var(--warning-color);">Unknown</span></p>
            <p><strong><i class="fas fa-clock"></i> State:</strong> <span style="color: var(--warning-color);">Error occurred</span></p>
        </div>
        """, unsafe_allow_html=True)

def render_chat_interface():
    """Render the main chat interface with stable layout and no auto-scroll."""
    # Create header with new chat button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### <i class='fas fa-comments'></i> Chat", unsafe_allow_html=True)
    with col2:
        if st.button("🔄 New Chat", key="new_chat_btn", help="Start a new conversation"):
            st.session_state.chat_history = []
            st.session_state.thread_id = f"session_{st.session_state.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.rerun()
    
    # Check if components are initialized
    if st.session_state.initialization_error:
        st.markdown(f'<div class="error-message"><i class="fas fa-exclamation-triangle"></i> {st.session_state.initialization_error}</div>', unsafe_allow_html=True)
        return
    
    # Create a stable container for chat messages
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        if not st.session_state.chat_history:
            st.markdown("""
            <div class="info-box">
                <h4><i class="fas fa-hand-wave"></i> Welcome!</h4>
                <p>Ask me about King Arthur Baking products. I can help you with:</p>
                <ul>
                    <li><i class="fas fa-star"></i> Product recommendations</li>
                    <li><i class="fas fa-balance-scale"></i> Product comparisons</li>
                    <li><i class="fas fa-info-circle"></i> Ingredient information</li>
                    <li><i class="fas fa-lightbulb"></i> Baking tips and advice</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Display all messages
        for message in st.session_state.chat_history:
            timestamp = message.get("timestamp", "")
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong><i class="fas fa-user"></i> You</strong>
                    <p>{message["content"]}</p>
                    <small style="opacity: 0.7; font-size: 0.8em; margin-top: 0.5rem;"><i class="fas fa-clock"></i> {timestamp}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong><i class="fas fa-robot"></i> Assistant</strong>
                    <p>{message["content"]}</p>
                    <small style="opacity: 0.7; font-size: 0.8em; margin-top: 0.5rem;"><i class="fas fa-clock"></i> {timestamp}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Show products if available
                if message.get("products"):
                    render_product_cards(message["products"])
    
    # Show processing status indicator
    if st.session_state.is_processing and st.session_state.get('pending_query'):
        query_preview = st.session_state.pending_query[:50] + "..." if len(st.session_state.pending_query) > 50 else st.session_state.pending_query
        st.markdown(f"""
        <div class="processing-indicator" style="background: linear-gradient(45deg, #f0f8ff, #e6f3ff); border: 2px solid #4CAF50; border-radius: 10px; padding: 15px; margin: 10px 0;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-robot fa-2x" style="color: #4CAF50;"></i>
                <div>
                    <strong style="color: #2196F3;">AI Assistant is thinking...</strong>
                    <br>
                    <small style="color: #666; font-style: italic;">Processing: "{query_preview}"</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state.is_processing:
        st.markdown("""
        <div class="loading-message" style="background: #f8f9fa; border: 1px solid #ddd; border-radius: 8px; padding: 10px; margin: 10px 0;">
            <i class="fas fa-spinner fa-spin" style="color: #007bff;"></i> <strong>Initializing...</strong>
        </div>
        """, unsafe_allow_html=True)
            
def render_chat_input():
    
    # Chat input form section
    st.markdown("### <i class='fas fa-paper-plane'></i> Send Message", unsafe_allow_html=True)
    
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            prompt = st.text_input(
                "Message",
                placeholder="Ask about baking products...",
                disabled=st.session_state.is_processing,
                key="chat_input",
                label_visibility="collapsed"
            )
        
        with col2:
            submit_label = "Send" if not st.session_state.is_processing else "Sending..."
            submit_button = st.form_submit_button(
                submit_label,
                disabled=st.session_state.is_processing,
                use_container_width=True
            )
    
    # Simplified single-phase processing to prevent multiple executions
    if submit_button and prompt and prompt.strip():
        # Create unique message identifier
        message_id = f"{prompt}_{time.time()}"
        
        # Prevent duplicate processing with message-specific check
        if st.session_state.last_processed_message == message_id:
            return
        
        # Validate input
        is_valid, validation_error = validate_user_input(prompt)
        if not is_valid:
            st.error(validation_error)
            return
        
        # Prevent concurrent processing
        if st.session_state.is_processing:
            st.warning("Please wait for the current request to complete.")
            return
        
        # Mark this message as being processed
        st.session_state.last_processed_message = message_id
        st.session_state.is_processing = True
        st.session_state.last_query_time = time.time()
        
        # Add user message immediately
        user_message = {
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "message_id": message_id
        }
        st.session_state.chat_history.append(user_message)
        
        # Process immediately with spinner
        try:
            with st.spinner("🤖 Processing your question..."):
                response = st.session_state.agent.chat(prompt, thread_id=st.session_state.thread_id)
                
                # Extract response content safely
                if isinstance(response, dict):
                    content = response["messages"][-1].content if response["messages"] else "I apologize, but I couldn't process your request."
                    products = response.get("products", [])
                else:
                    content = str(response) if response else "I apologize, but I couldn't generate a response."
                    products = []
                
                # Add assistant message
                assistant_message = {
                    "role": "assistant",
                    "content": content,
                    "products": products,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                }
                st.session_state.chat_history.append(assistant_message)
                
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error while processing your request. Please try again."
            logger.error(f"Chat error for session {st.session_state.session_id}: {e}")
            
            # Add error message
            error_message = {
                "role": "assistant",
                "content": error_msg,
                "products": [],
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            st.session_state.chat_history.append(error_message)
        
        finally:
            # Clear processing state
            st.session_state.is_processing = False
            # Don't rerun - let Streamlit handle the natural update
    
    # Show simple processing indicator without complex logic
    if st.session_state.is_processing:
        st.markdown("""
        <div class="processing-indicator" style="background: linear-gradient(45deg, #f0f8ff, #e6f3ff); border: 2px solid #4CAF50; border-radius: 10px; padding: 15px; margin: 10px 0;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-robot fa-2x" style="color: #4CAF50;"></i>
                <div>
                    <strong style="color: #2196F3;">AI Assistant is thinking...</strong>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main application function with improved error handling."""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Render header
        render_header()
        
        # Initialize components
        if not initialize_components():
            st.stop()
        
        # Create responsive layout
        col1, col2 = st.columns([7, 3])  # Adjusted ratio for better mobile experience
        
        with col1:
            # Main chat interface
            render_chat_interface()
            render_chat_input()
            
            # Control buttons with professional icons
            col_clear, col_refresh = st.columns([1, 1])
            
            with col_clear:
                clear_label = "Clear" if st.session_state.is_processing else "Clear Chat"
                if st.button(clear_label, disabled=st.session_state.is_processing, key="clear_btn"):
                    st.session_state.chat_history = []
                    st.rerun()
            
            with col_refresh:
                refresh_label = "Refresh"
                if st.button(refresh_label, disabled=st.session_state.is_processing, key="refresh_btn"):
                    # Clear all session state except session_id and thread_id
                    st.session_state.agent = None
                    st.session_state.db_manager = None
                    st.session_state.initialization_error = None
                    st.session_state.is_processing = False
                    st.session_state.pending_query = None
                    st.session_state.processing_started = False
                    st.session_state.last_query_time = 0
                    st.session_state.last_processed_message = None
                    # Keep session_id and regenerate thread_id
                    st.session_state.thread_id = f"session_{st.session_state.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    st.rerun()
        
        with col2:
            # Database stats and controls
            render_database_stats()
            
            # Simple help section
            st.markdown("""
            <div class="info-box">
                <h4><i class="fas fa-lightbulb"></i> Tips</h4>
                <p>For best results:</p>
                <ul>
                    <li>Be specific about what you're looking for</li>
                    <li>Mention dietary restrictions if relevant</li>
                    <li>Ask about ingredients or comparisons</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error("An error occurred while running the application. Please refresh the page.")

if __name__ == "__main__":
    main() 