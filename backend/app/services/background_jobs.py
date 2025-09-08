"""Background job system for RecallGuard."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.models import User, Product, Recall, RecallAlert
from app.services.recall_fetcher import recall_fetcher
from app.services.ai_matcher import ai_matcher
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

class BackgroundJobManager:
    """Manages background jobs for recall monitoring."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    def start(self):
        """Start the background job scheduler."""
        if not self.is_running:
            # Schedule recall scraping job to run every 4 hours
            self.scheduler.add_job(
                self.scrape_recalls_job,
                CronTrigger(hour="*/4"),  # Every 4 hours
                id="scrape_recalls",
                name="Scrape and store new recalls",
                max_instances=1,
                misfire_grace_time=3600  # 1 hour grace time
            )

            # Schedule recall checking job to run every 6 hours (offset from scraping)
            self.scheduler.add_job(
                self.check_recalls_job,
                CronTrigger(hour="2,8,14,20"),  # 2 AM, 8 AM, 2 PM, 8 PM
                id="check_recalls",
                name="Check for new recalls and notify users",
                max_instances=1,
                misfire_grace_time=3600  # 1 hour grace time
            )

            # Schedule daily summary job
            self.scheduler.add_job(
                self.daily_summary_job,
                CronTrigger(hour=9, minute=0),  # 9 AM daily
                id="daily_summary",
                name="Send daily summary to active users",
                max_instances=1
            )

            # Schedule weekly cleanup job
            self.scheduler.add_job(
                self.cleanup_job,
                CronTrigger(day_of_week="sun", hour=2, minute=0),  # Sunday 2 AM
                id="weekly_cleanup",
                name="Clean up old data",
                max_instances=1
            )

            self.scheduler.start()
            self.is_running = True
            logger.info("Background job scheduler started with 4 jobs")

    def stop(self):
        """Stop the background job scheduler."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Background job scheduler stopped")

    async def scrape_recalls_job(self):
        """Job to scrape and store recalls in database."""
        logger.info("Starting recall scraping job...")

        try:
            # Fetch and store recalls from all sources
            stats = await recall_fetcher.fetch_and_store_recalls(days_back=7)

            logger.info(f"Recall scraping completed: {stats['new_recalls']} new recalls, "
                       f"{stats['updated_recalls']} updated recalls from {stats['total_fetched']} total fetched")

        except Exception as e:
            logger.error(f"Error in recall scraping job: {e}")

    async def check_recalls_job(self):
        """Main job to check for recalls and notify users."""
        logger.info("Starting recall check job...")

        try:
            # Step 1: Get unprocessed recalls from database
            logger.info("Getting unprocessed recalls from database...")
            recalls = await recall_fetcher.get_unprocessed_recalls(limit=500)
            logger.info(f"Found {len(recalls)} unprocessed recalls")

            if not recalls:
                logger.info("No unprocessed recalls found")
                return

            # Step 2: Get all users and their products
            db = SessionLocal()
            try:
                users_with_products = await self._get_users_with_products(db)
                logger.info(f"Processing {len(users_with_products)} users")

                # Step 3: Process each user
                total_matches = 0
                total_notifications = 0
                processed_recall_ids = set()

                for user_data in users_with_products:
                    user = user_data['user']
                    products = user_data['products']

                    if not products:
                        continue

                    # Convert products to dict format for AI matcher
                    product_dicts = [
                        {
                            'id': p.id,
                            'product_name': p.product_name,
                            'brand': p.brand,
                            'model': p.model
                        }
                        for p in products
                    ]

                    # Step 4: Find matches using AI
                    matches = ai_matcher.find_matches(product_dicts, recalls)

                    if matches:
                        total_matches += len(matches)
                        logger.info(f"Found {len(matches)} matches for user {user.email}")

                        # Step 5: Store recall alerts in database
                        alert_matches = []
                        for match in matches:
                            # Store the alert
                            recall_alert = RecallAlert(
                                user_id=user.id,
                                recall_id=match['recall']['id'],
                                product_id=match['user_product']['id'],
                                match_score=int(match['match_score']),
                                confidence=match['confidence'],
                                match_details=match['match_details'],
                                notification_sent=False
                            )
                            db.add(recall_alert)
                            alert_matches.append(match)

                            # Track which recalls we've processed
                            processed_recall_ids.add(match['recall']['id'])

                        # Commit the alerts
                        db.commit()

                        # Step 6: Send notification
                        success = await notification_service.send_recall_alert(
                            user.email, alert_matches
                        )

                        if success:
                            total_notifications += 1
                            # Mark notifications as sent
                            await self._mark_notifications_sent(db, user.id, [m['recall']['id'] for m in alert_matches])

                # Step 7: Mark processed recalls
                if processed_recall_ids:
                    await recall_fetcher.mark_recalls_processed(list(processed_recall_ids))

                logger.info(f"Recall check completed: {total_matches} matches found, "
                           f"{total_notifications} notifications sent, "
                           f"{len(processed_recall_ids)} recalls processed")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error in recall check job: {e}")

    async def daily_summary_job(self):
        """Send daily summary to users (optional feature)."""
        logger.info("Starting daily summary job...")

        try:
            db = SessionLocal()
            try:
                # Get summary stats
                total_users = db.query(User).count()
                total_products = db.query(Product).count()
                total_recalls = db.query(Recall).count()
                recent_alerts = db.query(RecallAlert).filter(
                    RecallAlert.created_at >= datetime.utcnow() - timedelta(days=1)
                ).count()

                logger.info(f"Daily summary: {total_users} users, {total_products} products, "
                           f"{total_recalls} recalls in database, {recent_alerts} alerts in last 24h")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error in daily summary job: {e}")

    async def cleanup_job(self):
        """Clean up old data weekly."""
        logger.info("Starting cleanup job...")

        try:
            db = SessionLocal()
            try:
                # Clean up old processed recalls (older than 90 days)
                cutoff_date = datetime.utcnow() - timedelta(days=90)
                old_recalls = db.query(Recall).filter(
                    Recall.processed == True,
                    Recall.recall_date < cutoff_date
                ).count()

                if old_recalls > 0:
                    db.query(Recall).filter(
                        Recall.processed == True,
                        Recall.recall_date < cutoff_date
                    ).delete()

                    logger.info(f"Cleaned up {old_recalls} old recalls")

                # Clean up old notifications (older than 30 days)
                old_alerts = db.query(RecallAlert).filter(
                    RecallAlert.created_at < datetime.utcnow() - timedelta(days=30)
                ).count()

                if old_alerts > 0:
                    db.query(RecallAlert).filter(
                        RecallAlert.created_at < datetime.utcnow() - timedelta(days=30)
                    ).delete()

                    logger.info(f"Cleaned up {old_alerts} old alerts")

                db.commit()
                logger.info("Cleanup job completed")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error in cleanup job: {e}")

    async def _get_users_with_products(self, db: Session) -> List[Dict]:
        """Get all users with their products."""
        users = db.query(User).all()
        users_with_products = []

        for user in users:
            products = db.query(Product).filter(Product.user_id == user.id).all()
            users_with_products.append({
                'user': user,
                'products': products
            })

        return users_with_products

    async def _mark_notifications_sent(self, db: Session, user_id: int, recall_ids: List[int]):
        """Mark notifications as sent."""
        try:
            db.query(RecallAlert).filter(
                RecallAlert.user_id == user_id,
                RecallAlert.recall_id.in_(recall_ids),
                RecallAlert.notification_sent == False
            ).update({
                RecallAlert.notification_sent: True,
                RecallAlert.notification_sent_at: datetime.utcnow()
            }, synchronize_session=False)
            db.commit()
        except Exception as e:
            logger.error(f"Error marking notifications as sent: {e}")

    async def run_manual_check(self):
        """Run a manual recall check (for testing or immediate updates)."""
        logger.info("Running manual recall scraping and check...")
        await self.scrape_recalls_job()
        await self.check_recalls_job()

# Global instance
job_manager = BackgroundJobManager()

# Convenience functions
async def start_background_jobs():
    """Start background jobs."""
    job_manager.start()

async def stop_background_jobs():
    """Stop background jobs."""
    job_manager.stop()

async def run_manual_recall_check():
    """Run manual recall check."""
    await job_manager.run_manual_check()