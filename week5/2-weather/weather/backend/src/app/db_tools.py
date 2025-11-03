import sqlite3
import logging
from pathlib import Path
from datetime import datetime

db_path = Path("weather_forecast") / Path("memory") / Path("forecast.db")
DB = db_path.absolute()
logging.getLogger("strands").setLevel(logging.WARNING)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", 
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS forecast (
    city TEXT,
    forcast TEXT,
    date DATETIME,
    PRIMARY KEY (city, date)
);
"""

def cache_forecast(city: str, forcast: str):
    logger.info("cache forecast tool called for %s ", city, )
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        # Ensure table exists
        cursor.execute(CREATE_TABLE_SQL)
        # Current UTC timestamp
        current_date = datetime.utcnow().isoformat(timespec='seconds')
        cursor.execute("INSERT INTO forecast (city, forcast, date) VALUES (?, ?, ?)", (city, forcast, current_date))
        conn.commit()

def fetch_forecast_from_cache(city: str):
     logger.info("fetch forecast from cache tool called for %s ", city, )
   
     with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        # Ensure table exists
        cursor.execute(CREATE_TABLE_SQL)
        # Get the most recent record for the city
        cursor.execute("SELECT forcast, date FROM forecast WHERE city = ? ORDER BY date DESC LIMIT 1", (city,))
        row = cursor.fetchone()
        if not row:
            return None
        forecast_text, iso_ts = row
        try:
            ts = datetime.fromisoformat(iso_ts)
        except Exception:
            # Bad timestamp; purge and return None
            cursor.execute("DELETE FROM forecast WHERE city = ?", (city,))
            conn.commit()
            return None
        age = datetime.utcnow() - ts
        if age.total_seconds() <= 30 * 60:
            return forecast_text
        # Stale: delete and return None
        cursor.execute("DELETE FROM forecast WHERE city = ?", (city,))
        conn.commit()
        return None
