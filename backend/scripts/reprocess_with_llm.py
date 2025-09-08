#!/usr/bin/env python3
"""Script to reprocess existing recalls using LLM-enhanced parsing."""

import logging
from database import SessionLocal
from models import Recall
from llm_recall_parser import llm_parser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reprocess_recalls_with_llm():
    """Reprocess existing recalls using LLM for better accuracy."""

    db = SessionLocal()
    try:
        # Get all recalls that could benefit from LLM processing
        recalls_to_process = db.query(Recall).filter(
            # Focus on CPSC recalls with poor parsing
            ((Recall.source == 'CPSC') &
             (Recall.product_name.in_(['Unknown Product', 'Consumer Product', 'involves', 'Hotline']))) |
            # Or any recall with generic product names
            (Recall.product_name.like('%involves%')) |
            (Recall.product_name.like('%Hotline%')) |
            (Recall.product_name.like('%This%'))
        ).limit(100).all()  # Process in batches

        logger.info(f"Found {len(recalls_to_process)} recalls to reprocess with LLM")

        if not llm_parser.enabled:
            logger.warning("LLM parser not enabled. Will use improved manual parsing.")
        else:
            logger.info("Using LLM-enhanced parsing for better accuracy")

        updated_count = 0
        skipped_count = 0

        for i, recall in enumerate(recalls_to_process, 1):
            try:
                # Get the text to parse
                text_to_parse = ''
                if recall.details:
                    text_to_parse = recall.details
                elif recall.raw_data and isinstance(recall.raw_data, dict):
                    if 'description' in recall.raw_data:
                        text_to_parse = recall.raw_data['description']
                    elif 'xml_data' in recall.raw_data:
                        text_to_parse = recall.raw_data['xml_data']

                if not text_to_parse:
                    logger.warning(f"No text found for recall {recall.id}")
                    skipped_count += 1
                    continue

                # Parse with LLM or fallback
                if llm_parser.enabled:
                    parsed_data = llm_parser.parse_recall_text(text_to_parse, recall.source)
                else:
                    # Use improved manual parsing
                    parsed_data = llm_parser._fallback_parse(text_to_parse, recall.source)

                if not parsed_data:
                    logger.warning(f"Failed to parse recall {recall.id}")
                    skipped_count += 1
                    continue

                # Update the recall if we got better information
                updated = False
                old_product_name = recall.product_name

                # Update product name if it's better
                if (parsed_data['product_name'] and
                    parsed_data['product_name'] != 'Consumer Product' and
                    parsed_data['product_name'] != old_product_name):
                    recall.product_name = parsed_data['product_name']
                    updated = True

                # Update brand if we found one
                if parsed_data['brand'] and not recall.brand:
                    recall.brand = parsed_data['brand']
                    updated = True

                # Update model if we found one
                if parsed_data['model'] and not recall.model:
                    recall.model = parsed_data['model']
                    updated = True

                # Update category if we have a better one
                if (parsed_data['category'] and
                    parsed_data['category'] != 'consumer_product' and
                    not recall.category):
                    recall.category = parsed_data['category']
                    updated = True

                # Update recall date if LLM found a better one
                if parsed_data.get('recall_date') and not recall.recall_date:
                    recall.recall_date = parsed_data['recall_date']
                    updated = True

                # Store LLM metadata in raw_data
                if llm_parser.enabled and updated:
                    if not recall.raw_data:
                        recall.raw_data = {}
                    recall.raw_data.update({
                        'llm_confidence': parsed_data.get('confidence'),
                        'llm_hazard': parsed_data.get('hazard'),
                        'llm_affected_units': parsed_data.get('affected_units'),
                        'llm_processed': True
                    })

                if updated:
                    updated_count += 1
                    confidence_indicator = f" (confidence: {parsed_data.get('confidence', 'unknown')})" if llm_parser.enabled else ""
                    logger.info(f"Updated recall {recall.id}: '{old_product_name}' → '{recall.product_name}' by '{recall.brand or 'Unknown'}'{confidence_indicator}")

                # Progress indicator
                if i % 25 == 0:
                    logger.info(f"Processed {i}/{len(recalls_to_process)} recalls... ({updated_count} updated, {skipped_count} skipped)")
                    db.commit()  # Commit in batches

            except Exception as e:
                logger.error(f"Error processing recall {recall.id}: {e}")
                skipped_count += 1
                continue

        # Final commit
        db.commit()
        logger.info(f"✅ LLM reprocessing completed!")
        logger.info(f"📊 Results: {updated_count} updated, {skipped_count} skipped out of {len(recalls_to_process)} processed")

        # Show some examples of updated recalls
        if updated_count > 0:
            updated_recalls = db.query(Recall).filter(
                Recall.product_name != 'Consumer Product',
                Recall.product_name != 'Unknown Product'
            ).order_by(Recall.updated_at.desc()).limit(5).all()

            logger.info("Sample updated recalls:")
            for recall in updated_recalls:
                confidence = ""
                if recall.raw_data and recall.raw_data.get('llm_confidence'):
                    confidence = f" (confidence: {recall.raw_data['llm_confidence']})"
                logger.info(f"  - {recall.product_name} by {recall.brand or 'Unknown Brand'} [{recall.source}]{confidence}")

    except Exception as e:
        logger.error(f"Error during LLM reprocessing: {e}")
        db.rollback()
    finally:
        db.close()

def show_parsing_comparison():
    """Show before/after comparison of parsing results."""

    db = SessionLocal()
    try:
        # Get a sample of recalls for comparison
        sample_recalls = db.query(Recall).filter(
            Recall.source == 'CPSC'
        ).limit(3).all()

        logger.info("🔍 Parsing Comparison Examples:")
        logger.info("=" * 60)

        for recall in sample_recalls:
            logger.info(f"\nRecall ID: {recall.id}")
            logger.info(f"Current Product: {recall.product_name}")
            logger.info(f"Current Brand: {recall.brand}")

            # Get text to parse
            text_to_parse = recall.details or (recall.raw_data.get('description', '') if recall.raw_data else '')

            if text_to_parse and len(text_to_parse) > 50:
                logger.info(f"Text sample: {text_to_parse[:100]}...")

                # Show what LLM would extract
                if llm_parser.enabled:
                    parsed = llm_parser.parse_recall_text(text_to_parse, recall.source)
                    if parsed:
                        logger.info(f"LLM would extract:")
                        logger.info(f"  Product: {parsed['product_name']}")
                        logger.info(f"  Brand: {parsed['brand']}")
                        logger.info(f"  Category: {parsed['category']}")
                        logger.info(f"  Confidence: {parsed['confidence']}")
                else:
                    logger.info("LLM not available for comparison")

            logger.info("-" * 40)

    finally:
        db.close()

if __name__ == "__main__":
    logger.info("🧠 Starting LLM-enhanced recall reprocessing...")

    if llm_parser.enabled:
        logger.info("✅ LLM parser is enabled - using Gemini for intelligent extraction")
    else:
        logger.info("⚠️ LLM parser not enabled - using improved manual parsing")
        logger.info("💡 To enable LLM: Set GEMINI_API_KEY environment variable")
        logger.info("🔗 Get free API key: https://makersuite.google.com/app/apikey")

    # Show comparison first
    show_parsing_comparison()

    # Ask for confirmation
    print("\n" + "="*60)
    response = input("Proceed with reprocessing? (y/N): ").strip().lower()

    if response in ['y', 'yes']:
        reprocess_recalls_with_llm()
    else:
        logger.info("Reprocessing cancelled by user")