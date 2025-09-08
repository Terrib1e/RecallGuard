#!/usr/bin/env python3
"""Script to reprocess existing CPSC recalls with improved parsing."""

import logging
from database import SessionLocal
from models import Recall
from recall_fetcher import recall_fetcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reprocess_cpsc_recalls():
    """Reprocess existing CPSC recalls with improved parsing."""

    db = SessionLocal()
    try:
        # Get all CPSC recalls that need reprocessing
        cpsc_recalls = db.query(Recall).filter(
            Recall.source == 'CPSC',
            Recall.product_name.in_(['Unknown Product', 'Consumer Product'])
        ).all()

        logger.info(f"Found {len(cpsc_recalls)} CPSC recalls to reprocess")

        updated_count = 0

        for i, recall in enumerate(cpsc_recalls, 1):
            try:
                # Get the description text from raw_data
                description_text = ''
                if recall.raw_data and 'description' in recall.raw_data:
                    description_text = recall.raw_data['description']
                elif recall.details:
                    description_text = recall.details

                if not description_text:
                    logger.warning(f"No description text found for recall {recall.id}")
                    continue

                # Extract improved product information
                new_product_name = recall_fetcher._extract_cpsc_product_name(description_text)
                new_brand = recall_fetcher._extract_cpsc_brand(description_text)
                new_date = recall_fetcher._extract_cpsc_date(description_text)

                # Update the recall if we got better information
                updated = False

                if new_product_name and new_product_name != 'Consumer Product':
                    recall.product_name = new_product_name
                    updated = True

                if new_brand:
                    recall.brand = new_brand
                    updated = True

                if new_date:
                    recall.recall_date = new_date
                    updated = True

                if updated:
                    updated_count += 1
                    logger.info(f"Updated recall {recall.id}: '{new_product_name}' by '{new_brand}'")

                # Progress indicator
                if i % 50 == 0:
                    logger.info(f"Processed {i}/{len(cpsc_recalls)} recalls...")
                    db.commit()  # Commit in batches

            except Exception as e:
                logger.error(f"Error processing recall {recall.id}: {e}")
                continue

        # Final commit
        db.commit()
        logger.info(f"✅ Reprocessing completed! Updated {updated_count} out of {len(cpsc_recalls)} recalls")

        # Show some examples of updated recalls
        updated_recalls = db.query(Recall).filter(
            Recall.source == 'CPSC',
            Recall.product_name != 'Consumer Product',
            Recall.product_name != 'Unknown Product'
        ).limit(5).all()

        logger.info("Sample updated recalls:")
        for recall in updated_recalls:
            logger.info(f"  - {recall.product_name} by {recall.brand or 'Unknown Brand'}")

    except Exception as e:
        logger.error(f"Error during reprocessing: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reprocess_cpsc_recalls()