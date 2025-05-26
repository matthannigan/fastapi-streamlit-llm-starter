"""Main Streamlit application."""

import sys
import os
# Add the parent directory to Python path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import asyncio
import json
from typing import Dict, Any, Optional

from shared.models import TextProcessingRequest, ProcessingOperation
from app.utils.api_client import api_client, run_async
from app.config import settings

# Configure Streamlit page
st.set_page_config(
    page_title=settings.page_title,
    page_icon=settings.page_icon,
    layout=settings.layout,
    initial_sidebar_state="expanded"
)

def display_header():
    """Display the application header."""
    st.title("🤖 AI Text Processor")
    st.markdown(
        "Process text using advanced AI models. Choose from summarization, "
        "sentiment analysis, key point extraction, and more!"
    )
    st.divider()

def check_api_health():
    """Check API health and display status."""
    with st.sidebar:
        st.subheader("🔧 System Status")
        
        # Check API health
        is_healthy = run_async(api_client.health_check())
        
        if is_healthy:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Unavailable")
            st.warning("Please ensure the backend service is running.")
            return False
        
        return True

def get_operation_info() -> Optional[Dict[str, Any]]:
    """Get operation information from API."""
    operations = run_async(api_client.get_operations())
    if operations:
        return {op['id']: op for op in operations['operations']}
    return None

def create_sidebar():
    """Create the sidebar with operation selection."""
    with st.sidebar:
        st.subheader("⚙️ Configuration")
        
        # Get available operations
        operations_info = get_operation_info()
        if not operations_info:
            st.error("Failed to load operations")
            return None, {}
        
        # Operation selection
        operation_options = {
            op_id: f"{info['name']} - {info['description']}"
            for op_id, info in operations_info.items()
        }
        
        selected_op = st.selectbox(
            "Choose Operation",
            options=list(operation_options.keys()),
            format_func=lambda x: operation_options[x],
            key="operation_select"
        )
        
        # Operation-specific options
        options = {}
        op_info = operations_info[selected_op]
        
        if "max_length" in op_info.get("options", []):
            options["max_length"] = st.slider(
                "Summary Length (words)",
                min_value=50,
                max_value=500,
                value=150,
                step=25
            )
        
        if "max_points" in op_info.get("options", []):
            options["max_points"] = st.slider(
                "Number of Key Points",
                min_value=3,
                max_value=10,
                value=5
            )
        
        if "num_questions" in op_info.get("options", []):
            options["num_questions"] = st.slider(
                "Number of Questions",
                min_value=3,
                max_value=10,
                value=5
            )
        
        return selected_op, options

def display_text_input() -> tuple[str, Optional[str]]:
    """Display text input area."""
    st.subheader("📝 Input Text")
    
    # Text input options
    input_method = st.radio(
        "Input Method",
        ["Type/Paste Text", "Upload File"],
        horizontal=True
    )
    
    text_content = ""
    
    if input_method == "Type/Paste Text":
        text_content = st.text_area(
            "Enter your text here:",
            height=200,
            max_chars=settings.max_text_length,
            placeholder="Paste or type the text you want to process...",
            value=st.session_state.get('text_input', '')
        )
    else:
        uploaded_file = st.file_uploader(
            "Upload a text file",
            type=['txt', 'md'],
            help="Upload a .txt or .md file"
        )
        
        if uploaded_file is not None:
            try:
                text_content = str(uploaded_file.read(), "utf-8")
                st.success(f"File uploaded successfully! ({len(text_content)} characters)")
                
                # Show preview
                with st.expander("Preview uploaded text"):
                    st.text(text_content[:500] + "..." if len(text_content) > 500 else text_content)
            except Exception as e:
                st.error(f"Error reading file: {e}")
    
    # Question input for Q&A
    question = None
    if st.session_state.get("operation_select") == "qa":
        question = st.text_input(
            "Enter your question about the text:",
            placeholder="What is the main topic discussed in this text?"
        )
    
    return text_content, question

