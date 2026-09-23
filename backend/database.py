import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), 'geoguide.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        currency_code TEXT NOT NULL,
        default_locale TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS cities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_id INTEGER,
        name TEXT NOT NULL,
        state TEXT NOT NULL,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        timezone TEXT NOT NULL,
        description TEXT,
        best_season TEXT,
        peak_months TEXT,
        FOREIGN KEY(country_id) REFERENCES countries(id)
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        avatar_url TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS user_devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        device_token TEXT,
        platform TEXT,
        location_permission INTEGER DEFAULT 1,
        last_lat REAL,
        last_lng REAL,
        last_active TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS user_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        interests_json TEXT,
        budget_tier TEXT,
        pace TEXT,
        step_free_only INTEGER DEFAULT 0,
        max_walking_km REAL DEFAULT 2.0,
        avoid_midday_sun INTEGER DEFAULT 1,
        language TEXT DEFAULT 'en',
        voice_output INTEGER DEFAULT 1,
        updated_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT NOT NULL UNIQUE,
        icon TEXT,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS activities_poi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_id INTEGER,
        category_id INTEGER,
        name TEXT NOT NULL,
        tag_badge TEXT,
        short_desc TEXT,
        full_desc TEXT,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        distance_km REAL,
        travel_time_mins INTEGER,
        travel_mode TEXT,
        est_duration_mins INTEGER,
        entry_fee_inr INTEGER DEFAULT 0,
        entry_fee_foreign_inr INTEGER DEFAULT 0,
        is_step_free INTEGER DEFAULT 0,
        terrain_type TEXT,
        best_time_window TEXT,
        open_time TEXT,
        close_time TEXT,
        ticket_policy TEXT,
        rating REAL DEFAULT 4.5,
        review_count INTEGER DEFAULT 120,
        carbon_kg REAL DEFAULT 0.0,
        image_url TEXT,
        audio_intro_url TEXT,
        FOREIGN KEY(city_id) REFERENCES cities(id),
        FOREIGN KEY(category_id) REFERENCES categories(id)
    );

    CREATE TABLE IF NOT EXISTS hotels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_id INTEGER,
        name TEXT NOT NULL,
        category TEXT,
        price_per_night INTEGER,
        rating REAL,
        distance_desc TEXT,
        lat REAL,
        lng REAL,
        image_url TEXT,
        access_note TEXT,
        FOREIGN KEY(city_id) REFERENCES cities(id)
    );

    CREATE TABLE IF NOT EXISTS weather_daily (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_id INTEGER,
        date TEXT NOT NULL,
        temp_c INTEGER,
        feels_like_c INTEGER,
        condition TEXT,
        humidity_pct INTEGER,
        sunrise TEXT,
        sunset TEXT,
        daylight_hours TEXT,
        uv_index INTEGER,
        uv_alert_until TEXT,
        season_summary TEXT,
        advice_text TEXT,
        FOREIGN KEY(city_id) REFERENCES cities(id)
    );

    CREATE TABLE IF NOT EXISTS events_festivals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_id INTEGER,
        name TEXT NOT NULL,
        date_start TEXT,
        date_end TEXT,
        location_desc TEXT,
        description TEXT,
        impact_level TEXT,
        FOREIGN KEY(city_id) REFERENCES cities(id)
    );

    CREATE TABLE IF NOT EXISTS safety_advisories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_id INTEGER,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        severity TEXT NOT NULL,
        advisory_type TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        valid_until TEXT,
        detour_advice TEXT,
        FOREIGN KEY(city_id) REFERENCES cities(id)
    );


    CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        city_id INTEGER,
        title TEXT,
        start_date TEXT,
        end_date TEXT,
        budget_spent_inr INTEGER DEFAULT 0,
        sites_seen_count INTEGER DEFAULT 0,
        saved_count INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(city_id) REFERENCES cities(id)
    );

    CREATE TABLE IF NOT EXISTS itineraries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trip_id INTEGER,
        user_id INTEGER,
        title TEXT,
        date TEXT,
        duration_type TEXT,
        optimization_filter TEXT,
        total_duration_mins INTEGER,
        total_cost_inr INTEGER,
        total_walking_km REAL,
        total_carbon_kg REAL,
        note TEXT,
        FOREIGN KEY(trip_id) REFERENCES trips(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS itinerary_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        itinerary_id INTEGER,
        poi_id INTEGER,
        stop_order INTEGER,
        start_time TEXT,
        end_time TEXT,
        duration_mins INTEGER,
        travel_mode TEXT,
        travel_duration_mins INTEGER,
        cost_inr INTEGER,
        carbon_kg REAL,
        special_note TEXT,
        is_locked INTEGER DEFAULT 0,
        FOREIGN KEY(itinerary_id) REFERENCES itineraries(id),
        FOREIGN KEY(poi_id) REFERENCES activities_poi(id)
    );

    CREATE TABLE IF NOT EXISTS optimizer_weights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filter_name TEXT NOT NULL UNIQUE,
        weight_time REAL,
        weight_cost REAL,
        weight_walking REAL,
        weight_carbon REAL,
        weight_value REAL,
        max_walking_distance_m INTEGER
    );

    CREATE TABLE IF NOT EXISTS languages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        local_name TEXT NOT NULL,
        is_tts_supported INTEGER DEFAULT 1,
        is_default INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS currencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        symbol TEXT NOT NULL,
        exchange_rate_to_inr REAL,
        name TEXT
    );
    """)

    conn.commit()
    seed_data(conn)
    conn.close()

def seed_data(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM cities")
    if cursor.fetchone()[0] > 0:
        return

    # Countries
    cursor.execute("INSERT INTO countries (code, name, currency_code, default_locale) VALUES ('IN', 'India', 'INR', 'en_IN')")
    country_id = cursor.lastrowid

    # Languages
    cursor.executemany("INSERT INTO languages (code, name, local_name, is_tts_supported, is_default) VALUES (?, ?, ?, ?, ?)", [
        ('en', 'English', 'English', 1, 1),
        ('kn', 'Kannada', '?????', 1, 0),
        ('hi', 'Hindi', '??????', 1, 0)
    ])

    # Currencies
    cursor.executemany("INSERT INTO currencies (code, symbol, exchange_rate_to_inr, name) VALUES (?, ?, ?, ?)", [
        ('INR', '?', 1.0, 'Indian Rupee'),
        ('USD', '$', 84.5, 'US Dollar'),
        ('EUR', '?', 92.0, 'Euro'),
        ('GBP', '?', 108.0, 'British Pound')
    ])

    # Cities
    cursor.execute("""
    INSERT INTO cities (country_id, name, state, lat, lng, timezone, description, best_season, peak_months)
    VALUES (?, 'Hampi', 'Karnataka', 15.3350, 76.4600, 'Asia/Kolkata', 
    'Hampi is the site of Vijayanagara, capital of the empire that ruled southern India from 1336 to 1565 and one of the largest cities in the world at its peak. Around 1,600 surviving monuments ? temples, bazaars, aqueducts and royal enclosures ? lie scattered across boulder hills, preserved because the capital was abandoned after 1565 and never rebuilt, which is why the ruins survive as a time capsule.',
    'Late monsoon ? Best season October to February',
    'October to March')
    """, (country_id,))
    hampi_id = cursor.lastrowid

    # Users & Preferences
    cursor.execute("INSERT INTO users (name, email, avatar_url, created_at) VALUES ('Aarav', 'aarav@example.com', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150', '2026-08-25')")
    user_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO user_preferences (user_id, interests_json, budget_tier, pace, step_free_only, max_walking_km, avoid_midday_sun, language, voice_output, updated_at)
    VALUES (?, ?, 'medium', 'steady', 0, 2.0, 1, 'en', 1, '2026-08-31 10:56:00')
    """, (user_id, json.dumps(['History', 'Architecture', 'Photography', 'Landscape', 'Food', 'Living ritual'])))

    cursor.execute("""
    INSERT INTO user_devices (user_id, device_token, platform, location_permission, last_lat, last_lng, last_active)
    VALUES (?, 'dev-token-aarav', 'android_pwa', 1, 15.3352, 76.4603, '2026-08-31 10:56:00')
    """, (user_id,))

    # Categories
    categories_data = [
        ('Monuments & Temples', 'monuments', 'landmark', 'Ancient temples, stone carvings and ruins'),
        ('Hidden gems', 'hidden_gems', 'sparkles', 'Quiet spots, secluded trails and tranquil ruins'),
        ('Local Food & Dining', 'food', 'utensils', 'Authentic Karnataka cuisine and local delicacies'),
        ('Stays & Resorts', 'stays', 'hotel', 'Boutique heritage stays and riverside lodges'),
        ('Nature & Sunsets', 'nature', 'sun', 'Boulder viewpoints, riverbanks and scenic hills')
    ]
    cursor.executemany("INSERT INTO categories (name, slug, icon, description) VALUES (?, ?, ?, ?)", categories_data)

    cat_monuments, cat_hidden, cat_food, cat_stays, cat_nature = 1, 2, 3, 4, 5

    # Activities & POIs
    pois_data = [
        (hampi_id, cat_monuments, 'Vittala Temple', 'Top pick', 
         'Stone Chariot and 56 pillars that ring like notes.',
         'The pinnacle of Vijayanagara art, featuring the iconic Stone Chariot, musical pillared hall, and vast carved courtyard. Shares admission with the Zenana enclosure.',
         15.3400, 76.4800, 2.6, 12, 'cycle', 150, 30, 500, 0, 'Stone walkways & dirt trail', '08:30-11:30 & 15:30-17:00', '08:30', '17:00', 'Shared ASI single-day ticket with Zenana enclosure', 4.9, 2450, 0.0, 'https://images.unsplash.com/photo-1600100397608-f010e42f9b1c?w=600', '/audio/vittala.mp3'),

        (hampi_id, cat_monuments, 'Virupaksha Temple', 'Open now', 
         'In worship for centuries, with a 50 m eastern gopura.',
         'One of India oldest continuously functioning temples dedicated to Lord Shiva. Towering 50m gopura, living elephant Lakshmi, pinhole camera effect chamber.',
         15.3353, 76.4600, 0.2, 3, 'walk', 45, 2, 2, 0, 'Granite floors & steps', '06:00-12:30 & 17:00-20:00', '06:00', '20:00', 'Separate temple ticket ?2; camera fee ?50', 4.8, 3100, 0.0, 'https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?w=600', '/audio/virupaksha.mp3'),

        (hampi_id, cat_monuments, 'Lotus Mahal', 'Step-free', 
         'Zenana enclosure and the Elephant Stables, on level lawns.',
         'Graceful Indo-Islamic architecture with geometric arches, surrounded by lush manicured lawns and the expansive 11-domed Elephant Stables.',
         15.3200, 76.4700, 3.5, 10, 'auto', 60, 30, 500, 1, 'Level paved lawns, step-free access', '08:30-17:00', '08:30', '17:00', 'Shared ASI single-day ticket with Vittala Temple', 4.7, 1820, 0.15, 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=600', '/audio/lotus_mahal.mp3'),

        (hampi_id, cat_nature, 'Matanga Hill', 'Steep', 
         'The highest point over the ruins. Best at first light.',
         'Spectacular 360-degree panoramic view of the entire Vijayanagara landscape, boulder fields, and the winding Tungabhadra River. Best for sunrise.',
         15.3320, 76.4650, 0.7, 25, 'climb', 90, 0, 0, 0, 'Steep boulder staircase, no handrails', '05:30-08:30 & 17:00-18:45', '05:30', '19:00', 'Free entry, public access', 4.9, 1400, 0.0, 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=600', '/audio/matanga.mp3'),

        (hampi_id, cat_nature, 'Hemakuta Hill', 'Sunset spot', 
         'Terraced shrines two minutes above the bazaar. Easy underfoot.',
         'Cluster of early pre-Vijayanagara triple-chambered shrines on a gentle granite slope overlooking Virupaksha Temple. Ideal for peaceful sunset vistas.',
         15.3340, 76.4580, 0.4, 6, 'walk', 40, 0, 0, 1, 'Gentle granite slope, mostly step-free', '06:00-18:45', '06:00', '19:00', 'Free entry', 4.8, 980, 0.0, 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600', '/audio/hemakuta.mp3'),

        (hampi_id, cat_hidden, 'Underground Shiva Temple', 'In the shade', 
         'Sunken and cool, the right place to sit out the worst of the sun.',
         'Also known as Prasanna Virupaksha Temple. Situated several meters below ground level, surrounded by green lawns and filled with cooling water during monsoon.',
         15.3250, 76.4640, 1.8, 8, 'auto', 40, 0, 0, 0, 'Sunken stone corridor, cool water floor', '08:30-17:30', '08:30', '17:30', 'Free entry', 4.6, 620, 0.10, 'https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=600', '/audio/underground_shiva.mp3'),

        (hampi_id, cat_monuments, 'Hazara Rama relief panels', 'Intricate carvings', 
         'Ramayana carved in bands around the royal chapel walls.',
         'The private temple of the Vijayanagara royalty, celebrated for thousands of stone relief panels depicting scenes from the Ramayana and royal processions.',
         15.3210, 76.4670, 2.2, 7, 'walk', 30, 0, 0, 1, 'Level stone paths, easy access', '08:30-17:30', '08:30', '17:30', 'Free entry', 4.7, 750, 0.0, 'https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?w=600', '/audio/hazara_rama.mp3'),

        (hampi_id, cat_hidden, 'Sasivekalu Ganesha', 'Monolith', 
         'Single-stone monolithic Ganesha carved with an open pillared mandapa.',
         'Monolithic Ganesha with a snake carved around the belly, set on the slopes of Hemakuta Hill overlooking Hampi Bazaar.',
         15.3330, 76.4590, 0.5, 8, 'walk', 30, 0, 0, 1, 'Short paved slope', '06:00-18:00', '06:00', '18:00', 'Free entry', 4.6, 540, 0.0, 'https://images.unsplash.com/photo-1564507592333-c60657eea523?w=600', '/audio/ganesha.mp3'),

        (hampi_id, cat_nature, 'Anegundi Village', 'Hippie trail', 
         'Ancient Kishkindha kingdom across the river with rural heritage charm.',
         'Historical fortified town across the Tungabhadra with traditional houses, Pampa Sarovar, and boulder valleys.',
         15.3500, 76.4950, 6.8, 35, 'auto', 120, 0, 0, 0, 'Rural roads and rugged trails', '07:00-18:00', '07:00', '18:30', 'Free entry', 4.7, 890, 0.45, 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600', '/audio/anegundi.mp3')
    ]

    cursor.executemany("""
    INSERT INTO activities_poi (
        city_id, category_id, name, tag_badge, short_desc, full_desc, lat, lng,
        distance_km, travel_time_mins, travel_mode, est_duration_mins, entry_fee_inr,
        entry_fee_foreign_inr, is_step_free, terrain_type, best_time_window, open_time,
        close_time, ticket_policy, rating, review_count, carbon_kg, image_url, audio_intro_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, pois_data)

    food_data = [
        (hampi_id, cat_food, 'Jolada rotti with ennegayi', 'Local staple',
         'Millet flatbread with stuffed brinjal, the staple of this part of Karnataka.',
         'Served at the family kitchens on Hampi Bazaar from 12:00. Around ?180 for a full plate. Hampi Bazaar, 300 m ? Vegetarian ? No alcohol in the core zone.',
         15.3355, 76.4608, 0.3, 4, 'walk', 45, 180, 180, 1, 'Paved street level', '12:00-15:00 & 19:00-21:30', '12:00', '21:30', 'Pay per meal, Cash & UPI', 4.8, 510, 0.05, 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600', '/audio/food_jolada.mp3'),

        (hampi_id, cat_food, 'Thatte idli and Kalyana oota', 'Breakfast special',
         'Plate-sized idli in Hospet, 13 km away, and banana-leaf meals at Kamalapura.',
         'Plate-sized idli in Hospet, 13 km away, and banana-leaf meals at Kamalapura on festival days. Best before 10:30, when the batter is fresh. Hospet, 13 km ? ?60??120 ? Cash preferred.',
         15.3100, 76.4300, 13.0, 25, 'auto', 45, 90, 90, 1, 'Restaurant ground floor', '07:00-11:00', '07:00', '11:00', 'Cash & UPI', 4.7, 340, 0.30, 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600', '/audio/food_idli.mp3')
    ]
    cursor.executemany("""
    INSERT INTO activities_poi (
        city_id, category_id, name, tag_badge, short_desc, full_desc, lat, lng,
        distance_km, travel_time_mins, travel_mode, est_duration_mins, entry_fee_inr,
        entry_fee_foreign_inr, is_step_free, terrain_type, best_time_window, open_time,
        close_time, ticket_policy, rating, review_count, carbon_kg, image_url, audio_intro_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, food_data)

    hotels_data = [
        (hampi_id, 'Boulder-side resort', 'Boutique Heritage Resort', 6500, 4.6, 'Kamalapura, 4.2 km', 15.3120, 76.4750, 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600', 'Level access, serene boulder surroundings'),
        (hampi_id, 'Bazaar guesthouse', 'Heritage Homestay', 1200, 4.3, 'Hampi Bazaar, 200 m', 15.3356, 76.4610, 'https://images.unsplash.com/photo-1582719508461-905c673771fd?w=600', 'Virupapur Gaddi guesthouses across the river are hard to reach while the ferry is suspended.')
    ]
    cursor.executemany("INSERT INTO hotels (city_id, name, category, price_per_night, rating, distance_desc, lat, lng, image_url, access_note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", hotels_data)

    cursor.execute("""
    INSERT INTO weather_daily (city_id, date, temp_c, feels_like_c, condition, humidity_pct, sunrise, sunset, daylight_hours, uv_index, uv_alert_until, season_summary, advice_text)
    VALUES (?, '2026-08-31', 28, 32, 'Partly cloudy', 74, '06:14', '18:41', '7h 45 Daylight left', 8, '15:30',
    'Late monsoon ? Best season October to February',
    'The landscape is at its greenest and crowds are thin, but granite is slick after evening showers and the river is running high. May touches 40?C, so the ruins are best walked now or after October.')
    """, (hampi_id,))

    events_data = [
        (hampi_id, 'Janmashtami, 4 September', '2026-09-04', '2026-09-04', 'Virupaksha Bazaar', 'Night processions along Virupaksha Bazaar, then Ganesh Chaturthi rituals at the Sasivekalu Ganesha on 14 September. Hampi Utsav follows in November.', 'High'),
        (hampi_id, 'Ganesh Chaturthi', '2026-09-14', '2026-09-14', 'Sasivekalu Ganesha', 'Special poojas and heritage gatherings at the monolithic Ganesha shrines.', 'Medium'),
        (hampi_id, 'Hampi Utsav', '2026-11-03', '2026-11-05', 'Monuments', 'Grand cultural festival with music, lighting and dance.', 'Peak')
    ]
    cursor.executemany("INSERT INTO events_festivals (city_id, name, date_start, date_end, location_desc, description, impact_level) VALUES (?, ?, ?, ?, ?, ?, ?)", events_data)

    safety_data = [
        (hampi_id, 'Coracle crossings suspended', 'The Tungabhadra is in spate after upstream releases. Cross to Anegundi by the Bukkasagara road bridge instead ? 40 minutes by auto.', 'warning', 'transport', 1, '2026-09-05', 'Bukkasagara road bridge (40 min auto)'),
        (hampi_id, 'High UV until 15:30', 'There is almost no shade on the boulder trails. Climb Matanga or Anjanadri before 10:00, and carry two litres of water.', 'advisory', 'weather_heat', 1, '2026-08-31 15:30:00', 'Carry water, wear hats'),
        (hampi_id, 'Ticketed sites stop entry in 6 h 04 min', 'Vittala Temple and the Zenana enclosure share one ASI ticket and stop entry at 17:00. Free monuments stay open until dusk.', 'info', 'ticketing_hours', 1, '2026-08-31 17:00:00', 'Buy shared ASI ticket before 16:30')
    ]
    cursor.executemany("INSERT INTO safety_advisories (city_id, title, description, severity, advisory_type, is_active, valid_until, detour_advice) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", safety_data)


    weights_data = [
        ('balanced', 1.0, 1.0, 1.0, 1.0, 1.5, 1200),
        ('cheaper', 0.8, 3.0, 1.0, 1.0, 1.2, 1500),
        ('greener', 0.9, 1.0, 2.5, 3.5, 1.2, 2000),
        ('less_walking', 1.2, 0.8, 3.5, 0.5, 1.5, 700)
    ]
    cursor.executemany("INSERT INTO optimizer_weights (filter_name, weight_time, weight_cost, weight_walking, weight_carbon, weight_value, max_walking_distance_m) VALUES (?, ?, ?, ?, ?, ?, ?)", weights_data)

    cursor.execute("""
    INSERT INTO trips (user_id, city_id, title, start_date, end_date, budget_spent_inr, sites_seen_count, saved_count)
    VALUES (?, ?, 'Solo Hampi Explorer', '2026-08-27', '2026-08-30', 1180, 7, 0)
    """, (user_id, hampi_id))
    trip_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO itineraries (trip_id, user_id, title, date, duration_type, optimization_filter, total_duration_mins, total_cost_inr, total_walking_km, total_carbon_kg, note)
    VALUES (?, ?, 'Tomorrow, 06:00 to 19:00 ? Less walking ? ends 18:40', '2026-09-01', 'full_day', 'less_walking', 490, 337, 3.3, 0.70, 'Under 700 m on foot per stop, with vehicle drops close to each gate.')
    """, (trip_id, user_id))
    itinerary_id = cursor.lastrowid

    itinerary_items_data = [
        (itinerary_id, 6, 1, '13:05', '13:45', 40, 'auto', 10, 0, 0.10, 'Sunken and cool, the right place to sit out the worst of the sun.', 0),
        (itinerary_id, 3, 2, '14:00', '15:00', 60, 'auto', 15, 0, 0.15, 'Level lawns, one ticket shared with Vittala, shade along the wall.', 0),
        (itinerary_id, 7, 3, '15:15', '15:45', 30, 'walk', 5, 0, 0.00, 'Ramayana carved in bands around the royal chapel walls.', 0),
        (itinerary_id, 5, 4, '18:00', '18:40', 40, 'walk', 10, 0, 0.00, 'Terraced shrines two minutes above the bazaar. Easy underfoot.', 0)
    ]
    cursor.executemany("""
    INSERT INTO itinerary_items (itinerary_id, poi_id, stop_order, start_time, end_time, duration_mins, travel_mode, travel_duration_mins, cost_inr, carbon_kg, special_note, is_locked)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, itinerary_items_data)

    conn.commit()

if __name__ == '__main__':
    init_db()
    print('Database initialized.')
