"""Main Streamlit application."""

import streamlit as st
import asyncio
from app.utils.api_client import api_client
from app.config import settings


def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="FastAPI Streamlit LLM Starter",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 3rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .status-healthy {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .status-unhealthy {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🚀 FastAPI Streamlit LLM Starter</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">A modern template for building AI-powered applications</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Backend status check
        with st.spinner("Checking backend status..."):
            backend_healthy = asyncio.run(api_client.health_check())
        
        if backend_healthy:
            st.markdown('<div class="status-box status-healthy">✅ Backend is healthy</div>', unsafe_allow_html=True)
            
            # Get model info
            model_info = asyncio.run(api_client.get_models_info())
            if model_info:
                st.subheader("🤖 Model Information")
                st.write(f"**Model:** {model_info.get('current_model', 'Unknown')}")
                st.write(f"**Temperature:** {model_info.get('temperature', 'Unknown')}")
                st.write(f"**Status:** {model_info.get('status', 'Unknown')}")
        else:
            st.markdown('<div class="status-box status-unhealthy">❌ Backend is not available</div>', unsafe_allow_html=True)
            st.error("Please ensure the backend is running and accessible.")
        
        st.divider()
        
        # Settings
        st.subheader("🔧 Settings")
        st.write(f"**Backend URL:** {settings.backend_url}")
        st.write(f"**Debug Mode:** {'On' if settings.debug else 'Off'}")
    
    # Main content
    if backend_healthy:
        # Text processing interface
        st.header("📝 Text Processing")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Input")
            
            # Custom prompt
            custom_prompt = st.text_area(
                "Custom Prompt (optional)",
                value="Please analyze and improve this text:",
                height=100,
                help="Customize how you want the AI to process your text"
            )
            
            # Text input
            input_text = st.text_area(
                "Text to Process",
                height=300,
                placeholder="Enter your text here...",
                help="Enter the text you want to process with AI"
            )
            
            # Process button
            process_button = st.button("🚀 Process Text", type="primary", use_container_width=True)
        
        with col2:
            st.subheader("Output")
            
            if process_button and input_text.strip():
                with st.spinner("Processing text with AI..."):
                    result = asyncio.run(api_client.process_text(input_text, custom_prompt))
                
                if result:
                    st.success("✅ Text processed successfully!")
                    
                    # Display results
                    st.markdown("**Processed Text:**")
                    st.markdown(f"```\n{result['processed_text']}\n```")
                    
                    # Additional info
                    with st.expander("📊 Processing Details"):
                        st.write(f"**Model Used:** {result['model_used']}")
                        st.write(f"**Original Length:** {len(result['original_text'])} characters")
                        st.write(f"**Processed Length:** {len(result['processed_text'])} characters")
                else:
                    st.error("❌ Failed to process text. Please try again.")
            
            elif process_button and not input_text.strip():
                st.warning("⚠️ Please enter some text to process.")
            
            else:
                st.info("👆 Enter text and click 'Process Text' to get started.")
        
        # Example section
        st.divider()
        st.header("💡 Examples")
        
        examples = [
            {
                "title": "Text Improvement",
                "prompt": "Please improve the grammar, clarity, and style of this text:",
                "text": "this is a example of text that need some improvement in grammar and style"
            },
            {
                "title": "Summarization",
                "prompt": "Please provide a concise summary of this text:",
                "text": "Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of 'intelligent agents': any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals."
            },
            {
                "title": "Creative Writing",
                "prompt": "Please expand this into a creative short story:",
                "text": "The old lighthouse keeper noticed something strange in the fog that night."
            }
        ]
        
        cols = st.columns(len(examples))
        for i, example in enumerate(examples):
            with cols[i]:
                st.subheader(example["title"])
                st.write(f"**Prompt:** {example['prompt']}")
                st.write(f"**Text:** {example['text'][:100]}...")
                if st.button(f"Try {example['title']}", key=f"example_{i}"):
                    st.session_state.example_prompt = example["prompt"]
                    st.session_state.example_text = example["text"]
                    st.rerun()
        
        # Handle example selection
        if hasattr(st.session_state, 'example_prompt'):
            st.info("Example loaded! Scroll up to see it in the input fields.")
            # You would need to implement state management to actually populate the fields
    
    else:
        st.error("🔌 Backend connection failed. Please check your configuration and ensure the backend is running.")
        
        st.subheader("🛠️ Troubleshooting")
        st.markdown("""
        1. **Check if the backend is running:**
           ```bash
           cd backend
           uvicorn app.main:app --reload
           ```
        
        2. **Verify the backend URL in your configuration**
        
        3. **Check the logs for any error messages**
        """)


if __name__ == "__main__":
    main() 