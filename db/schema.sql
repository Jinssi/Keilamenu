-- Keilamenu Database Schema
-- Designed for Cosmos DB for PostgreSQL (Citus) with restaurant_id as distribution key
-- Compatible with standard PostgreSQL for local development

-- Ratings table: stores user votes on meals
-- Distributed by restaurant_id for efficient per-restaurant queries
CREATE TABLE IF NOT EXISTS ratings (
    id SERIAL,
    restaurant_id VARCHAR(50) NOT NULL,      -- Shard/distribution key
    meal_name VARCHAR(500) NOT NULL,         -- The meal being rated
    rating SMALLINT NOT NULL CHECK (rating IN (-1, 1)),  -- -1 = thumbs down, 1 = thumbs up
    meal_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (restaurant_id, id)          -- Composite PK includes shard key
);

-- Index for efficient lookups by restaurant and date
CREATE INDEX IF NOT EXISTS idx_ratings_restaurant_date 
ON ratings (restaurant_id, meal_date);

-- Index for finding top picks across all restaurants
CREATE INDEX IF NOT EXISTS idx_ratings_date_score
ON ratings (meal_date, rating);

-- For Cosmos DB for PostgreSQL (Citus), distribute the table:
-- This command will fail on standard PostgreSQL but that's okay for local dev
-- SELECT create_distributed_table('ratings', 'restaurant_id');

-- Example restaurant_id values used in the app:
-- 'iss' - ISS FG restaurant
-- 'nest' - Nest Restaurant  
-- 'compass' - Cafe Keilalahti by Compass Group
