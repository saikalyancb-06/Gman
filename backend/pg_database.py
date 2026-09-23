import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://geoguide:geoguide@127.0.0.1:5432/geoguide")

def get_pg_connection(url: Optional[str] = None):
    conn = psycopg2.connect(url or DATABASE_URL)
    conn.autocommit = True
    return conn

def init_postgres_schema(url: Optional[str] = None):
    conn = get_pg_connection(url)
    with conn.cursor() as cur:
        # Spatial extensions
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS cube;")
            cur.execute("CREATE EXTENSION IF NOT EXISTS earthdistance;")
        except Exception as e:
            print(f"[Warning] Spatial extension warning: {e}")

        # Core Relational Application Tables
        cur.execute("""
        CREATE TABLE IF NOT EXISTS countries (
            id SERIAL PRIMARY KEY,
            code VARCHAR(10) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL,
            currency_code VARCHAR(10) NOT NULL,
            default_locale VARCHAR(20) NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cities (
            id SERIAL PRIMARY KEY,
            country_id INTEGER REFERENCES countries(id),
            name VARCHAR(100) NOT NULL,
            state VARCHAR(100) NOT NULL,
            lat DOUBLE PRECISION NOT NULL,
            lng DOUBLE PRECISION NOT NULL,
            timezone VARCHAR(50) NOT NULL,
            description TEXT,
            best_season TEXT,
            peak_months TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE,
            avatar_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_devices (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            device_token TEXT,
            platform VARCHAR(50),
            location_permission INTEGER DEFAULT 1,
            last_lat DOUBLE PRECISION,
            last_lng DOUBLE PRECISION,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_preferences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id),
            interests_json JSONB,
            budget_tier VARCHAR(50),
            pace VARCHAR(50),
            step_free_only INTEGER DEFAULT 0,
            max_walking_km DOUBLE PRECISION DEFAULT 2.0,
            avoid_midday_sun INTEGER DEFAULT 1,
            language VARCHAR(20) DEFAULT 'en',
            voice_output INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(100) NOT NULL UNIQUE,
            icon VARCHAR(50),
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS activities_poi (
            id SERIAL PRIMARY KEY,
            city_id INTEGER REFERENCES cities(id),
            category_id INTEGER REFERENCES categories(id),
            name VARCHAR(200) NOT NULL,
            tag_badge VARCHAR(100),
            short_desc TEXT,
            full_desc TEXT,
            lat DOUBLE PRECISION NOT NULL,
            lng DOUBLE PRECISION NOT NULL,
            distance_km DOUBLE PRECISION,
            travel_time_mins INTEGER,
            travel_mode VARCHAR(50),
            est_duration_mins INTEGER,
            entry_fee_inr INTEGER DEFAULT 0,
            entry_fee_foreign_inr INTEGER DEFAULT 0,
            is_step_free INTEGER DEFAULT 0,
            terrain_type TEXT,
            best_time_window TEXT,
            open_time VARCHAR(20),
            close_time VARCHAR(20),
            ticket_policy TEXT,
            rating DOUBLE PRECISION DEFAULT 4.5,
            review_count INTEGER DEFAULT 120,
            carbon_kg DOUBLE PRECISION DEFAULT 0.0,
            image_url TEXT,
            audio_intro_url TEXT
        );

        CREATE TABLE IF NOT EXISTS hotels (
            id SERIAL PRIMARY KEY,
            city_id INTEGER REFERENCES cities(id),
            name VARCHAR(200) NOT NULL,
            category VARCHAR(100),
            price_per_night INTEGER,
            rating DOUBLE PRECISION,
            distance_desc TEXT,
            lat DOUBLE PRECISION,
            lng DOUBLE PRECISION,
            image_url TEXT,
            access_note TEXT
        );

        CREATE TABLE IF NOT EXISTS weather_daily (
            id SERIAL PRIMARY KEY,
            city_id INTEGER REFERENCES cities(id),
            date VARCHAR(20) NOT NULL,
            temp_c INTEGER,
            feels_like_c INTEGER,
            condition VARCHAR(100),
            humidity_pct INTEGER,
            sunrise VARCHAR(20),
            sunset VARCHAR(20),
            daylight_hours VARCHAR(50),
            uv_index INTEGER,
            uv_alert_until VARCHAR(50),
            season_summary TEXT,
            advice_text TEXT
        );

        CREATE TABLE IF NOT EXISTS events_festivals (
            id SERIAL PRIMARY KEY,
            city_id INTEGER REFERENCES cities(id),
            name VARCHAR(200) NOT NULL,
            date_start VARCHAR(30),
            date_end VARCHAR(30),
            location_desc TEXT,
            description TEXT,
            impact_level VARCHAR(50)
        );

        CREATE TABLE IF NOT EXISTS safety_advisories (
            id SERIAL PRIMARY KEY,
            city_id INTEGER REFERENCES cities(id),
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            severity VARCHAR(50) NOT NULL,
            advisory_type VARCHAR(50) NOT NULL,
            is_active INTEGER DEFAULT 1,
            valid_until VARCHAR(50),
            detour_advice TEXT
        );

        CREATE TABLE IF NOT EXISTS trips (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            city_id INTEGER REFERENCES cities(id),
            title VARCHAR(200),
            start_date VARCHAR(30),
            end_date VARCHAR(30),
            budget_spent_inr INTEGER DEFAULT 0,
            sites_seen_count INTEGER DEFAULT 0,
            saved_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS itineraries (
            id SERIAL PRIMARY KEY,
            trip_id INTEGER REFERENCES trips(id),
            user_id INTEGER REFERENCES users(id),
            title VARCHAR(200),
            date VARCHAR(30),
            duration_type VARCHAR(50),
            optimization_filter VARCHAR(50),
            total_duration_mins INTEGER,
            total_cost_inr INTEGER,
            total_walking_km DOUBLE PRECISION,
            total_carbon_kg DOUBLE PRECISION,
            note TEXT
        );

        CREATE TABLE IF NOT EXISTS itinerary_items (
            id SERIAL PRIMARY KEY,
            itinerary_id INTEGER REFERENCES itineraries(id),
            poi_id INTEGER REFERENCES activities_poi(id),
            stop_order INTEGER,
            start_time VARCHAR(20),
            end_time VARCHAR(20),
            duration_mins INTEGER,
            travel_mode VARCHAR(50),
            travel_duration_mins INTEGER,
            cost_inr INTEGER,
            carbon_kg DOUBLE PRECISION,
            special_note TEXT,
            is_locked INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS optimizer_weights (
            id SERIAL PRIMARY KEY,
            filter_name VARCHAR(100) NOT NULL UNIQUE,
            weight_time DOUBLE PRECISION,
            weight_cost DOUBLE PRECISION,
            weight_walking DOUBLE PRECISION,
            weight_carbon DOUBLE PRECISION,
            weight_value DOUBLE PRECISION,
            max_walking_distance_m INTEGER
        );

        CREATE TABLE IF NOT EXISTS languages (
            id SERIAL PRIMARY KEY,
            code VARCHAR(10) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL,
            local_name VARCHAR(100) NOT NULL,
            is_tts_supported INTEGER DEFAULT 1,
            is_default INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS currencies (
            id SERIAL PRIMARY KEY,
            code VARCHAR(10) NOT NULL UNIQUE,
            symbol VARCHAR(10) NOT NULL,
            exchange_rate_to_inr DOUBLE PRECISION,
            name VARCHAR(100)
        );

        CREATE TABLE IF NOT EXISTS bookmarks (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            poi_id INTEGER REFERENCES activities_poi(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS poi_feedback (
            id SERIAL PRIMARY KEY,
            poi_id INTEGER REFERENCES activities_poi(id),
            user_id INTEGER REFERENCES users(id),
            rating DOUBLE PRECISION,
            feedback_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- CANONICAL DYNAMIC RAG KNOWLEDGE LAYER
        CREATE TABLE IF NOT EXISTS entities (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            city_id INTEGER REFERENCES cities(id),
            city_name VARCHAR(100),
            region VARCHAR(100),
            country VARCHAR(100) DEFAULT 'India',
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            category VARCHAR(100),
            address TEXT,
            aliases JSONB DEFAULT '[]',
            source_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS knowledge_sources (
            id SERIAL PRIMARY KEY,
            source_name VARCHAR(255) NOT NULL,
            source_url TEXT NOT NULL,
            source_type VARCHAR(100) NOT NULL,
            authority_score DOUBLE PRECISION DEFAULT 0.85,
            verification_state VARCHAR(50) DEFAULT 'VERIFIED',
            retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published_at TIMESTAMP,
            expires_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS knowledge_documents (
            id SERIAL PRIMARY KEY,
            source_id INTEGER REFERENCES knowledge_sources(id),
            entity_id INTEGER REFERENCES entities(id),
            city_id INTEGER REFERENCES cities(id),
            title VARCHAR(255) NOT NULL,
            raw_content TEXT NOT NULL,
            content_hash VARCHAR(64) NOT NULL UNIQUE,
            content_type VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id SERIAL PRIMARY KEY,
            document_id INTEGER REFERENCES knowledge_documents(id),
            entity_id INTEGER REFERENCES entities(id),
            city_id INTEGER REFERENCES cities(id),
            topic VARCHAR(100),
            attribute VARCHAR(100),
            title VARCHAR(255) NOT NULL,
            chunk_text TEXT NOT NULL,
            source_name VARCHAR(255) NOT NULL,
            source_url TEXT,
            source_type VARCHAR(100),
            freshness_class VARCHAR(20) DEFAULT 'STATIC',
            confidence DOUBLE PRECISION DEFAULT 0.90,
            embedding DOUBLE PRECISION[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS web_cache (
            id SERIAL PRIMARY KEY,
            cache_key VARCHAR(255) NOT NULL UNIQUE,
            query VARCHAR(255) NOT NULL,
            entity_name VARCHAR(200),
            destination_name VARCHAR(100),
            payload_json JSONB NOT NULL,
            source_name VARCHAR(200),
            retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS operational_status (
            id SERIAL PRIMARY KEY,
            entity_id INTEGER REFERENCES entities(id),
            status VARCHAR(100) NOT NULL,
            open_time VARCHAR(20),
            close_time VARCHAR(20),
            schedule_detail TEXT,
            advisory_note TEXT,
            valid_until TIMESTAMP,
            source_id INTEGER REFERENCES knowledge_sources(id),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- INDEXES
        CREATE INDEX IF NOT EXISTS idx_entities_city ON entities(city_id);
        CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
        CREATE INDEX IF NOT EXISTS idx_chunks_city ON knowledge_chunks(city_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_entity ON knowledge_chunks(entity_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_attr ON knowledge_chunks(attribute);
        CREATE INDEX IF NOT EXISTS idx_web_cache_key ON web_cache(cache_key);
        """)
    conn.close()
    print("[OK] Canonical PostgreSQL Schema initialized.")

