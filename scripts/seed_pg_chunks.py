import sqlite3
import psycopg2
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.vector_store import compute_text_embedding

def seed_postgres_knowledge():
    print("Connecting to SQLite source and PostgreSQL...")
    s_conn = sqlite3.connect('data/source/ps13_original.sqlite')
    s_conn.row_factory = sqlite3.Row
    p_conn = psycopg2.connect('postgresql://geoguide:geoguide@127.0.0.1:5432/geoguide')
    p_conn.autocommit = True
    
    s_cur = s_conn.cursor()
    p_cur = p_conn.cursor()

    # Clear existing synthetic chunks to have a clean, authoritative set
    p_cur.execute("DELETE FROM knowledge_chunks WHERE source_type IN ('gazetteer', 'monograph', 'official_registry');")

    # Ensure all POIs from activities_poi exist in entities table
    p_cur.execute("""
    INSERT INTO entities (id, name, entity_type, city_id, city_name, latitude, longitude, category, address)
    SELECT p.id, p.name, 'POI', p.city_id, c.name, p.lat, p.lng, 'Heritage / POI', p.short_desc
    FROM activities_poi p
    LEFT JOIN cities c ON p.city_id = c.id
    ON CONFLICT (id) DO UPDATE SET 
        name = EXCLUDED.name,
        city_id = EXCLUDED.city_id,
        latitude = EXCLUDED.latitude,
        longitude = EXCLUDED.longitude;
    """)

    # 1. Seed Place KB
    s_cur.execute("SELECT * FROM place_kb")
    pkbs = s_cur.fetchall()
    for r in pkbs:
        content_clean = r['content'].replace('?30', '₹30').replace('?500', '₹500').replace('?2', '₹2').replace('?50', '₹50')
        emb = compute_text_embedding(f"{r['title']} {r['topic']} {content_clean}")
        p_cur.execute("""
        INSERT INTO knowledge_chunks (city_id, topic, attribute, title, chunk_text, source_name, source_type, freshness_class, confidence, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (r['city_id'], r['topic'], 'GENERAL', r['title'], content_clean, r['source_citation'], 'gazetteer', 'STATIC', 0.95, emb))
    print(f"[OK] Ingested {len(pkbs)} place_kb chunks into PostgreSQL with dense embeddings.")

    # 2. Seed POI Facts KB
    s_cur.execute("SELECT f.*, p.name as poi_name, p.city_id FROM poi_facts_kb f JOIN activities_poi p ON f.poi_id = p.id")
    facts = s_cur.fetchall()
    for f in facts:
        emb = compute_text_embedding(f"{f['poi_name']} {f['fact_title']} {f['fact_detail']}")
        p_cur.execute("""
        INSERT INTO knowledge_chunks (city_id, entity_id, topic, attribute, title, chunk_text, source_name, source_type, freshness_class, confidence, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (f['city_id'], f['poi_id'], 'poi_fact', 'FACT', f"{f['poi_name']} - {f['fact_title']}", f['fact_detail'], f['source_name'], 'monograph', 'STATIC', 0.95, emb))
    print(f"[OK] Ingested {len(facts)} poi_facts chunks into PostgreSQL with dense embeddings.")

    # 3. Seed activities_poi as knowledge chunks
    p_cur.execute("SELECT id, city_id, name, short_desc, full_desc, ticket_policy, open_time, close_time, entry_fee_inr FROM activities_poi")
    pois = p_cur.fetchall()
    for p in pois:
        poi_id, city_id, name, s_desc, f_desc, ticket, op_t, cl_t, fee = p
        text = f"{name}: {s_desc} {f_desc} Ticket Policy: {ticket} Hours: {op_t} to {cl_t} Entry fee: ₹{fee}"
        emb = compute_text_embedding(f"{name} {text}")
        p_cur.execute("""
        INSERT INTO knowledge_chunks (city_id, entity_id, topic, attribute, title, chunk_text, source_name, source_type, freshness_class, confidence, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (city_id, poi_id, 'poi_detail', 'POI_OVERVIEW', name, text, 'ASI / Official Tourism Registry', 'official_registry', 'STATIC', 0.95, emb))
    print(f"[OK] Ingested {len(pois)} POI profiles as knowledge_chunks into PostgreSQL.")

    s_conn.close()
    p_conn.close()
    print("Database seeding completed.")

if __name__ == '__main__':
    seed_postgres_knowledge()
