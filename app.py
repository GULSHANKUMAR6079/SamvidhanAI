"""
SamvidhanAI - Streamlit Application
Production-grade Constitutional RAG Assistant UI
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config import UIConfig, logger
from src.rag_chain import ConstitutionRAGChain


# Page Configuration
st.set_page_config(
    page_title=UIConfig.PAGE_TITLE,
    page_icon=UIConfig.PAGE_ICON,
    layout=UIConfig.LAYOUT,
    initial_sidebar_state="expanded"
)


# Custom CSS for constitutional theme
def load_custom_css():
    """Apply custom CSS styling"""
    st.markdown(f"""
    <style>
        /* Constitutional Color Theme */
        .stApp {{
            background-color: {UIConfig.COLORS['white']};
        }}
        
        /* Header styling */
        .main-header {{
            background: linear-gradient(90deg, 
                {UIConfig.COLORS['saffron']} 0%, 
                {UIConfig.COLORS['white']} 50%, 
                {UIConfig.COLORS['green']} 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }}
        
        /* Response sections */
        .response-section {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid {UIConfig.COLORS['ashoka_blue']};
            margin: 10px 0;
        }}
        
        /* Citations */
        .citation {{
            background-color: #e3f2fd;
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
            font-size: 0.9em;
        }}
        
        /* Disclaimer */
        .disclaimer {{
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
            margin-top: 20px;
        }}
    </style>
    """, unsafe_allow_html=True)


@st.cache_resource(show_spinner="🏛️ Initializing SamvidhanAI...")
def initialize_rag_chain():
    """Initialize RAG chain (cached for performance)"""
    try:
        chain = ConstitutionRAGChain()
        logger.info("✅ RAG chain initialized for Streamlit")
        return chain, None
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Failed to initialize RAG chain: {error_msg}")
        return None, error_msg


def display_header():
    """Display application header"""
    st.markdown("""
    <div class="main-header">
        <h1>🏛️ SamvidhanAI</h1>
        <p style="font-size: 1.2em; color: #000080;">
            Constitution of India Assistant
        </p>
        <p style="font-size: 0.9em; color: #555;">
            Powered by AI • Grounded in Constitutional Law
        </p>
    </div>
    """, unsafe_allow_html=True)


def display_sidebar(rag_chain):
    """Display sidebar with settings and stats"""
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Emblem_of_India.svg/1200px-Emblem_of_India.svg.png", 
                 width=100)
        
        st.title("Settings")
        
        # User Type Selection
        user_type = st.selectbox(
            "👤 Select Your Role",
            UIConfig.USER_TYPES,
            help="Responses will be tailored to your role"
        )
        
        # Advanced Options
        with st.expander("⚙️ Advanced Options"):
            use_query_expansion = st.checkbox(
                "Use Query Expansion",
                value=False,
                help="Expand queries for better retrieval (slower but more accurate)"
            )
            
            validate_citations = st.checkbox(
                "Validate Citations",
                value=False,
                help="Validate all citations (slower but ensures accuracy)"
            )
        
        st.divider()
        
        # Statistics
        st.subheader("📊 Statistics")
        
        try:
            stats = rag_chain.vector_store.get_collection_stats()
            st.metric("Articles Indexed", stats.get('total_documents', 'N/A'))
        except:
            st.info("Stats unavailable")
        
        # Session stats
        if 'query_count' in st.session_state:
            st.metric("Your Queries", st.session_state.query_count)
        
        st.divider()
        
        # Information
        st.subheader("ℹ️ About")
        st.info("""
        **SamvidhanAI** is an AI-powered assistant for exploring the Constitution of India.
        
        **Features:**
        - Accurate constitutional references
        - Citation-backed answers
        - User-type adapted responses
        - Zero hallucination tolerance
        """)
        
        # Data Source
        st.caption("📚 Data Source: Legislative Department, Govt. of India")
        
    return user_type, use_query_expansion, validate_citations


def format_response(response_data):
    """Format and display the response"""
    answer = response_data.get('answer', '')
    
    # Check if out of scope
    if response_data.get('out_of_scope', False):
        st.warning("⛔ Out of Scope Query")
        st.markdown(answer)
        return
    
    # Display structured answer
    st.markdown(answer)
    
    # Show retrieved sources in expander
    retrieved_docs = response_data.get('retrieved_docs', [])
    if retrieved_docs:
        with st.expander("📚 View Retrieved Sources", expanded=False):
            for i, doc in enumerate(retrieved_docs, 1):
                metadata = doc.metadata
                st.markdown(f"""
                <div class="citation">
                    <strong>Source {i}:</strong> Article {metadata.get('article_number', 'N/A')} 
                    ({metadata.get('part', 'N/A')})<br>
                    <em>{metadata.get('title', 'N/A')}</em><br>
                    <small>{doc.page_content[:200]}...</small>
                </div>
                """, unsafe_allow_html=True)
    
    # Show validation results if available
    validation = response_data.get('validation')
    if validation:
        with st.expander("🔍 Citation Validation", expanded=False):
            if validation.get('validation_passed', True):
                st.success("✅ All citations validated")
            else:
                st.warning(f"⚠️ {len(validation.get('issues', []))} validation issues found")
                for issue in validation.get('issues', []):
                    st.write(f"- {issue.get('claim')}: {issue.get('issue')}")


def display_chat_interface(rag_chain, user_type, use_query_expansion, validate_citations):
    """Display chat interface"""
    
    # Initialize chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        st.session_state.query_count = 0
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(message["content"].get('answer', ''))
            else:
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about the Constitution of India..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.query_count += 1
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Searching constitutional sources..."):
                try:
                    response = rag_chain.query(
                        question=prompt,
                        user_type=user_type,
                        use_query_expansion=use_query_expansion,
                        validate_citations=validate_citations
                    )
                    
                    format_response(response)
                    
                    # Add to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    logger.error(f"Query error: {e}")


def display_sample_queries():
    """Display sample queries for new users"""
    if len(st.session_state.get('messages', [])) == 0:
        st.info("💡 **Try asking:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            - What is Article 21?
            - Explain Fundamental Rights
            - What are Directive Principles?
            """)
        
        with col2:
            st.markdown("""
            - Tell me about Part III
            - What is the Right to Education?
            - Explain Article 356
            """)