def reset_knowledge_corpus(url: Optional[str] = None):
    """
    DESTRUCTIVE RESET OF RAG KNOWLEDGE LAYER
    Completely drops and recreates all factual knowledge, chunks, documents, sources, embeddings, and web cache tables.
    Leaves the knowledge layer completely empty.
    """
    conn = get_pg_connection(url)
    with conn.cursor() as cur:
        cur.execute("""
        TRUNCATE TABLE knowledge_chunks CASCADE;
        TRUNCATE TABLE knowledge_documents CASCADE;
        TRUNCATE TABLE knowledge_sources CASCADE;
        TRUNCATE TABLE web_cache CASCADE;
        TRUNCATE TABLE operational_status CASCADE;
        TRUNCATE TABLE entities CASCADE;
        """)
    conn.close()
    print("[OK] Destructive Reset Complete: knowledge_chunks=0, knowledge_documents=0, knowledge_sources=0, web_cache=0, entities=0")

def seed_base_relational_data(url: Optional[str] = None):
    """Seeds baseline infrastructure (India, Languages, Currencies, Cities, User Profile, Optimizer Weights) without hardcoded factual answers."""
    conn = get_pg_connection(url)
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM countries")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO countries (code, name, currency_code, default_locale) VALUES ('IN', 'India', 'INR', 'en_IN') RETURNING id;")
            country_id = cur.fetchone()[0]
            
            cur.executemany("INSERT INTO languages (code, name, local_name, is_tts_supported, is_default) VALUES (%s, %s, %s, %s, %s);", [
                ('en', 'English', 'English', 1, 1),
                ('kn', 'Kannada', 'ಕನ್ನಡ', 1, 0),
                ('hi', 'Hindi', 'हिन्दी', 1, 0)
            ])

            cur.executemany("INSERT INTO currencies (code, symbol, exchange_rate_to_inr, name) VALUES (%s, %s, %s, %s);", [
                ('INR', '₹', 1.0, 'Indian Rupee'),
                ('USD', '$', 84.5, 'US Dollar'),
                ('EUR', '€', 92.0, 'Euro'),
                ('GBP', '£', 108.0, 'British Pound')
            ])

            cur.execute("""
            INSERT INTO cities (country_id, name, state, lat, lng, timezone, description, best_season, peak_months)
            VALUES 
                (%s, 'Hampi', 'Karnataka', 15.3350, 76.4600, 'Asia/Kolkata', 'UNESCO World Heritage Vijayanagara ruins', 'October to February', 'October to March'),
                (%s, 'Bengaluru', 'Karnataka', 12.9716, 77.5946, 'Asia/Kolkata', 'Silicon capital and Garden City of India', 'Pleasant year-round', 'September to March'),
                (%s, 'Mysuru', 'Karnataka', 12.2958, 76.6394, 'Asia/Kolkata', 'City of Palaces and royal heritage', 'October to March', 'October to March');
            """, (country_id, country_id, country_id))

            cur.execute("INSERT INTO users (name, email, avatar_url) VALUES ('Aarav', 'aarav@example.com', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150') RETURNING id;")
            user_id = cur.fetchone()[0]

            import json
            cur.execute("""
            INSERT INTO user_preferences (user_id, interests_json, budget_tier, pace, step_free_only, max_walking_km, avoid_midday_sun, language, voice_output)
            VALUES (%s, %s, 'medium', 'steady', 0, 2.0, 1, 'en', 1);
            """, (user_id, json.dumps(['History', 'Architecture', 'Photography', 'Landscape', 'Food', 'Living ritual'])))

            cur.execute("""
            INSERT INTO user_devices (user_id, device_token, platform, location_permission, last_lat, last_lng)
            VALUES (%s, 'dev-token-aarav', 'android_pwa', 1, 15.3352, 76.4603);
            """, (user_id,))

            categories_data = [
                ('Monuments & Temples', 'monuments', 'landmark', 'Ancient temples, stone carvings and ruins'),
                ('Hidden gems', 'hidden_gems', 'sparkles', 'Quiet spots, secluded trails and tranquil ruins'),
                ('Local Food & Dining', 'food', 'utensils', 'Authentic Karnataka cuisine and local delicacies'),
                ('Stays & Resorts', 'stays', 'hotel', 'Boutique heritage stays and riverside lodges'),
                ('Nature & Sunsets', 'nature', 'sun', 'Boulder viewpoints, riverbanks and scenic hills')
            ]
            cur.executemany("INSERT INTO categories (name, slug, icon, description) VALUES (%s, %s, %s, %s);", categories_data)

            weights_data = [
                ('balanced', 1.0, 1.0, 1.0, 1.0, 1.5, 1200),
                ('cheaper', 0.8, 3.0, 1.0, 1.0, 1.2, 1500),
                ('greener', 0.9, 1.0, 2.5, 3.5, 1.2, 2000),
                ('less_walking', 1.2, 0.8, 3.5, 0.5, 1.5, 700)
            ]
            cur.executemany("INSERT INTO optimizer_weights (filter_name, weight_time, weight_cost, weight_walking, weight_carbon, weight_value, max_walking_distance_m) VALUES (%s, %s, %s, %s, %s, %s, %s);", weights_data)

            # Insert baseline trip
            cur.execute("SELECT id FROM cities WHERE name='Hampi'")
            hampi_id = cur.fetchone()[0]
            cur.execute("INSERT INTO trips (user_id, city_id, title, budget_spent_inr, sites_seen_count) VALUES (%s, %s, 'Solo Explorer', 1180, 4) RETURNING id;", (user_id, hampi_id))
            trip_id = cur.fetchone()[0]
            cur.execute("INSERT INTO itineraries (trip_id, user_id, title, date, duration_type, optimization_filter, total_duration_mins, total_cost_inr, total_walking_km, total_carbon_kg, note) VALUES (%s, %s, 'Heritage Tour', '2026-09-01', 'full_day', 'balanced', 490, 337, 3.3, 0.70, 'Grounded itinerary');", (trip_id, user_id))

    conn.close()
    print("[OK] Baseline Relational Infrastructure Seeded in PostgreSQL.")

if __name__ == '__main__':
    init_postgres_schema()
    seed_base_relational_data()
