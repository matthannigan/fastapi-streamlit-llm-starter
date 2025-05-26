#!/usr/bin/env python3
"""
Example of how to add custom text processing operations to the FastAPI-Streamlit-LLM Starter Template.

This script demonstrates the step-by-step process of extending the application
with new operations like translation and text classification using standardized
patterns for imports, error handling, and sample data.
"""

# Standard library imports
import asyncio
import logging
from enum import Enum
from typing import Dict, Any, List, Optional

# Third-party imports
import httpx

# Local application imports
from shared.sample_data import get_sample_text, get_medium_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This example shows how to extend the existing ProcessingOperation enum
# In practice, you would modify the actual files as shown below

class ExtendedProcessingOperation(str, Enum):
    """Extended processing operations including custom ones."""
    # Existing operations
    SUMMARIZE = "summarize"
    SENTIMENT = "sentiment"
    KEY_POINTS = "key_points"
    QUESTIONS = "questions"
    QA = "qa"
    
    # New custom operations
    TRANSLATE = "translate"
    CLASSIFY = "classify"
    EXTRACT_ENTITIES = "extract_entities"
    READABILITY = "readability"

def print_step(step_num: int, title: str):
    """Print a formatted step header."""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {title}")
    print(f"{'='*60}")

def print_code_block(title: str, code: str):
    """Print a formatted code block."""
    print(f"\n📝 {title}:")
    print("```python")
    print(code)
    print("```")

