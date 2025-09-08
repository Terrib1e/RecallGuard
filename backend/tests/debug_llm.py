#!/usr/bin/env python3
"""Debug script for LLM recall parser issues."""

import os
import logging
from llm_recall_parser import llm_parser

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_llm_connection():
    """Debug LLM connection and basic functionality."""

    print("🔍 LLM Debug Script")
    print("=" * 50)

    # Check API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("💡 Set your API key: export GEMINI_API_KEY='your-key-here'")
        return

    print(f"✅ API key found: {api_key[:8]}...")
    print(f"✅ LLM Parser enabled: {llm_parser.enabled}")

    if not llm_parser.enabled:
        print("❌ LLM parser failed to initialize")
        return

    # Test with simple text
    print("\n🧪 Testing with simple recall text...")

    simple_text = """
    PRODUCT RECALL NOTICE
    Product: Wireless Bluetooth Headphones
    Brand: TechAudio
    Model: TA-500
    Issue: Battery overheating risk
    Date: January 15, 2024
    Units: 10,000
    """

    try:
        print("Sending request to Gemini API...")
        result = llm_parser.parse_recall_text(simple_text, "TEST")

        if result:
            print("✅ Parsing successful!")
            print(f"Product: {result['product_name']}")
            print(f"Brand: {result['brand']}")
            print(f"Confidence: {result['confidence']}")
        else:
            print("❌ Parsing returned None")

    except Exception as e:
        print(f"❌ Error during parsing: {e}")
        logger.exception("Full error details:")

def test_api_directly():
    """Test Gemini API directly to isolate issues."""

    print("\n🔧 Direct API Test")
    print("-" * 30)

    try:
        import google.generativeai as genai

        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ No API key for direct test")
            return

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Very simple test
        response = model.generate_content("Say hello in JSON format: {\"message\": \"hello\"}")

        print(f"Response object: {type(response)}")
        print(f"Has text attribute: {hasattr(response, 'text')}")

        if hasattr(response, 'text'):
            print(f"Response text: {response.text}")

        if hasattr(response, 'candidates'):
            print(f"Candidates count: {len(response.candidates) if response.candidates else 0}")

    except Exception as e:
        print(f"❌ Direct API test failed: {e}")
        logger.exception("Direct API error:")

if __name__ == "__main__":
    debug_llm_connection()
    test_api_directly()

    print("\n💡 Troubleshooting Tips:")
    print("1. Check your internet connection")
    print("2. Verify API key is correct")
    print("3. Check if you've exceeded API quota")
    print("4. Try regenerating your API key")
    print("5. Check Google AI Studio: https://makersuite.google.com/")