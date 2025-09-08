"""Recall data fetching service for RecallGuard."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import aiohttp
import requests
from bs4 import BeautifulSoup
import re
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.models import Recall

# Import the LLM parser
try:
    from llm_recall_parser import llm_parser
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    llm_parser = None

logger = logging.getLogger(__name__)

class RecallFetcher:
    """Service to fetch recall data from various government sources."""

    def __init__(self):
        self.session = requests.Session()  # Keep for fallback
        self.session.headers.update({
            'User-Agent': 'RecallGuard/1.0 (Recall Alert Service)'
        })
        self._aiohttp_session = None

    async def _get_session(self):
        """Get or create aiohttp session."""
        if self._aiohttp_session is None or self._aiohttp_session.closed:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=3)
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            self._aiohttp_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': 'RecallGuard/1.0 (Recall Alert Service)'}
            )
        return self._aiohttp_session

    async def _close_session(self):
        """Close aiohttp session."""
        if self._aiohttp_session and not self._aiohttp_session.closed:
            await self._aiohttp_session.close()

    async def fetch_and_store_recalls(self, days_back: int = 30) -> Dict[str, int]:
        """Fetch recalls from all sources and store in database with parallel processing."""
        stats = {
            'total_fetched': 0,
            'new_recalls': 0,
            'updated_recalls': 0,
            'fda_food_recalls': 0,
            'fda_drug_recalls': 0,
            'fda_device_recalls': 0,
            'fda_animal_recalls': 0,
            'fda_cosmetics_recalls': 0,
            'fda_tobacco_recalls': 0,
            'fda_biologics_recalls': 0,
            'cpsc_recalls': 0,
            'nhtsa_recalls': 0,
            'usda_recalls': 0,
            'recalls_gov_recalls': 0
        }

        try:
            # Fetch from all sources in parallel for better performance
            logger.info("🔍 Fetching recalls from all sources in parallel...")
            
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=15, limit_per_host=3),
                timeout=aiohttp.ClientTimeout(total=20, connect=5),
                headers={'User-Agent': 'RecallGuard/1.0 (Recall Alert Service)'}
            ) as session:
                fetch_tasks = [
                    self.fetch_fda_food_recalls_async(session, days_back),
                    self.fetch_fda_drug_recalls_async(session, days_back),
                    self.fetch_fda_device_recalls_async(session, days_back),
                    self.fetch_fda_animal_recalls_async(session, days_back),
                    self.fetch_fda_cosmetics_recalls_async(session, days_back),
                    self.fetch_fda_tobacco_recalls_async(session, days_back),
                    self.fetch_fda_biologics_recalls_async(session, days_back),
                    self.fetch_cpsc_recalls_async(session, days_back),
                    self.fetch_nhtsa_recalls_async(session, days_back),
                    self.fetch_usda_recalls_async(session, days_back),
                    self.fetch_recalls_gov_async(session, days_back)
                ]
                
                results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
            
            # Unpack results
            fda_food_recalls = results[0] if not isinstance(results[0], Exception) else []
            fda_drug_recalls = results[1] if not isinstance(results[1], Exception) else []
            fda_device_recalls = results[2] if not isinstance(results[2], Exception) else []
            fda_animal_recalls = results[3] if not isinstance(results[3], Exception) else []
            fda_cosmetics_recalls = results[4] if not isinstance(results[4], Exception) else []
            fda_tobacco_recalls = results[5] if not isinstance(results[5], Exception) else []
            fda_biologics_recalls = results[6] if not isinstance(results[6], Exception) else []
            cpsc_recalls = results[7] if not isinstance(results[7], Exception) else []
            nhtsa_recalls = results[8] if not isinstance(results[8], Exception) else []
            usda_recalls = results[9] if not isinstance(results[9], Exception) else []
            recalls_gov_recalls = results[10] if not isinstance(results[10], Exception) else []
            
            # Log any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    source_names = ['FDA Food', 'FDA Drug', 'FDA Device', 'FDA Animal', 
                                   'FDA Cosmetics', 'FDA Tobacco', 'FDA Biologics', 
                                   'CPSC', 'NHTSA', 'USDA', 'Recalls.gov']
                    logger.error(f"❌ Failed to fetch {source_names[i]} recalls: {result}")
            
            # Update stats
            stats['fda_food_recalls'] = len(fda_food_recalls)
            stats['fda_drug_recalls'] = len(fda_drug_recalls)
            stats['fda_device_recalls'] = len(fda_device_recalls)
            stats['fda_animal_recalls'] = len(fda_animal_recalls)
            stats['fda_cosmetics_recalls'] = len(fda_cosmetics_recalls)
            stats['fda_tobacco_recalls'] = len(fda_tobacco_recalls)
            stats['fda_biologics_recalls'] = len(fda_biologics_recalls)
            stats['cpsc_recalls'] = len(cpsc_recalls)
            stats['nhtsa_recalls'] = len(nhtsa_recalls)
            stats['usda_recalls'] = len(usda_recalls)
            stats['recalls_gov_recalls'] = len(recalls_gov_recalls)
            
            all_recalls = (fda_food_recalls + fda_drug_recalls + fda_device_recalls + 
                          fda_animal_recalls + fda_cosmetics_recalls + fda_tobacco_recalls + 
                          fda_biologics_recalls + cpsc_recalls + nhtsa_recalls + usda_recalls +
                          recalls_gov_recalls)
            stats['total_fetched'] = len(all_recalls)
            
            logger.info(f"✅ Fetched total {len(all_recalls)} recalls from all sources")
            
            if all_recalls:
                logger.info("💾 Storing recalls in database with optimized batching...")
                store_stats = await self._store_recalls_batch(all_recalls)
                stats['new_recalls'] = store_stats['new']
                stats['updated_recalls'] = store_stats['updated']
                
            logger.info(f"🎉 Recall fetch and store completed successfully!")
            logger.info(f"📊 Final Statistics: {stats}")

        except Exception as e:
            logger.error(f"❌ Error in fetch_and_store_recalls: {e}")

        return stats

    async def _store_recalls_batch(self, all_recalls: List[Dict]) -> Dict[str, int]:
        """Store recalls in optimized batches to avoid database timeouts."""
        stats = {'new': 0, 'updated': 0}
        batch_size = 25  # Smaller batches for better reliability
        total_batches = (len(all_recalls) + batch_size - 1) // batch_size
        
        db = SessionLocal()
        try:
            for batch_num in range(0, len(all_recalls), batch_size):
                batch = all_recalls[batch_num:batch_num + batch_size]
                current_batch = (batch_num // batch_size) + 1
                
                logger.info(f"   📦 Processing batch {current_batch}/{total_batches} ({len(batch)} recalls)...")
                
                for recall_data in batch:
                    try:
                        if await self._store_recall(db, recall_data):
                            stats['new'] += 1
                        else:
                            stats['updated'] += 1
                    except Exception as e:
                        logger.warning(f"Failed to store recall {recall_data.get('source_id', 'unknown')}: {e}")
                        continue
                
                # Commit batch and add progress
                try:
                    db.commit()
                    progress = (current_batch / total_batches) * 100
                    logger.info(f"   ✅ Batch {current_batch}/{total_batches} complete ({progress:.1f}%)")
                    
                    # Add small delay to prevent database overload
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Failed to commit batch {current_batch}: {e}")
                    db.rollback()
                    
        finally:
            db.close()
            
        logger.info(f"✅ Stored {stats['new']} new recalls, updated {stats['updated']} existing recalls")
        return stats

    async def _store_recall(self, db: Session, recall_data: Dict) -> bool:
        """Store recall in database, return True if new, False if updated."""
        try:
            # Validate required fields
            if not recall_data.get('product_name'):
                logger.warning(f"Skipping recall with missing product_name: {recall_data.get('source_id', 'unknown')}")
                return False

            if not recall_data.get('recall_date'):
                logger.warning(f"Skipping recall with missing recall_date: {recall_data.get('source_id', 'unknown')}")
                return False

            # Truncate long fields to prevent database errors
            product_name = str(recall_data['product_name'])[:500]  # Limit to 500 chars
            brand = str(recall_data.get('brand', ''))[:200] if recall_data.get('brand') else None
            model = str(recall_data.get('model', ''))[:200] if recall_data.get('model') else None
            details = str(recall_data.get('details', ''))[:5000] if recall_data.get('details') else None  # Limit details
            link = str(recall_data.get('link', ''))[:1000] if recall_data.get('link') else None
            source_id = str(recall_data.get('source_id', ''))[:200] if recall_data.get('source_id') else None

            # Check if recall already exists
            existing_recall = None
            if source_id:
                existing_recall = db.query(Recall).filter(
                    Recall.source == recall_data['source'],
                    Recall.source_id == source_id
                ).first()

            if existing_recall:
                # Update existing recall
                existing_recall.product_name = product_name
                existing_recall.brand = brand
                existing_recall.model = model
                existing_recall.details = details
                existing_recall.link = link
                existing_recall.raw_data = recall_data.get('raw_data')
                existing_recall.updated_at = datetime.utcnow()
                return False
            else:
                # Create new recall
                new_recall = Recall(
                    source=recall_data['source'],
                    source_id=source_id,
                    category=recall_data.get('category'),
                    product_name=product_name,
                    brand=brand,
                    model=model,
                    recall_date=recall_data['recall_date'],
                    details=details,
                    link=link,
                    raw_data=recall_data.get('raw_data'),
                    processed=False
                )
                db.add(new_recall)
                return True

        except Exception as e:
            logger.error(f"Error storing recall {recall_data.get('source_id', 'unknown')}: {e}")
            # Don't let one bad recall stop the whole process
            return False

    async def get_unprocessed_recalls(self, limit: int = 100) -> List[Dict]:
        """Get unprocessed recalls from database for AI matching."""
        db = SessionLocal()
        try:
            recalls = db.query(Recall).filter(
                Recall.processed == False
            ).limit(limit).all()

            recall_dicts = []
            for recall in recalls:
                recall_dicts.append({
                    'id': recall.id,
                    'source': recall.source,
                    'category': recall.category,
                    'product_name': recall.product_name,
                    'brand': recall.brand,
                    'model': recall.model,
                    'recall_date': recall.recall_date,
                    'details': recall.details,
                    'link': recall.link
                })

            return recall_dicts

        finally:
            db.close()

    async def mark_recalls_processed(self, recall_ids: List[int]):
        """Mark recalls as processed after AI matching."""
        db = SessionLocal()
        try:
            db.query(Recall).filter(
                Recall.id.in_(recall_ids)
            ).update({Recall.processed: True}, synchronize_session=False)
            db.commit()
        finally:
            db.close()

    async def fetch_fda_food_recalls_async(self, session: aiohttp.ClientSession, days_back: int = 30) -> List[Dict]:
        """Fetch food recalls from FDA API using async HTTP."""
        recalls = []
        
        try:
            base_url = "https://api.fda.gov/food/enforcement.json"
            
            for skip in range(0, 300, 100):
                params = {
                    'limit': 100,
                    'skip': skip
                }
                
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'results' in data and data['results']:
                            for item in data['results']:
                                recall = self._parse_fda_recall(item, 'food')
                                if recall and recall['recall_date'] > datetime.now() - timedelta(days=days_back):
                                    recalls.append(recall)
                        else:
                            break
                    else:
                        logger.warning(f"FDA Food API returned status {response.status}")
                        break
                        
        except Exception as e:
            logger.error(f"Error fetching FDA food recalls: {e}")
            
        logger.info(f"✅ Fetched {len(recalls)} FDA Food recalls")
        return recalls

    async def fetch_fda_drug_recalls_async(self, session: aiohttp.ClientSession, days_back: int = 30) -> List[Dict]:
        """Fetch drug recalls from FDA API using async HTTP."""
        recalls = []
        
        try:
            base_url = "https://api.fda.gov/drug/enforcement.json"
            
            for skip in range(0, 300, 100):
                params = {
                    'limit': 100,
                    'skip': skip
                }
                
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'results' in data and data['results']:
                            for item in data['results']:
                                recall = self._parse_fda_recall(item, 'drug')
                                if recall and recall['recall_date'] > datetime.now() - timedelta(days=days_back):
                                    recalls.append(recall)
                        else:
                            break
                    else:
                        break
                        
        except Exception as e:
            logger.error(f"Error fetching FDA drug recalls: {e}")
            
        logger.info(f"✅ Fetched {len(recalls)} FDA Drug recalls")
        return recalls

    async def fetch_fda_device_recalls_async(self, session: aiohttp.ClientSession, days_back: int = 30) -> List[Dict]:
        """Fetch device recalls from FDA API using async HTTP."""
        recalls = []
        
        try:
            base_url = "https://api.fda.gov/device/enforcement.json"
            
            for skip in range(0, 300, 100):
                params = {
                    'limit': 100,
                    'skip': skip
                }
                
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'results' in data and data['results']:
                            for item in data['results']:
                                recall = self._parse_fda_recall(item, 'medical_device')
                                if recall and recall['recall_date'] > datetime.now() - timedelta(days=days_back):
                                    recalls.append(recall)
                        else:
                            break
                    else:
                        break
                        
        except Exception as e:
            logger.error(f"Error fetching FDA device recalls: {e}")
            
        logger.info(f"✅ Fetched {len(recalls)} FDA Device recalls")
        return recalls

    async def fetch_cpsc_recalls_async(self, session: aiohttp.ClientSession, days_back: int = 30) -> List[Dict]:
        """Fetch CPSC recalls using async HTTP."""
        recalls = []
        
        try:
            api_url = "https://www.saferproducts.gov/RestWebServices/Recall"
            
            # Try JSON API first
            try:
                async with session.get(api_url, params={'format': 'json'}) as response:
                    if response.status == 200:
                        api_data = await response.json()
                        cutoff_date = datetime.now() - timedelta(days=days_back)
                        
                        # Increase limit to catch more recalls including KidKraft
                        limited_data = api_data[:500] if len(api_data) > 500 else api_data
                        logger.info(f"Processing {len(limited_data)} of {len(api_data)} CPSC recalls for performance")
                        
                        for item in limited_data:
                            recall = self._parse_cpsc_api_recall(item)
                            if recall and recall.get('recall_date', datetime.min) > cutoff_date:
                                recalls.append(recall)
                                
                        logger.info(f"✅ Fetched {len(recalls)} CPSC recalls from API")
                        return recalls
            except Exception as e:
                logger.warning(f"CPSC API failed: {e}, trying RSS fallback")
            
            # Fallback to RSS
            rss_url = "https://www.cpsc.gov/Recalls/CPSC-Recalls-RSS"
            async with session.get(rss_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'xml')
                    items = soup.find_all('item')
                    
                    cutoff_date = datetime.now() - timedelta(days=days_back)
                    # Limit RSS items for performance
                    limited_items = items[:50] if len(items) > 50 else items
                    logger.info(f"Processing {len(limited_items)} of {len(items)} CPSC RSS items for performance")
                    
                    for item in limited_items:
                        recall = self._parse_cpsc_rss_recall(item)
                        if recall and recall.get('recall_date', datetime.min) > cutoff_date:
                            recalls.append(recall)
                            
        except Exception as e:
            logger.error(f"Error fetching CPSC recalls: {e}")
            
        logger.info(f"✅ Fetched {len(recalls)} CPSC recalls")
        return recalls

    async def fetch_nhtsa_recalls_async(self, session: aiohttp.ClientSession, days_back: int = 30) -> List[Dict]:
        """Fetch NHTSA recalls using async HTTP."""
        recalls = []
        
        try:
            base_url = "https://api.nhtsa.gov/recalls/recallsByVehicle"
            current_year = datetime.now().year
            
            for year in [current_year, current_year - 1]:
                params = {'modelYear': year, 'format': 'json'}
                
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'results' in data:
                            for item in data['results']:
                                recall = self._parse_nhtsa_recall(item)
                                if recall and recall['recall_date'] > datetime.now() - timedelta(days=days_back):
                                    recalls.append(recall)
                                    
        except Exception as e:
            logger.error(f"Error fetching NHTSA recalls: {e}")
            
        logger.info(f"✅ Fetched {len(recalls)} NHTSA recalls")
        return recalls

    async def fetch_usda_recalls_async(self, session: aiohttp.ClientSession, days_back: int = 30) -> List[Dict]:
        """Fetch USDA recalls using async HTTP."""
        recalls = []
        
        try:
            usda_url = "https://www.fsis.usda.gov/recalls-alerts/rss"
            
            async with session.get(usda_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'xml')
                    items = soup.find_all('item')
                    
                    cutoff_date = datetime.now() - timedelta(days=days_back)
                    for item in items:
                        recall = self._parse_usda_recall(item)
                        if recall and recall.get('recall_date', datetime.min) > cutoff_date:
                            recalls.append(recall)
                            
        except Exception as e:
            logger.error(f"Error fetching USDA recalls: {e}")
            
        logger.info(f"✅ Fetched {len(recalls)} USDA recalls")
        return recalls

    async def fetch_fda_animal_recalls_async(self, session: aiohttp.ClientSession, days_back: int = 30) -> List[Dict]:
        """Fetch animal and veterinary recalls from FDA API using async HTTP."""
        recalls = []
        
        try:
            base_url = "https://api.fda.gov/animalandveterinary/enforcement.json"
            
            for skip in range(0, 300, 100):
                params = {
                    'limit': 100,
                    'skip': skip
                }
                
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'results' in data and data['results']:
                            for item in data['results']:
                                recall = self._parse_fda_recall(item, 'animal_veterinary')
                                if recall and recall['recall_date'] > datetime.now() - timedelta(days=days_back):
                                    recalls.append(recall)
                        else:
                            break
                    else:
                        break
                        
        except Exception as e:
            logger.error(f"Error fetching FDA animal/veterinary recalls: {e}")
            
        logger.info(f"✅ Fetched {len(recalls)} FDA Animal/Veterinary recalls")
        return recalls

    async def fetch_fda_cosmetics_recalls_async(self, session: aiohttp.ClientSession, days_back: int = 30) -> List[Dict]:
        """Fetch cosmetics recalls from FDA API using async HTTP."""
        recalls = []
        
        try:
            # FDA doesn't have a specific cosmetics enforcement API, but we'll check the general enforcement
            base_url = "https://api.fda.gov/other/enforcement.json"
            
            for skip in range(0, 100, 50):
                params = {
                    'limit': 50,
                    'skip': skip,
                    'search': 'product_description:"cosmetic" OR product_description:"makeup" OR product_description:"beauty"'
                }
                
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'results' in data and data['results']:
                            for item in data['results']:
                                recall = self._parse_fda_recall(item, 'cosmetics')
                                if recall and recall['recall_date'] > datetime.now() - timedelta(days=days_back):
                                    recalls.append(recall)
                        else:
                            break
                    else:
                        break
                        
        except Exception as e:
            logger.error(f"Error fetching FDA cosmetics recalls: {e}")
            
        logger.info(f"✅ Fetched {len(recalls)} FDA Cosmetics recalls")
        return recalls

    async def fetch_fda_tobacco_recalls_async(self, session: aiohttp.ClientSession, days_back: int = 30) -> List[Dict]:
        """Fetch tobacco product recalls from FDA API using async HTTP."""
        recalls = []
        
        try:
            base_url = "https://api.fda.gov/tobacco/enforcement.json"
            
            for skip in range(0, 100, 50):
                params = {
                    'limit': 50,
                    'skip': skip
                }
                
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'results' in data and data['results']:
                            for item in data['results']:
                                recall = self._parse_fda_recall(item, 'tobacco')
                                if recall and recall['recall_date'] > datetime.now() - timedelta(days=days_back):
                                    recalls.append(recall)
                        else:
                            break
                    else:
                        break
                        
        except Exception as e:
            logger.error(f"Error fetching FDA tobacco recalls: {e}")
            
        logger.info(f"✅ Fetched {len(recalls)} FDA Tobacco recalls")
        return recalls

    async def fetch_fda_biologics_recalls_async(self, session: aiohttp.ClientSession, days_back: int = 30) -> List[Dict]:
        """Fetch biologics recalls from FDA API using async HTTP."""
        recalls = []
        
        try:
            # Biologics are often included in drug enforcement
            base_url = "https://api.fda.gov/drug/enforcement.json"
            
            for skip in range(0, 200, 100):
                params = {
                    'limit': 100,
                    'skip': skip,
                    'search': 'product_description:"biologic" OR product_description:"vaccine" OR product_description:"blood"'
                }
                
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'results' in data and data['results']:
                            for item in data['results']:
                                recall = self._parse_fda_recall(item, 'biologics')
                                if recall and recall['recall_date'] > datetime.now() - timedelta(days=days_back):
                                    recalls.append(recall)
                        else:
                            break
                    else:
                        break
                        
        except Exception as e:
            logger.error(f"Error fetching FDA biologics recalls: {e}")
            
        logger.info(f"✅ Fetched {len(recalls)} FDA Biologics recalls")
        return recalls

    async def fetch_recalls_gov_async(self, session: aiohttp.ClientSession, days_back: int = 30) -> List[Dict]:
        """Fetch recalls from Recalls.gov using web scraping since no API is available."""
        recalls = []
        
        try:
            # Since recalls.gov doesn't have an API, we'll scrape their recent recalls
            recalls_urls = [
                "https://www.recalls.gov/recent.html",
                "https://www.recalls.gov/consumer-products.html",
                "https://www.recalls.gov/foods-medicines-cosmetics.html",
            ]
            
            for url in recalls_urls:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            html_content = await response.text()
                            soup = BeautifulSoup(html_content, 'html.parser')
                            
                            # Look for recall links and information
                            recall_links = soup.find_all('a', href=True)
                            
                            for link in recall_links:
                                href = link.get('href', '')
                                text = link.get_text(strip=True)
                                
                                # Filter for actual recall links
                                if any(keyword in href.lower() for keyword in ['recall', 'cpsc', 'fda', 'nhtsa']) and len(text) > 10:
                                    recall = self._parse_recalls_gov_item(link, href, text, url)
                                    if recall:
                                        recalls.append(recall)
                                        
                                    # Limit to avoid overwhelming the site
                                    if len(recalls) >= 50:
                                        break
                                        
                except Exception as e:
                    logger.warning(f"Failed to scrape {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching recalls.gov data: {e}")
            
        # Remove duplicates based on link
        seen_links = set()
        unique_recalls = []
        for recall in recalls:
            link = recall.get('link', '')
            if link not in seen_links:
                seen_links.add(link)
                unique_recalls.append(recall)
                
        logger.info(f"✅ Fetched {len(unique_recalls)} Recalls.gov recalls")
        return unique_recalls

    def _parse_recalls_gov_item(self, link_element, href: str, text: str, source_url: str) -> Dict:
        """Parse a recalls.gov recall item."""
        try:
            # Extract basic information
            product_name = text[:100] if text else "Unknown Product"
            
            # Try to infer category from source URL
            category = 'consumer_product'  # default
            if 'food' in source_url.lower() or 'medicine' in source_url.lower():
                if any(term in text.lower() for term in ['food', 'meat', 'dairy', 'frozen']):
                    category = 'food'
                elif any(term in text.lower() for term in ['drug', 'medicine', 'medication']):
                    category = 'drug'
                elif any(term in text.lower() for term in ['cosmetic', 'beauty', 'makeup']):
                    category = 'cosmetics'
                    
            # Generate unique source ID
            source_id = f"recalls_gov_{hash(href) % 100000}"
            
            # Make the href absolute if it's relative
            if href.startswith('/'):
                full_link = f"https://www.recalls.gov{href}"
            elif href.startswith('http'):
                full_link = href
            else:
                full_link = f"https://www.recalls.gov/{href}"
                
            return {
                'source': 'Recalls.gov',
                'source_id': source_id,
                'category': category,
                'product_name': product_name,
                'brand': None,  # Not easily extractable from link text
                'model': None,
                'recall_date': datetime.now() - timedelta(days=1),  # Assume recent
                'details': f"Recall information from Recalls.gov: {text}",
                'link': full_link,
                'raw_data': {
                    'original_text': text,
                    'source_url': source_url,
                    'href': href
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing recalls.gov item: {e}")
            return None

    async def fetch_fda_food_recalls(self, days_back: int = 30) -> List[Dict]:
        """Fetch food recalls from FDA API - using correct endpoint without date filter initially."""
        recalls = []

        try:
            # FDA API endpoint for food recalls
            base_url = "https://api.fda.gov/food/enforcement.json"

            # Start with recent recalls without date filter to avoid 404
            for skip in range(0, 300, 100):  # Get up to 300 results
                params = {
                    'limit': 100,
                    'skip': skip
                }

                response = self.session.get(base_url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if 'results' in data and data['results']:
                        for item in data['results']:
                            recall = self._parse_fda_recall(item, 'food')
                            if recall:
                                # Filter by date after parsing
                                if recall['recall_date'] > datetime.now() - timedelta(days=days_back):
                                    recalls.append(recall)
                    else:
                        break  # No more results
                elif response.status_code == 404:
                    logger.warning(f"FDA Food API endpoint not found - trying alternative approach")
                    break
                else:
                    logger.warning(f"FDA Food API returned status {response.status_code}")
                    break

        except Exception as e:
            logger.error(f"Error fetching FDA food recalls: {e}")

        return recalls

    async def fetch_fda_drug_recalls(self, days_back: int = 30) -> List[Dict]:
        """Fetch drug recalls from FDA API."""
        recalls = []

        try:
            base_url = "https://api.fda.gov/drug/enforcement.json"

            for skip in range(0, 300, 100):
                params = {
                    'limit': 100,
                    'skip': skip
                }

                response = self.session.get(base_url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if 'results' in data and data['results']:
                        for item in data['results']:
                            recall = self._parse_fda_recall(item, 'drug')
                            if recall:
                                # Filter by date after parsing
                                if recall['recall_date'] > datetime.now() - timedelta(days=days_back):
                                    recalls.append(recall)
                    else:
                        break
                else:
                    break

        except Exception as e:
            logger.error(f"Error fetching FDA drug recalls: {e}")

        return recalls

    async def fetch_fda_device_recalls(self, days_back: int = 30) -> List[Dict]:
        """Fetch medical device recalls from FDA API."""
        recalls = []

        try:
            base_url = "https://api.fda.gov/device/enforcement.json"

            for skip in range(0, 300, 100):
                params = {
                    'limit': 100,
                    'skip': skip
                }

                response = self.session.get(base_url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if 'results' in data and data['results']:
                        for item in data['results']:
                            recall = self._parse_fda_recall(item, 'medical_device')
                            if recall:
                                # Filter by date after parsing
                                if recall['recall_date'] > datetime.now() - timedelta(days=days_back):
                                    recalls.append(recall)
                    else:
                        break
                else:
                    break

        except Exception as e:
            logger.error(f"Error fetching FDA device recalls: {e}")

        return recalls

    async def fetch_cpsc_recalls(self, days_back: int = 30) -> List[Dict]:
        """Fetch recalls from CPSC using their official API."""
        recalls = []

        try:
            # Use the official CPSC API from their documentation
            api_url = "https://www.saferproducts.gov/RestWebServices/Recall"

            logger.info("Fetching CPSC recalls from official API...")

            # Try different approaches to get recent recalls
            api_params = [
                {},  # Get all recent recalls
                {'format': 'json'},  # Specify JSON format
                {'RecallDateStart': (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')},  # Date filter
            ]

            for params in api_params:
                try:
                    response = self.session.get(api_url, params=params, timeout=10)  # Reduced timeout
                    logger.info(f"CPSC API response status: {response.status_code}")

                    if response.status_code == 200:
                        # Try to parse as JSON
                        try:
                            api_data = response.json()
                            logger.info(f"Successfully parsed {len(api_data)} CPSC recalls from API")
                            
                            # Increase limit to get more recalls including KidKraft
                            limited_data = api_data[:500] if len(api_data) > 500 else api_data
                            logger.info(f"Processing {len(limited_data)} of {len(api_data)} CPSC recalls for performance")

                            cutoff_date = datetime.now() - timedelta(days=days_back)

                            for item in limited_data:
                                recall = self._parse_cpsc_api_recall(item)
                                if recall and recall.get('recall_date', datetime.min) > cutoff_date:
                                    recalls.append(recall)
                            break  # Success, no need to try other params

                        except json.JSONDecodeError:
                            # Try parsing as XML
                            try:
                                soup = BeautifulSoup(response.content, 'xml')
                                recall_items = soup.find_all('Recall')
                                logger.info(f"Found {len(recall_items)} CPSC recalls in XML format")
                                
                                # Increase limit to get KidKraft and other important recalls
                                limited_items = recall_items[:200] if len(recall_items) > 200 else recall_items
                                logger.info(f"Processing {len(limited_items)} of {len(recall_items)} CPSC XML recalls for performance")

                                for item in limited_items:
                                    recall = self._parse_cpsc_xml_recall(item)
                                    if recall:
                                        recalls.append(recall)
                                break
                            except Exception as e:
                                logger.warning(f"Failed to parse CPSC XML: {e}")

                    else:
                        logger.warning(f"CPSC API returned status {response.status_code}")

                except Exception as e:
                    logger.warning(f"CPSC API attempt failed: {e}")
                    continue

            # Fallback to RSS feed if API doesn't work
            if not recalls:
                logger.info("Falling back to CPSC RSS feed...")
                try:
                    cpsc_rss_url = "https://www.cpsc.gov/Recalls/CPSC-Recalls-RSS"
                    response = self.session.get(cpsc_rss_url, timeout=30)

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'xml')
                        items = soup.find_all('item')
                        logger.info(f"Found {len(items)} items in CPSC RSS feed")

                        cutoff_date = datetime.now() - timedelta(days=days_back)

                        for item in items:
                            recall = self._parse_cpsc_rss_recall(item)
                            if recall and recall.get('recall_date', datetime.min) > cutoff_date:
                                recalls.append(recall)

                except Exception as e:
                    logger.error(f"CPSC RSS fallback failed: {e}")

        except Exception as e:
            logger.error(f"Error fetching CPSC recalls: {e}")

        logger.info(f"Successfully fetched {len(recalls)} CPSC recalls")
        return recalls

    async def fetch_nhtsa_recalls(self, days_back: int = 30) -> List[Dict]:
        """Fetch automotive recalls from NHTSA API."""
        recalls = []

        try:
            # NHTSA API for vehicle recalls
            base_url = "https://api.nhtsa.gov/recalls/recallsByVehicle"

            # Get recent recalls by year
            current_year = datetime.now().year
            years_to_check = [current_year, current_year - 1]

            for year in years_to_check:
                try:
                    params = {
                        'modelYear': year,
                        'format': 'json'
                    }

                    response = self.session.get(base_url, params=params, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        if 'results' in data:
                            for item in data['results']:
                                recall = self._parse_nhtsa_recall(item)
                                if recall:
                                    # Check if recall is within date range
                                    if recall['recall_date'] > datetime.now() - timedelta(days=days_back):
                                        recalls.append(recall)
                except Exception as e:
                    logger.warning(f"Error fetching NHTSA recalls for year {year}: {e}")

        except Exception as e:
            logger.error(f"Error fetching NHTSA recalls: {e}")

        return recalls

    async def fetch_usda_recalls(self, days_back: int = 30) -> List[Dict]:
        """Fetch food safety recalls from USDA."""
        recalls = []

        try:
            # USDA FSIS recalls RSS feed
            usda_url = "https://www.fsis.usda.gov/recalls-alerts/rss"

            response = self.session.get(usda_url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                items = soup.find_all('item')

                cutoff_date = datetime.now() - timedelta(days=days_back)

                for item in items:
                    recall = self._parse_usda_recall(item)
                    if recall and recall.get('recall_date', datetime.min) > cutoff_date:
                        recalls.append(recall)

        except Exception as e:
            logger.error(f"Error fetching USDA recalls: {e}")

        return recalls

    def _parse_fda_recall(self, item: Dict, category: str) -> Optional[Dict]:
        """Parse FDA recall data with optional LLM enhancement."""
        try:
            # Extract product name and details
            product_description = item.get('product_description', '')
            reason = item.get('reason_for_recall', '')
            full_text = f"{product_description}. {reason}".strip()

            # Parse recall date
            recall_date_str = item.get('recall_initiation_date', '')
            recall_date = None
            if recall_date_str:
                try:
                    recall_date = datetime.strptime(recall_date_str, '%Y%m%d')
                except:
                    pass

            # Generate source_id from FDA data
            source_id = item.get('recall_number') or f"fda_{category}_{recall_date_str}_{hash(product_description) % 10000}"

            # Skip LLM parsing for bulk operations to improve performance
            # if LLM_AVAILABLE and llm_parser and llm_parser.enabled and full_text:
            #     logger.debug("Using LLM parser for FDA recall extraction")
            #     parsed_data = llm_parser.parse_recall_text(full_text, "FDA")
            #     if parsed_data:
            #         return parsed recall data...

            # Fallback to manual parsing
            logger.debug("Using manual parsing for FDA recall")

            return {
                'source': 'FDA',
                'source_id': source_id,
                'category': category,
                'product_name': self._extract_product_name(product_description),
                'brand': self._extract_brand(product_description),
                'model': self._extract_model(product_description),
                'recall_date': recall_date or datetime.now(),
                'details': full_text,
                'link': f"https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts",
                'raw_data': item
            }
        except Exception as e:
            logger.error(f"Error parsing FDA recall: {e}")
            return None

    def _parse_cpsc_api_recall(self, item: Dict) -> Optional[Dict]:
        """Parse CPSC API recall data."""
        try:
            # Handle different API response formats
            product_name = ''
            manufacturer = ''

            if 'Products' in item and item['Products']:
                product_name = item['Products'][0].get('Name', '') if isinstance(item['Products'], list) else item['Products'].get('Name', '')
            elif 'ProductName' in item:
                product_name = item['ProductName']
            elif 'Title' in item:
                product_name = item['Title']

            if 'Manufacturers' in item and item['Manufacturers']:
                manufacturer = item['Manufacturers'][0].get('Name', '') if isinstance(item['Manufacturers'], list) else item['Manufacturers'].get('Name', '')
            elif 'Manufacturer' in item:
                manufacturer = item['Manufacturer']

            recall_date = None
            for date_field in ['RecallDate', 'PublicationDate', 'AnnouncementDate']:
                if item.get(date_field):
                    try:
                        recall_date = datetime.strptime(item[date_field][:10], '%Y-%m-%d')
                        break
                    except:
                        pass

            source_id = f"cpsc_api_{item.get('RecallID', item.get('ID', hash(product_name) % 10000))}"

            return {
                'source': 'CPSC',
                'source_id': source_id,
                'category': 'consumer_product',
                'product_name': product_name or 'Unknown Product',
                'brand': manufacturer,
                'model': None,
                'recall_date': recall_date or datetime.now(),
                'details': item.get('Description', item.get('Hazard', '')),
                'link': item.get('URL', item.get('Link', '')),
                'raw_data': item
            }
        except Exception as e:
            logger.error(f"Error parsing CPSC API recall: {e}")
            return None

    def _parse_cpsc_xml_recall(self, item) -> Optional[Dict]:
        """Parse CPSC XML recall data using LLM for better accuracy."""
        try:
            # Get the text content from the XML item
            description_text = ''

            # Try to get the description/content from various possible fields
            if hasattr(item, 'text') and item.text:
                description_text = item.text.strip()
            elif item.find('Description'):
                description_text = item.find('Description').text.strip()
            elif hasattr(item, 'string') and item.string:
                description_text = item.string.strip()
            else:
                # Get all text content from the item
                description_text = item.get_text().strip()

            if not description_text:
                logger.warning("No description text found in CPSC XML item")
                return None

            logger.debug(f"CPSC XML content: {description_text[:200]}...")

            # Skip LLM parsing for bulk operations to improve performance
            # if LLM_AVAILABLE and llm_parser and llm_parser.enabled:
            #     logger.debug("Using LLM parser for CPSC recall extraction")
            #     parsed_data = llm_parser.parse_recall_text(description_text, "CPSC")
            #     if parsed_data:
            #         return parsed recall data...

            # Fallback to manual parsing if LLM is not available
            logger.debug("Using manual parsing for CPSC recall (LLM not available)")

            # Extract product information using manual methods
            product_name = self._extract_cpsc_product_name(description_text)
            brand = self._extract_cpsc_brand(description_text)
            recall_date = self._extract_cpsc_date(description_text)

            # Generate a unique source ID
            source_id = f"cpsc_xml_{hash(description_text[:100]) % 100000}"

            # Try to extract recall number if present
            recall_number_match = re.search(r'Release #?\s*(\d{2}-\d{3})', description_text, re.IGNORECASE)
            if recall_number_match:
                source_id = f"cpsc_{recall_number_match.group(1)}"

            logger.debug(f"Manual parsed CPSC: product='{product_name}', brand='{brand}', date='{recall_date}'")

            return {
                'source': 'CPSC',
                'source_id': source_id,
                'category': 'consumer_product',
                'product_name': product_name,
                'brand': brand,
                'model': None,
                'recall_date': recall_date or datetime.now(),
                'details': description_text,
                'link': 'https://www.cpsc.gov/Recalls',
                'raw_data': {'xml_data': str(item), 'description': description_text}
            }

        except Exception as e:
            logger.error(f"Error parsing CPSC XML recall: {e}")
            return None

    def _extract_cpsc_product_name(self, text: str) -> str:
        """Extract product name from CPSC recall text."""
        if not text:
            return 'Consumer Product'

        # Look for common CPSC recall patterns
        patterns = [
            # "Product Recalled by Company"
            r'([A-Za-z\s]+)\s+Recalled\s+by\s+([A-Za-z\s]+)',
            # "Company Recalls Product"
            r'([A-Za-z\s]+)\s+Recalls?\s+([A-Za-z\s]+)',
            # "CPSC, Company Announce Recall of Product"
            r'CPSC,\s+([A-Za-z\s]+)\s+Announce\s+Recall\s+of\s+([A-Za-z\s]+)',
            # "Recall of Product"
            r'Recall\s+of\s+([A-Za-z\s]+)',
            # Look for product types at the beginning
            r'^([A-Za-z\s]+?)\s+(?:Recalled|Recall)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # For patterns with two groups, prefer the product (usually group 1 or 2)
                if len(match.groups()) == 2:
                    # Check which group looks more like a product
                    group1, group2 = match.groups()
                    if any(word in group1.lower() for word in ['hair', 'toy', 'chair', 'lamp', 'dryer', 'phone', 'device']):
                        return group1.strip()
                    else:
                        return group2.strip()
                else:
                    return match.group(1).strip()

        # Fallback: extract first few words that might be the product
        words = text.split()
        if len(words) >= 2:
            # Skip common prefixes
            start_idx = 0
            skip_words = ['news', 'from', 'cpsc', 'u.s.', 'consumer', 'product', 'safety', 'commission']
            while start_idx < len(words) and words[start_idx].lower() in skip_words:
                start_idx += 1

            if start_idx < len(words):
                # Take 1-3 words as product name
                product_words = words[start_idx:start_idx + 3]
                return ' '.join(product_words)

        return 'Consumer Product'

    def _extract_cpsc_brand(self, text: str) -> Optional[str]:
        """Extract brand/manufacturer from CPSC recall text."""
        if not text:
            return None

        # Look for brand/manufacturer patterns
        patterns = [
            # "Product Recalled by Brand"
            r'Recalled\s+by\s+([A-Za-z\s&]+?)(?:\s+NEWS|\s+CPSC|\s+U\.S\.|\s*$)',
            # "Brand Recalls Product"
            r'^([A-Za-z\s&]+?)\s+Recalls?\s+',
            # "CPSC, Brand Announce"
            r'CPSC,\s+([A-Za-z\s&]+?)\s+Announce',
            # "manufactured by Brand"
            r'manufactured\s+by\s+([A-Za-z\s&]+?)(?:\s|$)',
            # "distributed by Brand"
            r'distributed\s+by\s+([A-Za-z\s&]+?)(?:\s|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                brand = match.group(1).strip()
                # Clean up common suffixes
                brand = re.sub(r'\s+(Inc|LLC|Corp|Company|Co)\.?$', '', brand, flags=re.IGNORECASE)
                if len(brand) > 1 and brand.lower() not in ['cpsc', 'news', 'commission']:
                    return brand

        return None

    def _extract_cpsc_date(self, text: str) -> Optional[datetime]:
        """Extract recall date from CPSC recall text."""
        if not text:
            return None

        # Look for date patterns in CPSC text
        date_patterns = [
            # "FOR IMMEDIATE RELEASE Month Day, Year"
            r'FOR\s+IMMEDIATE\s+RELEASE\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})',
            # "Release # Month Day, Year"
            r'Release\s+#?\s*\d{2}-\d{3}\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})',
            # Just "Month Day, Year" pattern
            r'([A-Za-z]+\s+\d{1,2},\s+\d{4})',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    # Try to parse the date
                    return datetime.strptime(date_str, '%B %d, %Y')
                except:
                    try:
                        return datetime.strptime(date_str, '%b %d, %Y')
                    except:
                        continue

        return None

    def _parse_cpsc_rss_recall(self, item) -> Optional[Dict]:
        """Parse CPSC RSS recall data."""
        try:
            title = item.find('title').text if item.find('title') else ''
            description = item.find('description').text if item.find('description') else ''
            link = item.find('link').text if item.find('link') else ''
            pub_date = item.find('pubDate').text if item.find('pubDate') else ''

            # Parse date
            recall_date = None
            if pub_date:
                try:
                    recall_date = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z')
                except:
                    try:
                        recall_date = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
                    except:
                        pass

            # Generate source_id from CPSC data
            source_id = f"cpsc_rss_{hash(title) % 10000}_{recall_date.strftime('%Y%m%d') if recall_date else 'unknown'}"

            return {
                'source': 'CPSC',
                'source_id': source_id,
                'category': 'consumer_product',
                'product_name': self._extract_product_name(title),
                'brand': self._extract_brand(title),
                'model': self._extract_model(title),
                'recall_date': recall_date or datetime.now(),
                'details': f"{title}. {description}",
                'link': link,
                'raw_data': {'title': title, 'description': description}
            }
        except Exception as e:
            logger.error(f"Error parsing CPSC RSS recall: {e}")
            return None

    def _parse_nhtsa_recall(self, item: Dict) -> Optional[Dict]:
        """Parse NHTSA recall data."""
        try:
            make = item.get('Make', '')
            model = item.get('Model', '')
            year = item.get('ModelYear', '')

            product_name = f"{year} {make} {model}".strip()

            recall_date = None
            if item.get('ReportReceivedDate'):
                try:
                    recall_date = datetime.strptime(item['ReportReceivedDate'], '%Y%m%d')
                except:
                    pass

            source_id = f"nhtsa_{item.get('NHTSACampaignNumber', hash(product_name) % 10000)}"

            return {
                'source': 'NHTSA',
                'source_id': source_id,
                'category': 'automotive',
                'product_name': product_name,
                'brand': make,
                'model': f"{year} {model}",
                'recall_date': recall_date or datetime.now(),
                'details': item.get('Summary', ''),
                'link': f"https://www.nhtsa.gov/recalls",
                'raw_data': item
            }
        except Exception as e:
            logger.error(f"Error parsing NHTSA recall: {e}")
            return None

    def _parse_usda_recall(self, item) -> Optional[Dict]:
        """Parse USDA recall data."""
        try:
            title = item.find('title').text if item.find('title') else ''
            description = item.find('description').text if item.find('description') else ''
            link = item.find('link').text if item.find('link') else ''
            pub_date = item.find('pubDate').text if item.find('pubDate') else ''

            # Parse date
            recall_date = None
            if pub_date:
                try:
                    recall_date = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z')
                except:
                    try:
                        recall_date = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
                    except:
                        pass

            source_id = f"usda_{hash(title) % 10000}_{recall_date.strftime('%Y%m%d') if recall_date else 'unknown'}"

            return {
                'source': 'USDA',
                'source_id': source_id,
                'category': 'food',
                'product_name': self._extract_product_name(title),
                'brand': self._extract_brand(title),
                'model': self._extract_model(title),
                'recall_date': recall_date or datetime.now(),
                'details': f"{title}. {description}",
                'link': link,
                'raw_data': {'title': title, 'description': description}
            }
        except Exception as e:
            logger.error(f"Error parsing USDA recall: {e}")
            return None

    # Legacy method for compatibility
    async def fetch_all_recalls(self, days_back: int = 30) -> List[Dict]:
        """Fetch recalls from all sources (legacy method for compatibility)."""
        all_recalls = []

        # Fetch from different sources
        try:
            fda_food_recalls = await self.fetch_fda_food_recalls(days_back)
            all_recalls.extend(fda_food_recalls)
        except Exception as e:
            logger.error(f"Failed to fetch FDA food recalls: {e}")

        try:
            fda_drug_recalls = await self.fetch_fda_drug_recalls(days_back)
            all_recalls.extend(fda_drug_recalls)
        except Exception as e:
            logger.error(f"Failed to fetch FDA drug recalls: {e}")

        try:
            cpsc_recalls = await self.fetch_cpsc_recalls(days_back)
            all_recalls.extend(cpsc_recalls)
        except Exception as e:
            logger.error(f"Failed to fetch CPSC recalls: {e}")

        return all_recalls

    # Keep existing helper methods
    def _extract_product_name(self, text: str) -> str:
        """Extract product name from recall text using heuristics."""
        if not text:
            return ''

        # Remove common prefixes and clean up
        text = re.sub(r'^(recall|recalled|voluntary recall of|withdrawal of)\s*', '', text, flags=re.IGNORECASE)

        # Extract first significant phrase (usually the product)
        words = text.split()
        if len(words) > 0:
            # Take first 3-5 words as product name
            product_words = words[:min(5, len(words))]
            return ' '.join(product_words)

        return text[:100]  # Fallback to first 100 chars

    def _extract_brand(self, text: str) -> Optional[str]:
        """Extract brand name from recall text."""
        if not text:
            return None

        # Look for brand patterns
        brand_patterns = [
            r'brand[:\s]+([A-Za-z]+)',
            r'manufactured by\s+([A-Za-z\s]+)',
            r'distributed by\s+([A-Za-z\s]+)',
            r'([A-Z][a-z]+)\s+brand',
        ]

        for pattern in brand_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_model(self, text: str) -> Optional[str]:
        """Extract model from recall text."""
        if not text:
            return None

        # Look for model patterns
        model_patterns = [
            r'model[:\s]+([A-Za-z0-9\-]+)',
            r'model number[:\s]+([A-Za-z0-9\-]+)',
            r'#([A-Za-z0-9\-]+)',
        ]

        for pattern in model_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

# Global instance
recall_fetcher = RecallFetcher()