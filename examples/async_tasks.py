"""
PyScheduler - Tâches asynchrones
===============================

Exemples d'utilisation de tâches asynchrones avec PyScheduler.
"""

import asyncio
import aiohttp
import time
from datetime import datetime
from pyscheduler import PyScheduler, task

# ============================================================================
# TÂCHES ASYNCHRONES
# ============================================================================

@task(interval=10)
async def async_web_scraping():
    """Scraping web asynchrone"""
    print(f"🕷️ [SCRAPING] Début scraping async...")
    
    urls = ["http://httpbin.org/delay/1", "http://httpbin.org/delay/2"]
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    print(f"✅ [SCRAPING] {len(results)} URLs traitées")
    return {"urls_processed": len(results)}

async def fetch_url(session, url):
    """Fetch une URL"""
    try:
        async with session.get(url) as response:
            return await response.json()
    except Exception as e:
        return {"error": str(e)}

@task(interval=15)
async def async_database_batch():
    """Traitement batch async de base de données"""
    print(f"🗄️ [DB-BATCH] Traitement batch async...")
    
    # Simulation de requêtes parallèles
    async def process_record(record_id):
        await asyncio.sleep(0.5)  # Simulation I/O
        return f"processed_{record_id}"
    
    records = range(1, 6)
    results = await asyncio.gather(*[process_record(r) for r in records])
    
    print(f"✅ [DB-BATCH] {len(results)} enregistrements traités")
    return {"records_processed": len(results)}

def main():
    """Démo tâches async"""
    print("⚡ PyScheduler - Tâches Asynchrones")
    print("=" * 50)
    
    scheduler = PyScheduler(log_level="INFO")
    
    try:
        scheduler.start()
        print("⏰ Test tâches async - 45 secondes...")
        time.sleep(45)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé")
    finally:
        scheduler.stop()

if __name__ == "__main__":
    main()