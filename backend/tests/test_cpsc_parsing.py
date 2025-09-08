#!/usr/bin/env python3
"""Test script for CPSC parsing functions."""

from recall_fetcher import recall_fetcher

def test_cpsc_parsing():
    """Test the CPSC text parsing functions."""

    # Test case from the actual database
    test_text = "Hairdryers Recalled by Babyliss Pro NEWS from CPSC U.S. Consumer Product Safety Commission Office of Information and Public Affairs Washington, DC 20207 FOR IMMEDIATE RELEASE August 29, 2002 Release # 02-238 Hairdryer Recall Hotline: (800) 726-4202 CPSC Consumer Hotline: (800) 638-2772 CPSC Media Contact: Ken Giles, (301) 504-7052 CPSC, Babyliss Pro Announce Recall of Hairdryers"

    print("Testing CPSC parsing functions...")
    print(f"Input text: {test_text[:100]}...")
    print()

    # Test product name extraction
    product = recall_fetcher._extract_cpsc_product_name(test_text)
    print(f"Extracted Product: '{product}'")

    # Test brand extraction
    brand = recall_fetcher._extract_cpsc_brand(test_text)
    print(f"Extracted Brand: '{brand}'")

    # Test date extraction
    date = recall_fetcher._extract_cpsc_date(test_text)
    print(f"Extracted Date: {date}")

    print()
    print("✅ CPSC parsing test completed!")

if __name__ == "__main__":
    test_cpsc_parsing()