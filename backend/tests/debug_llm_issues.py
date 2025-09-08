#!/usr/bin/env python3
"""Debug script to test LLM with problematic recall data patterns."""

import os
import logging
from llm_recall_parser import llm_parser

# Enable verbose logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_problematic_cases():
    """Test LLM with data patterns that might cause issues."""

    print("🔍 Testing LLM with Problematic Data Patterns")
    print("=" * 60)

    if not llm_parser.enabled:
        print("❌ LLM parser not enabled")
        return

    # Test cases that might cause issues
    problematic_cases = [
        {
            "name": "Empty String",
            "text": "",
            "expected_behavior": "Should fall back gracefully"
        },
        {
            "name": "Whitespace Only",
            "text": "   \n\t   ",
            "expected_behavior": "Should fall back gracefully"
        },
        {
            "name": "Very Short Text",
            "text": "recall",
            "expected_behavior": "Should handle minimal input"
        },
        {
            "name": "Special Characters",
            "text": "Product recall: ñ® ™ © § ¶ • – — ' ' " " … ‹ › « » ¡ ¿",
            "expected_behavior": "Should handle unicode characters"
        },
        {
            "name": "Very Long Text",
            "text": "Product recall notice. " * 500,  # Very long text
            "expected_behavior": "Should truncate and process"
        },
        {
            "name": "XML/HTML Content",
            "text": "<xml><item><title>Product Recall</title><description>Test recall</description></item></xml>",
            "expected_behavior": "Should extract meaningful info"
        },
        {
            "name": "Mixed Languages",
            "text": "Product recall / Rappel de produit / Llamada de producto",
            "expected_behavior": "Should handle multiple languages"
        },
        {
            "name": "Numbers and Dates",
            "text": "Recall #2024-001 dated 01/15/2024 for 10,000 units model ABC-123",
            "expected_behavior": "Should extract numbers and dates"
        }
    ]

    for i, case in enumerate(problematic_cases, 1):
        print(f"\n🧪 Test {i}: {case['name']}")
        print(f"Expected: {case['expected_behavior']}")
        print(f"Input length: {len(case['text'])} characters")

        if len(case['text']) <= 100:
            print(f"Input: '{case['text']}'")
        else:
            print(f"Input: '{case['text'][:100]}...'")

        print("-" * 40)

        try:
            result = llm_parser.parse_recall_text(case['text'], "TEST")

            if result:
                print(f"✅ Result: {result['product_name']} (confidence: {result['confidence']})")
            else:
                print("❌ No result returned")

        except Exception as e:
            print(f"❌ Error: {e}")
            logger.exception("Full error details:")

        print()

def test_real_recall_data():
    """Test with real recall data from database if available."""

    print("\n🔍 Testing with Real Database Recall Data")
    print("=" * 60)

    try:
        from database import SessionLocal
        from models import Recall

        db = SessionLocal()
        try:
            # Get a few recalls from database
            recalls = db.query(Recall).limit(3).all()

            if not recalls:
                print("No recalls found in database")
                return

            for recall in recalls:
                print(f"\nTesting Recall ID: {recall.id}")
                print(f"Source: {recall.source}")
                print(f"Current product: {recall.product_name}")

                # Test with details field
                if recall.details:
                    print(f"Details length: {len(recall.details)} characters")

                    try:
                        result = llm_parser.parse_recall_text(recall.details, recall.source)

                        if result:
                            print(f"✅ LLM parsed: {result['product_name']} by {result['brand']} (confidence: {result['confidence']})")
                        else:
                            print("❌ LLM parsing failed")

                    except Exception as e:
                        print(f"❌ Error parsing recall {recall.id}: {e}")
                        logger.exception("Full error details:")
                else:
                    print("No details field to test")

                print("-" * 40)

        finally:
            db.close()

    except ImportError:
        print("Database modules not available for testing")
    except Exception as e:
        print(f"Error accessing database: {e}")

if __name__ == "__main__":
    test_problematic_cases()
    test_real_recall_data()

    print("\n💡 If you see consistent failures:")
    print("1. Check your API key quota: https://makersuite.google.com/app/apikey")
    print("2. Try a new API key if quota is exceeded")
    print("3. Check internet connectivity")
    print("4. Review the logs above for specific error patterns")