"""
GraphQL Background Task - Fetch Cloudflare Data
Optimized for free tier with batching and caching
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Import database
from app.database import get_db
from app.models import Attack

# Import Cloudflare GraphQL client
from app.integrations.cloudflare_graphql import get_cloudflare_graphql_client
from app.integrations.cloudflare_graphql_transformer import CloudflareGraphQLTransformer

logger = logging.getLogger(__name__)

# Cache for last fetch time (avoid duplicate fetches)
_last_fetch_time = None
_fetch_lock = asyncio.Lock()


async def fetch_cloudflare_data_graphql():
    """
    Fetch data from Cloudflare using GraphQL
    Optimized for free tier usage
    """
    global _last_fetch_time
    
    async with _fetch_lock:
        logger.info("🔍 Starting Cloudflare GraphQL data fetch...")
        
        try:
            # Get GraphQL client
            client = get_cloudflare_graphql_client()
            
            # Determine since time
            if _last_fetch_time:
                since = _last_fetch_time
            else:
                since = datetime.utcnow() - timedelta(minutes=5)
            
            logger.info(f"📅 Fetching data since: {since}")
            
            # Fetch all data in ONE GraphQL query (efficient!)
            data = await client.fetch_all_data(
                since=since,
                events_limit=1000
            )
            
            events = data.get("events", [])
            analytics = data.get("analytics", {})
            
            if not events:
                logger.info("ℹ️  No new events fetched")
                _last_fetch_time = datetime.utcnow()
                return
            
            logger.info(f"✅ Fetched {len(events)} events via GraphQL")
            logger.info(f"📊 Analytics: {analytics.get('total_requests', 0)} requests, {analytics.get('total_threats', 0)} threats")
            
            # Transform events to attack records
            transformer = CloudflareGraphQLTransformer()
            attack_records = []
            
            for event in events:
                record = transformer.transform_event(event)
                if record:
                    attack_records.append(record)
            
            logger.info(f"🔄 Transformed {len(attack_records)} attack records")
            
            if not attack_records:
                _last_fetch_time = datetime.utcnow()
                return
            
            # Store in database (with batching)
            stored_count = await store_attacks_batch(attack_records)
            
            logger.info(f"💾 Stored {stored_count} new attacks in database")
            
            # Update last fetch time
            _last_fetch_time = datetime.utcnow()
            
            # Log summary
            logger.info(f"""
╔═══════════════════════════════════════╗
║  CLOUDFLARE FETCH COMPLETE            ║
╠═══════════════════════════════════════╣
║  Events Fetched:    {len(events):>5}            ║
║  Records Stored:    {stored_count:>5}            ║
║  Total Requests:    {analytics.get('total_requests', 0):>5}            ║
║  Total Threats:     {analytics.get('total_threats', 0):>5}            ║
║  Threat %:          {analytics.get('threat_percentage', 0):>5.1f}%          ║
╚═══════════════════════════════════════╝
            """)
            
        except Exception as e:
            logger.error(f"❌ Error in GraphQL fetch: {e}")
            import traceback
            traceback.print_exc()


async def store_attacks_batch(attack_records: list) -> int:
    """
    Store attack records in database using batching
    
    Args:
        attack_records: List of attack record dicts
        
    Returns:
        Number of records stored
    """
    db = next(get_db())
    stored_count = 0
    batch_size = 100
    
    try:
        # Process in batches
        for i in range(0, len(attack_records), batch_size):
            batch = attack_records[i:i + batch_size]
            
            for record in batch:
                try:
                    # Check for duplicate
                    existing = db.query(Attack).filter(
                        Attack.ip_address == record["ip_address"],
                        Attack.timestamp == record["timestamp"]
                    ).first()
                    
                    if existing:
                        continue  # Skip duplicate
                    
                    # Create attack record
                    attack = Attack(**record)
                    db.add(attack)
                    stored_count += 1
                    
                except Exception as record_error:
                    logger.warning(f"⚠️  Error storing record: {record_error}")
                    continue
            
            # Commit batch
            db.commit()
            logger.debug(f"✅ Committed batch {i//batch_size + 1}")
        
        logger.info(f"💾 Batch storage complete: {stored_count} records")
        
    except Exception as db_error:
        logger.error(f"❌ Database error: {db_error}")
        db.rollback()
    finally:
        db.close()
    
    return stored_count


def run_graphql_fetch_task():
    """
    Synchronous wrapper for async GraphQL fetch
    Called by APScheduler - runs in a thread pool
    """
    logger.info("⏰ Scheduled GraphQL fetch task starting...")
    
    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(fetch_cloudflare_data_graphql())
        logger.info("✅ Scheduled GraphQL fetch task complete")
    except Exception as e:
        logger.error(f"❌ Error in scheduled task: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loop.close()


# Manual fetch for testing
async def manual_fetch():
    """Manual fetch for testing purposes"""
    print("🧪 Running manual GraphQL fetch test...")
    await fetch_cloudflare_data_graphql()
    print("✅ Manual fetch complete")


if __name__ == "__main__":
    # Test the fetch task
    asyncio.run(manual_fetch())
