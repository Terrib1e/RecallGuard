#!/usr/bin/env python3
"""Script to create the recall_alerts table."""

import logging
from sqlalchemy import text
from database import SessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_recall_alerts_table():
    """Create the recall_alerts table if it doesn't exist."""

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS recall_alerts (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        recall_id INTEGER NOT NULL REFERENCES recalls(id) ON DELETE CASCADE,
        product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        match_score INTEGER NOT NULL CHECK (match_score >= 0 AND match_score <= 100),
        confidence VARCHAR NOT NULL CHECK (confidence IN ('high', 'medium', 'low')),
        match_details JSON,
        notification_sent BOOLEAN DEFAULT FALSE,
        notification_sent_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        -- Ensure unique alerts per user/recall/product combination
        UNIQUE(user_id, recall_id, product_id)
    );
    """

    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_recall_alerts_user_id ON recall_alerts(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_recall_alerts_recall_id ON recall_alerts(recall_id)",
        "CREATE INDEX IF NOT EXISTS idx_recall_alerts_product_id ON recall_alerts(product_id)",
        "CREATE INDEX IF NOT EXISTS idx_recall_alerts_confidence ON recall_alerts(confidence)",
        "CREATE INDEX IF NOT EXISTS idx_recall_alerts_notification_sent ON recall_alerts(notification_sent)",
        "CREATE INDEX IF NOT EXISTS idx_recall_alerts_created_at ON recall_alerts(created_at)",
    ]

    db = SessionLocal()
    try:
        logger.info("Creating recall_alerts table...")

        # Create the table
        db.execute(text(create_table_sql))
        db.commit()
        logger.info("✓ recall_alerts table created successfully")

        # Create indexes
        for i, index_sql in enumerate(create_indexes_sql, 1):
            try:
                logger.info(f"Creating index {i}/{len(create_indexes_sql)}...")
                db.execute(text(index_sql))
                db.commit()
                logger.info(f"✓ Index {i} created successfully")
            except Exception as e:
                logger.warning(f"Index {i} creation failed (may already exist): {e}")
                db.rollback()

        logger.info("recall_alerts table setup completed!")

        # Show table structure
        result = db.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'recall_alerts' ORDER BY ordinal_position"))
        columns = result.fetchall()

        logger.info("recall_alerts table structure:")
        for col in columns:
            logger.info(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")

    except Exception as e:
        logger.error(f"Table creation failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_recall_alerts_table()
    print("recall_alerts table created successfully!")