"""
Database service for Cosmos DB for PostgreSQL.
Handles connection pooling and ratings CRUD operations.
Uses restaurant_id as the distribution/shard key for efficient queries.
"""
import os
from datetime import date
from typing import Optional
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

# Connection pool singleton
_pool: Optional[pool.ThreadedConnectionPool] = None


def get_pool() -> Optional[pool.ThreadedConnectionPool]:
    """Get or create the connection pool singleton."""
    global _pool
    if _pool is None:
        conn_string = os.getenv('POSTGRES_CONNECTION_STRING')
        if conn_string:
            try:
                _pool = pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=10,
                    dsn=conn_string
                )
            except Exception as e:
                print(f"Database connection error: {e}")
    return _pool


@contextmanager
def get_connection():
    """Context manager for getting a connection from the pool."""
    p = get_pool()
    if p is None:
        yield None
        return
    
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def init_db():
    """
    Initialize the database schema.
    Creates the ratings table distributed by restaurant_id for Cosmos DB PostgreSQL (Citus).
    Falls back to regular table for local PostgreSQL.
    """
    with get_connection() as conn:
        if conn is None:
            print("Database not configured, skipping init")
            return False
        
        with conn.cursor() as cur:
            # Create ratings table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ratings (
                    id SERIAL,
                    restaurant_id VARCHAR(50) NOT NULL,
                    meal_name VARCHAR(500) NOT NULL,
                    rating SMALLINT NOT NULL CHECK (rating IN (-1, 1)),
                    meal_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (restaurant_id, id)
                );
            """)
            
            # Create index for efficient queries by restaurant and date
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_ratings_restaurant_date 
                ON ratings (restaurant_id, meal_date);
            """)
            
            # Try to distribute table for Citus (Cosmos DB for PostgreSQL)
            # This will fail silently on regular PostgreSQL
            try:
                cur.execute("""
                    SELECT create_distributed_table('ratings', 'restaurant_id');
                """)
                print("Table distributed by restaurant_id (Citus mode)")
            except psycopg2.Error:
                # Not running on Citus, that's fine for local dev
                conn.rollback()
                conn.commit()
                print("Running on standard PostgreSQL (non-distributed)")
            
            print("Database initialized successfully")
            return True


def add_rating(restaurant_id: str, meal_name: str, rating: int, meal_date: Optional[date] = None) -> bool:
    """
    Add a rating for a meal.
    
    Args:
        restaurant_id: The restaurant identifier (shard key)
        meal_name: Name of the meal being rated
        rating: 1 for thumbs up, -1 for thumbs down
        meal_date: Date of the meal (defaults to today)
    
    Returns:
        True if rating was added successfully
    """
    if rating not in (-1, 1):
        return False
    
    if meal_date is None:
        meal_date = date.today()
    
    with get_connection() as conn:
        if conn is None:
            return False
        
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ratings (restaurant_id, meal_name, rating, meal_date)
                VALUES (%s, %s, %s, %s)
            """, (restaurant_id, meal_name, rating, meal_date))
            return True


def get_ratings_summary(restaurant_id: str, meal_date: Optional[date] = None) -> dict:
    """
    Get aggregated ratings for a restaurant's meals.
    
    Args:
        restaurant_id: The restaurant identifier
        meal_date: Date to filter by (defaults to today)
    
    Returns:
        Dict mapping meal_name to {'up': count, 'down': count, 'score': net_score}
    """
    if meal_date is None:
        meal_date = date.today()
    
    with get_connection() as conn:
        if conn is None:
            return {}
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    meal_name,
                    COUNT(*) FILTER (WHERE rating = 1) as up,
                    COUNT(*) FILTER (WHERE rating = -1) as down,
                    SUM(rating) as score
                FROM ratings
                WHERE restaurant_id = %s AND meal_date = %s
                GROUP BY meal_name
            """, (restaurant_id, meal_date))
            
            results = {}
            for row in cur.fetchall():
                results[row['meal_name']] = {
                    'up': row['up'] or 0,
                    'down': row['down'] or 0,
                    'score': row['score'] or 0
                }
            return results


def get_top_pick(meal_date: Optional[date] = None) -> Optional[dict]:
    """
    Get the highest-rated meal across all restaurants for a given date.
    
    Returns:
        Dict with restaurant_id, meal_name, and score, or None if no ratings
    """
    if meal_date is None:
        meal_date = date.today()
    
    with get_connection() as conn:
        if conn is None:
            return None
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    restaurant_id,
                    meal_name,
                    SUM(rating) as score,
                    COUNT(*) as total_votes
                FROM ratings
                WHERE meal_date = %s
                GROUP BY restaurant_id, meal_name
                HAVING SUM(rating) > 0
                ORDER BY score DESC, total_votes DESC
                LIMIT 1
            """, (meal_date,))
            
            row = cur.fetchone()
            if row:
                return {
                    'restaurant_id': row['restaurant_id'],
                    'meal_name': row['meal_name'],
                    'score': row['score'],
                    'total_votes': row['total_votes']
                }
            return None


def close_pool():
    """Close the connection pool."""
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None
