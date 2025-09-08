#!/usr/bin/env python3
"""Test script for LLM recall parser."""

import os
import logging
from llm_recall_parser import llm_parser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_llm_parser():
    """Test the LLM recall parser with sample data."""

    print("🧠 Testing LLM Recall Parser...")
    print(f"LLM Enabled: {llm_parser.enabled}")

    if not llm_parser.enabled:
        print("❌ LLM parser not enabled. Please set GEMINI_API_KEY environment variable.")
        print("You can get a free API key from: https://makersuite.google.com/app/apikey")
        return

    # Test cases with different types of recall text
    test_cases = [
        {
            "name": "CPSC Hairdryer Recall",
            "text": "Hairdryers Recalled by Babyliss Pro NEWS from CPSC U.S. Consumer Product Safety Commission Office of Information and Public Affairs Washington, DC 20207 FOR IMMEDIATE RELEASE August 29, 2002 Release # 02-238 Hairdryer Recall Hotline: (800) 726-4202 CPSC Consumer Hotline: (800) 638-2772 CPSC Media Contact: Ken Giles, (301) 504-7052 CPSC, Babyliss Pro Announce Recall of Hairdryers",
            "source": "CPSC"
        },
        {
            "name": "FDA Food Recall",
            "text": "Voluntary recall of organic baby food pouches due to potential lead contamination. Product: Happy Baby Organic Baby Food Pouches, Stage 2. Brand: Happy Family Organics. Distributed nationwide. Consumers should stop using immediately.",
            "source": "FDA"
        },
        {
            "name": "NHTSA Vehicle Recall",
            "text": "2023 Honda Civic sedan vehicles recalled due to faulty airbag sensors. Model years 2022-2023 affected. Approximately 150,000 units. Contact Honda customer service for repair scheduling.",
            "source": "NHTSA"
        }
    ]

    print("\n" + "="*60)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['name']}")
        print(f"Source: {test_case['source']}")
        print(f"Input: {test_case['text'][:100]}...")
        print("-" * 40)

        try:
            # Parse with LLM
            result = llm_parser.parse_recall_text(test_case['text'], test_case['source'])

            if result:
                print(f"✅ Product: {result['product_name']}")
                print(f"✅ Brand: {result['brand']}")
                print(f"✅ Model: {result['model']}")
                print(f"✅ Category: {result['category']}")
                print(f"✅ Hazard: {result['hazard']}")
                print(f"✅ Date: {result['recall_date']}")
                print(f"✅ Affected Units: {result['affected_units']}")
                print(f"✅ Confidence: {result['confidence']}")
            else:
                print("❌ Failed to parse")

        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "="*60)
    print("🎉 LLM Parser testing completed!")

def test_batch_parsing():
    """Test batch parsing functionality."""

    if not llm_parser.enabled:
        print("❌ LLM parser not enabled for batch testing.")
        return

    print("\n🔄 Testing batch parsing...")

    # Sample recalls for batch processing
    sample_recalls = [
        {
            "id": 1,
            "source": "CPSC",
            "details": "Toy cars recalled due to choking hazard. Brand: Hot Wheels. Model: Speed Racers 2023. Approximately 50,000 units affected."
        },
        {
            "id": 2,
            "source": "FDA",
            "details": "Prescription medication recall. Drug: Lisinopril 10mg tablets. Manufacturer: Generic Pharma Inc. Lot numbers: ABC123, DEF456."
        }
    ]

    try:
        parsed_results = llm_parser.batch_parse_recalls(sample_recalls)

        print(f"✅ Batch processed {len(parsed_results)} recalls:")
        for result in parsed_results:
            print(f"  - {result['product_name']} by {result.get('brand', 'Unknown')}")

    except Exception as e:
        print(f"❌ Batch parsing error: {e}")

if __name__ == "__main__":
    test_llm_parser()
    test_batch_parsing()

    print("\n💡 To enable LLM parsing:")
    print("1. Get a free Gemini API key: https://makersuite.google.com/app/apikey")
    print("2. Set environment variable: export GEMINI_API_KEY='your-api-key'")
    print("3. Or add to .env file: GEMINI_API_KEY=your-api-key")