def show_file_modifications():
    """Show the required file modifications to add custom operations."""
    
    print("🚀 Adding Custom Operations to FastAPI-Streamlit-LLM Starter Template")
    print("=" * 80)
    
    # Step 1: Modify shared models
    print_step(1, "Extend ProcessingOperation Enum in shared/models.py")
    
    models_code = '''
# Add new operations to the existing enum
class ProcessingOperation(str, Enum):
    """Available text processing operations."""
    SUMMARIZE = "summarize"
    SENTIMENT = "sentiment"
    KEY_POINTS = "key_points"
    QUESTIONS = "questions"
    QA = "qa"
    
    # New custom operations
    TRANSLATE = "translate"
    CLASSIFY = "classify"
    EXTRACT_ENTITIES = "extract_entities"
    READABILITY = "readability"

# Add new request validation for translation
class TextProcessingRequest(BaseModel):
    # ... existing fields ...
    
    @field_validator('options')
    @classmethod
    def validate_translation_options(cls, v, info):
        """Validate translation-specific options."""
        operation = info.data.get('operation')
        if operation == ProcessingOperation.TRANSLATE:
            if not v.get('target_language'):
                raise ValueError('target_language is required for translation')
        return v
'''
    
    print_code_block("shared/models.py modifications", models_code)
    
    # Step 2: Add backend processing methods
    print_step(2, "Add Processing Methods in backend/app/services/text_processor.py")
    
    processor_code = '''
class TextProcessor:
    # ... existing methods ...
    
    async def _translate_text(self, text: str, options: Dict[str, Any]) -> str:
        """Translate text to target language."""
        target_language = options.get("target_language", "Spanish")
        
        prompt = f"""
        Translate the following text to {target_language}. 
        Maintain the original meaning and tone.
        
        Text to translate: {text}
        
        Translation:
        """
        
        result = await self.agent.run(prompt)
        return result.output.strip()
    
    async def _classify_text(self, text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Classify text into predefined categories."""
        categories = options.get("categories", [
            "News", "Opinion", "Technical", "Educational", "Entertainment"
        ])
        
        prompt = f"""
        Classify the following text into one of these categories: {', '.join(categories)}
        
        Text: {text}
        
        Provide your response as a JSON object with:
        - "category": the selected category
        - "confidence": confidence score (0-1)
        - "reasoning": brief explanation
        
        Response:
        """
        
        result = await self.agent.run(prompt)
        try:
            import json
            return json.loads(result.output.strip())
        except:
            return {
                "category": categories[0],
                "confidence": 0.5,
                "reasoning": "Could not parse classification result"
            }
    
    async def _extract_entities(self, text: str, options: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract named entities from text."""
        entity_types = options.get("entity_types", [
            "PERSON", "ORGANIZATION", "LOCATION", "DATE", "MONEY"
        ])
        
        prompt = f"""
        Extract named entities from the following text. 
        Focus on these types: {', '.join(entity_types)}
        
        Text: {text}
        
        Return a JSON list of entities with format:
        [{"text": "entity", "type": "TYPE", "context": "surrounding context"}]
        
        Entities:
        """
        
        result = await self.agent.run(prompt)
        try:
            import json
            return json.loads(result.output.strip())
        except:
            return []
    
    async def _analyze_readability(self, text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze text readability and complexity."""
        
        prompt = f"""
        Analyze the readability and complexity of this text:
        
        Text: {text}
        
        Provide analysis as JSON with:
        - "reading_level": estimated grade level (e.g., "8th grade")
        - "complexity": "low", "medium", or "high"
        - "avg_sentence_length": estimated average sentence length
        - "difficult_words": number of potentially difficult words
        - "suggestions": list of improvement suggestions
        
        Analysis:
        """
        
        result = await self.agent.run(prompt)
        try:
            import json
            return json.loads(result.output.strip())
        except:
            return {
                "reading_level": "Unknown",
                "complexity": "medium",
                "avg_sentence_length": 15,
                "difficult_words": 0,
                "suggestions": []
            }
    
    async def process_text(self, request: TextProcessingRequest) -> TextProcessingResponse:
        """Enhanced process_text method with custom operations."""
        start_time = time.time()
        
        try:
            # ... existing operation handling ...
            
            # Add new custom operations
            elif request.operation == ProcessingOperation.TRANSLATE:
                result = await self._translate_text(request.text, request.options)
                
            elif request.operation == ProcessingOperation.CLASSIFY:
                classification = await self._classify_text(request.text, request.options)
                result = classification.get("category", "Unknown")
                metadata.update(classification)
                
            elif request.operation == ProcessingOperation.EXTRACT_ENTITIES:
                entities = await self._extract_entities(request.text, request.options)
                result = f"Found {len(entities)} entities"
                metadata["entities"] = entities
                
            elif request.operation == ProcessingOperation.READABILITY:
                readability = await self._analyze_readability(request.text, request.options)
                result = f"Reading level: {readability.get('reading_level', 'Unknown')}"
                metadata.update(readability)
            
            # ... rest of existing code ...
'''
    
    print_code_block("backend/app/services/text_processor.py modifications", processor_code)
    
    # Step 3: Update API endpoints
    print_step(3, "Update Operations Endpoint in backend/app/main.py")
    
    api_code = '''
@app.get("/operations")
async def get_operations():
    """Get available processing operations with custom ones."""
    return {
        "operations": [
            # ... existing operations ...
            {
                "id": "translate",
                "name": "Translate",
                "description": "Translate text to another language",
                "options": ["target_language"],
                "example_options": {
                    "target_language": "Spanish"
                }
            },
            {
                "id": "classify",
                "name": "Classify",
                "description": "Classify text into categories",
                "options": ["categories"],
                "example_options": {
                    "categories": ["News", "Opinion", "Technical"]
                }
            },
            {
                "id": "extract_entities",
                "name": "Extract Entities",
                "description": "Extract named entities from text",
                "options": ["entity_types"],
                "example_options": {
                    "entity_types": ["PERSON", "ORGANIZATION", "LOCATION"]
                }
            },
            {
                "id": "readability",
                "name": "Readability Analysis",
                "description": "Analyze text readability and complexity",
                "options": [],
                "example_options": {}
            }
        ]
    }
'''
    
    print_code_block("backend/app/main.py modifications", api_code)
    
    # Step 4: Update frontend UI
    print_step(4, "Enhance Frontend UI in frontend/app/app.py")
    
    frontend_code = '''
def create_operation_options(operation: str) -> Dict[str, Any]:
    """Create operation-specific options UI."""
    options = {}
    
    if operation == "translate":
        options["target_language"] = st.selectbox(
            "Target Language",
            ["Spanish", "French", "German", "Italian", "Portuguese", 
             "Chinese", "Japanese", "Arabic", "Russian"],
            key="target_language"
        )
    
    elif operation == "classify":
        default_categories = ["News", "Opinion", "Technical", "Educational", "Entertainment"]
        categories = st.multiselect(
            "Classification Categories",
            default_categories,
            default=default_categories[:3],
            key="categories"
        )
        if categories:
            options["categories"] = categories
    
    elif operation == "extract_entities":
        default_entities = ["PERSON", "ORGANIZATION", "LOCATION", "DATE", "MONEY"]
        entity_types = st.multiselect(
            "Entity Types to Extract",
            default_entities,
            default=default_entities[:3],
            key="entity_types"
        )
        if entity_types:
            options["entity_types"] = entity_types
    
    # ... existing options handling ...
    
    return options

def display_custom_results(result: Dict[str, Any], operation: str):
    """Display results for custom operations."""
    
    if operation == "translate":
        st.success("Translation completed!")
        st.write("**Translated Text:**")
        st.write(result.get("result", ""))
    
    elif operation == "classify":
        metadata = result.get("metadata", {})
        st.success(f"Text classified as: **{result.get('result', 'Unknown')}**")
        
        if "confidence" in metadata:
            st.metric("Confidence", f"{metadata['confidence']:.1%}")
        
        if "reasoning" in metadata:
            st.write("**Reasoning:**", metadata["reasoning"])
    
    elif operation == "extract_entities":
        metadata = result.get("metadata", {})
        entities = metadata.get("entities", [])
        
        st.success(f"Found {len(entities)} entities")
        
        if entities:
            for entity in entities:
                with st.expander(f"{entity.get('text', '')} ({entity.get('type', '')})"):
                    st.write("**Context:**", entity.get('context', 'N/A'))
    
    elif operation == "readability":
        metadata = result.get("metadata", {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Reading Level", metadata.get("reading_level", "Unknown"))
        with col2:
            st.metric("Complexity", metadata.get("complexity", "Unknown"))
        with col3:
            st.metric("Avg Sentence Length", metadata.get("avg_sentence_length", 0))
        
        suggestions = metadata.get("suggestions", [])
        if suggestions:
            st.write("**Improvement Suggestions:**")
            for suggestion in suggestions:
                st.write(f"• {suggestion}")
'''
    
    print_code_block("frontend/app/app.py modifications", frontend_code)

