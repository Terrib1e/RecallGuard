#!/usr/bin/env python3
"""Script to populate the database with initial recall data."""

import asyncio
import logging
from datetime import datetime
from recall_fetcher import recall_fetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to populate recalls."""
    logger.info("Starting recall population script...")

    try:
        # Fetch and store recalls from the last 30 days
        logger.info("Fetching recalls from the last 30 days...")
        stats = await recall_fetcher.fetch_and_store_recalls(days_back=30)

        logger.info("Recall population completed!")
        logger.info(f"Statistics:")
        logger.info(f"  - Total fetched: {stats['total_fetched']}")
        logger.info(f"  - New recalls: {stats['new_recalls']}")
        logger.info(f"  - Updated recalls: {stats['updated_recalls']}")
        logger.info(f"  - FDA Food recalls: {stats['fda_food_recalls']}")
        logger.info(f"  - FDA Drug recalls: {stats['fda_drug_recalls']}")
        logger.info(f"  - FDA Device recalls: {stats['fda_device_recalls']}")
        logger.info(f"  - CPSC recalls: {stats['cpsc_recalls']}")
        logger.info(f"  - NHTSA recalls: {stats['nhtsa_recalls']}")
        logger.info(f"  - USDA recalls: {stats['usda_recalls']}")

        if stats['new_recalls'] > 0:
            logger.info(f"Successfully added {stats['new_recalls']} new recalls to the database!")
        else:
            logger.info("No new recalls found (database may already be up to date)")

    except Exception as e:
        logger.error(f"Error during recall population: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)