def display_results(response, operation: str):
    """Display processing results."""
    st.subheader("📊 Results")
    
    # Processing info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Operation", operation.replace("_", " ").title())
    with col2:
        if response.processing_time:
            st.metric("Processing Time", f"{response.processing_time:.2f}s")
    with col3:
        word_count = response.metadata.get("word_count", "N/A")
        st.metric("Word Count", word_count)
    
    st.divider()
    
    # Display results based on operation type
    if operation == "summarize":
        st.markdown("### 📋 Summary")
        st.write(response.result)
    
    elif operation == "sentiment":
        st.markdown("### 🎭 Sentiment Analysis")
        sentiment = response.sentiment
        
        # Color code sentiment
        color = {
            "positive": "green",
            "negative": "red",
            "neutral": "gray"
        }.get(sentiment.sentiment, "gray")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Sentiment:** :{color}[{sentiment.sentiment.title()}]")
            st.progress(sentiment.confidence)
            st.caption(f"Confidence: {sentiment.confidence:.2%}")
        
        with col2:
            st.markdown("**Explanation:**")
            st.write(sentiment.explanation)
    
    elif operation == "key_points":
        st.markdown("### 🎯 Key Points")
        for i, point in enumerate(response.key_points, 1):
            st.markdown(f"{i}. {point}")
    
    elif operation == "questions":
        st.markdown("### ❓ Generated Questions")
        for i, question in enumerate(response.questions, 1):
            st.markdown(f"{i}. {question}")
    
    elif operation == "qa":
        st.markdown("### 💬 Answer")
        st.write(response.result)
    
    # Debug information
    if settings.show_debug_info:
        with st.expander("🔍 Debug Information"):
            st.json(response.dict())

def main():
    """Main application function."""
    display_header()
    
    # Check API health
    if not check_api_health():
        st.stop()
    
    # Create sidebar
    selected_operation, options = create_sidebar()
    if not selected_operation:
        st.stop()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Text input
        text_content, question = display_text_input()
        
        # Process button
        if st.button("🚀 Process Text", type="primary", use_container_width=True):
            if not text_content.strip():
                st.error("Please enter some text to process.")
                return
            
            if selected_operation == "qa" and not question:
                st.error("Please enter a question for Q&A operation.")
                return
            
            # Create request
            request = TextProcessingRequest(
                text=text_content,
                operation=ProcessingOperation(selected_operation),
                question=question,
                options=options
            )
            
            # Process text with progress indicator
            with st.spinner("Processing your text..."):
                response = run_async(api_client.process_text(request))
            
            if response and response.success:
                # Store results in session state
                st.session_state['last_response'] = response
                st.session_state['last_operation'] = selected_operation
                st.success("✅ Processing completed!")
            else:
                st.error("❌ Processing failed. Please try again.")
    
    with col2:
        # Tips and information
        st.subheader("💡 Tips")
        st.markdown("""
        **For best results:**
        - Use clear, well-structured text
        - Longer texts work better for summarization
        - Be specific with your questions for Q&A
        - Try different operations to explore your text
        """)
        
        # Example texts
        with st.expander("📚 Example Texts"):
            if st.button("Load News Article Example"):
                example_text = """
                Artificial intelligence is rapidly transforming industries across the globe. 
                From healthcare to finance, AI technologies are enabling unprecedented 
                automation and decision-making capabilities. Machine learning algorithms 
                can now process vast amounts of data in seconds, identifying patterns 
                that would take humans hours or days to discover. However, this rapid 
                advancement also raises important questions about job displacement, 
                privacy, and the ethical implications of automated decision-making. 
                As we move forward, it will be crucial to balance innovation with 
                responsible development and deployment of AI systems.
                """
                st.session_state['text_input'] = example_text
                st.rerun()
    
    # Display results if available
    if 'last_response' in st.session_state and 'last_operation' in st.session_state:
        st.divider()
        display_results(st.session_state['last_response'], st.session_state['last_operation'])
        
        # Download results
        if st.button("📥 Download Results"):
            results_json = json.dumps(st.session_state['last_response'].dict(), indent=2)
            st.download_button(
                label="Download as JSON",
                data=results_json,
                file_name=f"ai_text_processing_results_{st.session_state['last_operation']}.json",
                mime="application/json"
            )

if __name__ == "__main__":
    # Load example text if set
    if 'example_text' in st.session_state:
        st.session_state['text_input'] = st.session_state['example_text']
        del st.session_state['example_text']
    
    main() 