async def test_custom_operations():
    """Test the custom operations (simulated)."""
    
    print_step(5, "Testing Custom Operations")
    
    # Use standardized sample text for testing
    sample_text = get_sample_text("ai_technology")
    
    print("📖 Sample text for testing:")
    print(f'"{sample_text}"')
    
    # Simulate API calls (in real implementation, these would be actual HTTP requests)
    test_cases = [
        {
            "operation": "translate",
            "options": {"target_language": "Spanish"},
            "expected": "Translation to Spanish"
        },
        {
            "operation": "classify",
            "options": {"categories": ["Technology", "Healthcare", "Business"]},
            "expected": "Classification as Technology/Healthcare"
        },
        {
            "operation": "extract_entities",
            "options": {"entity_types": ["ORGANIZATION", "TECHNOLOGY"]},
            "expected": "Entities: Google, Microsoft, AI"
        },
        {
            "operation": "readability",
            "options": {},
            "expected": "Readability analysis with grade level"
        }
    ]
    
    print("\n🧪 Test Cases:")
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Operation: {test['operation']}")
        print(f"   Options: {test['options']}")
        print(f"   Expected: {test['expected']}")
        print(f"   Status: ✅ Ready for implementation")

def show_deployment_checklist():
    """Show checklist for deploying custom operations."""
    
    print_step(6, "Deployment Checklist")
    
    checklist = [
        "✅ Update shared/models.py with new enum values",
        "✅ Add processing methods to text_processor.py",
        "✅ Update /operations endpoint in main.py",
        "✅ Enhance frontend UI components",
        "✅ Add validation for new operation options",
        "✅ Update API documentation",
        "✅ Add unit tests for new operations",
        "✅ Test integration with frontend",
        "✅ Update README with new features",
        "✅ Deploy and monitor performance"
    ]
    
    print("\n📋 Deployment Checklist:")
    for item in checklist:
        print(f"   {item}")
    
    print("\n💡 Pro Tips:")
    print("   • Test each operation individually before integration")
    print("   • Add proper error handling for AI model failures")
    print("   • Consider rate limiting for expensive operations")
    print("   • Monitor token usage for cost optimization")
    print("   • Add caching for frequently requested operations")

def show_advanced_examples():
    """Show advanced customization examples."""
    
    print_step(7, "Advanced Customization Examples")
    
    advanced_code = '''
# Example 1: Operation with external API integration
async def _detect_language(self, text: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Detect language using external service."""
    # Could integrate with Google Translate API, Azure Cognitive Services, etc.
    
    prompt = f"""
    Detect the language of this text and provide confidence score:
    
    Text: {text}
    
    Return JSON: {{"language": "language_name", "code": "ISO_code", "confidence": 0.95}}
    """
    
    result = await self.agent.run(prompt)
    # Parse and return structured result
    
# Example 2: Batch operation processing
async def _batch_summarize(self, texts: List[str], options: Dict[str, Any]) -> List[str]:
    """Process multiple texts efficiently."""
    summaries = []
    
    for text in texts:
        summary = await self._summarize_text(text, options)
        summaries.append(summary)
    
    return summaries

# Example 3: Operation with file upload support
async def _analyze_document(self, file_content: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze uploaded document."""
    # Extract text from PDF, DOCX, etc.
    # Then apply text processing operations
    
    text = extract_text_from_file(file_content)
    analysis = await self._comprehensive_analysis(text, options)
    
    return analysis
'''
    
    print_code_block("Advanced customization examples", advanced_code)

async def main():
    """Main function demonstrating custom operation integration."""
    
    print("🎯 FastAPI-Streamlit-LLM Starter Template - Custom Operations Guide")
    print("=" * 80)
    print("This guide shows how to extend the template with custom text processing operations.")
    print("\n📚 What you'll learn:")
    print("   • How to add new processing operations")
    print("   • Backend and frontend integration")
    print("   • Testing and deployment strategies")
    print("   • Advanced customization techniques")
    
    try:
        # Show the step-by-step process
        show_file_modifications()
        await test_custom_operations()
        show_deployment_checklist()
        show_advanced_examples()
        
        print("\n" + "="*80)
        print("🎉 Custom Operations Integration Guide Complete!")
        print("="*80)
        print("\n💡 Next Steps:")
        print("   1. Choose which custom operations to implement")
        print("   2. Follow the file modification steps above")
        print("   3. Test each operation thoroughly")
        print("   4. Deploy and monitor performance")
        print("\n📖 Additional Resources:")
        print("   • Check the main README.md for setup instructions")
        print("   • Review existing operations in text_processor.py")
        print("   • Test with basic_usage.py after implementation")
        
    except Exception as e:
        print(f"\n❌ Error in demonstration: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 