def display_disclaimer():
    """Display legal disclaimer"""
    st.markdown(f"""
    <div class="disclaimer">
        {UIConfig.DISCLAIMER}
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application"""
    
    # Load custom CSS
    load_custom_css()
    
    # Display header
    display_header()
    
    # Initialize RAG chain
    rag_chain, error = initialize_rag_chain()
    
    if error:
        st.error(f"""
        ❌ **Failed to initialize SamvidhanAI**
        
        **Error:** {error}
        
        **Common Solutions:**
        1. Check that GOOGLE_API_KEY is set in .env file
        2. Run: `python src/vector_store.py` to initialize the database
        3. Ensure all dependencies are installed: `pip install -r requirements.txt`
        """)
        
        # Show setup instructions
        with st.expander("📖 Setup Instructions"):
            st.code("""
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 3. Download Constitution PDF
python scripts/download_constitution.py

# 4. Process PDF
python src/data_processor.py

# 5. Initialize vector database
python src/vector_store.py

# 6. Run the app
streamlit run app.py
            """, language="bash")
        
        return
    
    # Display sidebar and get settings
    user_type, use_query_expansion, validate_citations = display_sidebar(rag_chain)
    
    # Display sample queries for new users
    display_sample_queries()
    
    # Display chat interface
    display_chat_interface(rag_chain, user_type, use_query_expansion, validate_citations)
    
    # Display disclaimer
    display_disclaimer()


if __name__ == "__main__":
    main()
