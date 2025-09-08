#!/usr/bin/env python3
"""Migration script to enhance the existing recalls table with new columns."""

import logging
from sqlalchemy import text
from database import engine, SessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_recalls_table():
    """Add new columns to existing recalls table."""

    # SQL commands to add new columns
    migration_commands = [
        # Add source column (FDA, CPSC, etc.)
        "ALTER TABLE recalls ADD COLUMN IF NOT EXISTS source VARCHAR DEFAULT 'UNKNOWN'",

        # Add source_id column (unique ID from source)
        "ALTER TABLE recalls ADD COLUMN IF NOT EXISTS source_id VARCHAR",

        # Add category column (food, drug, consumer_product)
        "ALTER TABLE recalls ADD COLUMN IF NOT EXISTS category VARCHAR",

        # Add raw_data column (JSON field for original API response)
        "ALTER TABLE recalls ADD COLUMN IF NOT EXISTS raw_data JSON",

        # Add processed column (boolean to track if recall has been processed for alerts)
        "ALTER TABLE recalls ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE",

        # Add created_at timestamp
        "ALTER TABLE recalls ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",

        # Add updated_at timestamp
        "ALTER TABLE recalls ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",

        # Create indexes for better performance
        "CREATE INDEX IF NOT EXISTS idx_recalls_source ON recalls(source)",
        "CREATE INDEX IF NOT EXISTS idx_recalls_source_id ON recalls(source_id)",
        "CREATE INDEX IF NOT EXISTS idx_recalls_category ON recalls(category)",
        "CREATE INDEX IF NOT EXISTS idx_recalls_processed ON recalls(processed)",
        "CREATE INDEX IF NOT EXISTS idx_recalls_recall_date ON recalls(recall_date)",
        "CREATE INDEX IF NOT EXISTS idx_recalls_product_name ON recalls(product_name)",
        "CREATE INDEX IF NOT EXISTS idx_recalls_brand ON recalls(brand)",
    ]

    db = SessionLocal()
    try:
        logger.info("Starting recalls table migration...")

        for i, command in enumerate(migration_commands, 1):
            try:
                logger.info(f"Executing migration step {i}/{len(migration_commands)}: {command[:50]}...")
                db.execute(text(command))
                db.commit()
                logger.info(f"✓ Step {i} completed successfully")
            except Exception as e:
                logger.warning(f"Step {i} failed (may already exist): {e}")
                db.rollback()

        # Update existing records to have default values
        logger.info("Updating existing records with default values...")

        # Set source to 'LEGACY' for existing records without a source
        update_commands = [
            "UPDATE recalls SET source = 'LEGACY' WHERE source IS NULL OR source = 'UNKNOWN'",
            "UPDATE recalls SET processed = FALSE WHERE processed IS NULL",
            "UPDATE recalls SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL",
            "UPDATE recalls SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL",
        ]

        for command in update_commands:
            try:
                result = db.execute(text(command))
                db.commit()
                logger.info(f"✓ Updated {result.rowcount} records: {command[:50]}...")
            except Exception as e:
                logger.warning(f"Update failed: {e}")
                db.rollback()

        logger.info("Migration completed successfully!")

        # Show final table structure
        result = db.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'recalls' ORDER BY ordinal_position"))
        columns = result.fetchall()

        logger.info("Final recalls table structure:")
        for col in columns:
            logger.info(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_recalls_table()
    print("Migration completed! Your recalls table now supports the enhanced recall system.")