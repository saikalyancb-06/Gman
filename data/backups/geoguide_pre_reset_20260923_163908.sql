BEGIN TRANSACTION;
CREATE TABLE activities_poi (
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
INSERT INTO "activities_poi" VALUES(1,1,1,'Vittala Temple','Top pick','Stone Chariot and 56 pillars that ring like notes.','The pinnacle of Vijayanagara art, featuring the iconic Stone Chariot, musical pillared hall, and vast carved courtyard. Shares admission with the Zenana enclosure.',15.34,76.48,2.6,12,'cycle',150,30,500,0,'Stone walkways & dirt trail','08:30-11:30 & 15:30-17:00','08:30','17:00','Shared ASI single-day ticket with Zenana enclosure',4.9,2450,0.0,'https://images.unsplash.com/photo-1600100397608-f010e42f9b1c?w=600','/audio/vittala.mp3');
INSERT INTO "activities_poi" VALUES(2,1,1,'Virupaksha Temple','Open now','In worship for centuries, with a 50 m eastern gopura.','One of India oldest continuously functioning temples dedicated to Lord Shiva. Towering 50m gopura, living elephant Lakshmi, pinhole camera effect chamber.',15.3353,76.46,0.2,3,'walk',45,2,2,0,'Granite floors & steps','06:00-12:30 & 17:00-20:00','06:00','20:00','Separate temple ticket ?2; camera fee ?50',4.8,3100,0.0,'https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?w=600','/audio/virupaksha.mp3');
INSERT INTO "activities_poi" VALUES(3,1,1,'Lotus Mahal','Step-free','Zenana enclosure and the Elephant Stables, on level lawns.','Graceful Indo-Islamic architecture with geometric arches, surrounded by lush manicured lawns and the expansive 11-domed Elephant Stables.',15.32,76.47,3.5,10,'auto',60,30,500,1,'Level paved lawns, step-free access','08:30-17:00','08:30','17:00','Shared ASI single-day ticket with Vittala Temple',4.7,1820,0.15,'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=600','/audio/lotus_mahal.mp3');
INSERT INTO "activities_poi" VALUES(4,1,5,'Matanga Hill','Steep','The highest point over the ruins. Best at first light.','Spectacular 360-degree panoramic view of the entire Vijayanagara landscape, boulder fields, and the winding Tungabhadra River. Best for sunrise.',15.332,76.465,0.7,25,'climb',90,0,0,0,'Steep boulder staircase, no handrails','05:30-08:30 & 17:00-18:45','05:30','19:00','Free entry, public access',4.9,1400,0.0,'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=600','/audio/matanga.mp3');
INSERT INTO "activities_poi" VALUES(5,1,5,'Hemakuta Hill','Sunset spot','Terraced shrines two minutes above the bazaar. Easy underfoot.','Cluster of early pre-Vijayanagara triple-chambered shrines on a gentle granite slope overlooking Virupaksha Temple. Ideal for peaceful sunset vistas.',15.334,76.458,0.4,6,'walk',40,0,0,1,'Gentle granite slope, mostly step-free','06:00-18:45','06:00','19:00','Free entry',4.8,980,0.0,'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600','/audio/hemakuta.mp3');
INSERT INTO "activities_poi" VALUES(6,1,2,'Underground Shiva Temple','In the shade','Sunken and cool, the right place to sit out the worst of the sun.','Also known as Prasanna Virupaksha Temple. Situated several meters below ground level, surrounded by green lawns and filled with cooling water during monsoon.',15.325,76.464,1.8,8,'auto',40,0,0,0,'Sunken stone corridor, cool water floor','08:30-17:30','08:30','17:30','Free entry',4.6,620,0.1,'https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=600','/audio/underground_shiva.mp3');
INSERT INTO "activities_poi" VALUES(7,1,1,'Hazara Rama relief panels','Intricate carvings','Ramayana carved in bands around the royal chapel walls.','The private temple of the Vijayanagara royalty, celebrated for thousands of stone relief panels depicting scenes from the Ramayana and royal processions.',15.321,76.467,2.2,7,'walk',30,0,0,1,'Level stone paths, easy access','08:30-17:30','08:30','17:30','Free entry',4.7,750,0.0,'https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?w=600','/audio/hazara_rama.mp3');
INSERT INTO "activities_poi" VALUES(8,1,2,'Sasivekalu Ganesha','Monolith','Single-stone monolithic Ganesha carved with an open pillared mandapa.','Monolithic Ganesha with a snake carved around the belly, set on the slopes of Hemakuta Hill overlooking Hampi Bazaar.',15.333,76.459,0.5,8,'walk',30,0,0,1,'Short paved slope','06:00-18:00','06:00','18:00','Free entry',4.6,540,0.0,'https://images.unsplash.com/photo-1564507592333-c60657eea523?w=600','/audio/ganesha.mp3');
INSERT INTO "activities_poi" VALUES(9,1,5,'Anegundi Village','Hippie trail','Ancient Kishkindha kingdom across the river with rural heritage charm.','Historical fortified town across the Tungabhadra with traditional houses, Pampa Sarovar, and boulder valleys.',15.35,76.495,6.8,35,'auto',120,0,0,0,'Rural roads and rugged trails','07:00-18:00','07:00','18:30','Free entry',4.7,890,0.45,'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600','/audio/anegundi.mp3');
INSERT INTO "activities_poi" VALUES(10,1,3,'Jolada rotti with ennegayi','Local staple','Millet flatbread with stuffed brinjal, the staple of this part of Karnataka.','Served at the family kitchens on Hampi Bazaar from 12:00. Around ?180 for a full plate. Hampi Bazaar, 300 m ? Vegetarian ? No alcohol in the core zone.',15.3355,76.4608,0.3,4,'walk',45,180,180,1,'Paved street level','12:00-15:00 & 19:00-21:30','12:00','21:30','Pay per meal, Cash & UPI',4.8,510,0.05,'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600','/audio/food_jolada.mp3');
INSERT INTO "activities_poi" VALUES(11,1,3,'Thatte idli and Kalyana oota','Breakfast special','Plate-sized idli in Hospet, 13 km away, and banana-leaf meals at Kamalapura.','Plate-sized idli in Hospet, 13 km away, and banana-leaf meals at Kamalapura on festival days. Best before 10:30, when the batter is fresh. Hospet, 13 km ? ?60??120 ? Cash preferred.',15.31,76.43,13.0,25,'auto',45,90,90,1,'Restaurant ground floor','07:00-11:00','07:00','11:00','Cash & UPI',4.7,340,0.3,'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600','/audio/food_idli.mp3');
INSERT INTO "activities_poi" VALUES(12,2,5,'Lalbagh Botanical Garden & Glass House','Top pick','240 acres of century-old trees and the iconic 1889 London Crystal Palace replica.','Commissioned by Hyder Ali and expanded by Tipu Sultan. Features a 3,000-million-year-old Peninsular Gneiss rock hill, lake, bonsai gardens, and the royal Glass House.',12.9507,77.5848,1.8,8,'metro',120,30,300,1,'Smooth paved level pathways, step-free','06:00-09:00 (Free walk) & 09:00-18:00 (Ticketed)','06:00','19:00','Ticket ₹30 for adults; battery buggies available for seniors',4.8,4820,0.05,'https://images.unsplash.com/photo-1596176530529-78163a4f7af2?w=600','/audio/lalbagh.mp3');
INSERT INTO "activities_poi" VALUES(13,2,1,'Bengaluru Palace','Tudor Heritage','Tudor-style wooden carvings, turreted parapets, and royal Chamarajendra Wodeyar history.','Built in 1878, inspired by Windsor Castle. Filled with fortified towers, stained glass, elegant wood carvings, and personal memorabilia of the Mysore royal family.',12.9988,77.5921,3.2,12,'auto',90,250,500,0,'Granite steps and wooden corridors','10:00-17:30','10:00','17:30','Entry ₹250 (Indians) / ₹500 (Foreigners); Audio guide included',4.6,3200,0.15,'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=600','/audio/palace.mp3');
INSERT INTO "activities_poi" VALUES(14,2,5,'Cubbon Park & State Library','Green lung','300 acres of tranquil bamboo groves, heritage bandstand, and red brick State Central Library.','Created in 1870 by Major General Richard Sankey. Step-free walking avenues, shade canopy, and peaceful green lawns right in the heart of Bengaluru.',12.9763,77.5929,0.8,5,'walk',60,0,0,1,'Paved level jogging and wheelchair promenades','06:00-19:00','06:00','20:00','Free entry; Motor vehicles restricted inside',4.8,5100,0.0,'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600','/audio/cubbon.mp3');
INSERT INTO "activities_poi" VALUES(15,2,1,'Tipu Sultan Summer Palace','Teak architecture','Two-storey wooden palace constructed entirely of French-carved teakwood pillars.','Constructed inside Bangalore Fort in 1791. Features ornate floral wooden arches, gilded balcony chambers, and historical museum exhibits on the Anglo-Mysore wars.',12.9593,77.5738,2.4,10,'auto',45,20,250,0,'Stone steps to upper wooden balcony','08:30-17:30','08:30','17:30','ASI ticket ₹20 (Indians) / ₹250 (Foreigners)',4.5,1420,0.1,'https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=600','/audio/tipu_palace.mp3');
INSERT INTO "activities_poi" VALUES(16,2,2,'National Gallery of Modern Art (NGMA)','Art & Heritage','Colonial Manikyavelu Mansion housing 500+ Indian modern masterpieces on manicured lawns.','Showcases masterworks by Raja Ravi Varma, Amrita Sher-Gil, and Rabindranath Tagore, surrounded by ancient trees, fountains, and a serene garden cafe.',12.9897,77.5886,2.1,8,'auto',75,20,500,1,'Ramp access & elevator inside heritage mansion','10:00-18:00 (Closed Mondays)','10:00','18:00','Entry ₹20; Step-free wheelchair accessible',4.7,1150,0.08,'https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?w=600','/audio/ngma.mp3');
INSERT INTO "activities_poi" VALUES(17,2,3,'Vidyarthi Bhavan Masale Dose','Iconic Eatery','Legendary crispy ghee roast dosas served in Gandhi Bazaar since 1943.','Famous for thick golden crisp crust, potato sagu, and unlimited fresh coconut chutney. Served in Gandhi Bazaar, Basavanagudi • ₹75 per dose • Cash & UPI.',12.9442,77.5714,3.5,14,'auto',45,75,75,1,'Street-level heritage dining','06:30-11:30 & 14:00-20:00 (Closed Fridays)','06:30','20:00','Pay per item, walk-in token system',4.8,8900,0.08,'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600','/audio/vidyarthi.mp3');
INSERT INTO "activities_poi" VALUES(18,2,3,'Brahmin Coffee Bar Filter Kaapi & Idli','Morning ritual','Piping hot melt-in-mouth rice idlis, crispy uddina vada and frothy filter coffee.','Shankarapura, near Basavanagudi. Authentic standing tiffin counter with mint-coconut chutney. Best before 10:00 AM • ₹40–₹80.',12.9535,77.5701,2.7,10,'auto',30,50,50,1,'Standing quick service','06:00-12:00 & 15:00-19:00 (Closed Sundays)','06:00','19:00','UPI & Cash',4.9,6700,0.05,'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600','/audio/brahmins.mp3');
INSERT INTO "activities_poi" VALUES(19,3,1,'Mysore Palace (Amba Vilas)','Royal Wonder','Spectacular Indo-Saracenic royal palace with 100,000 golden evening bulbs.','Seat of the Kingdom of Mysore. Features carved rosewood doors, ivory inlays, kaleidoscope stained-glass ceilings, and magnificent Dasara golden throne.',12.3051,76.6551,1.2,5,'auto',120,100,500,1,'Wheelchair ramps and level ground floor','10:00-17:30','10:00','17:30','Entry ₹100; Palace illumination on Sundays & festivals 19:00-20:00',4.9,12400,0.05,'https://images.unsplash.com/photo-1600100397608-f010e42f9b1c?w=600','/audio/mysore_palace.mp3');
INSERT INTO "activities_poi" VALUES(20,3,5,'Chamundi Hill & Sri Chamundeshwari Temple','Hilltop Vista','Ancient temple perched 1,000 meters above sea level with monolithic 5-meter Nandi.','Dedicated to Goddess Chamundeshwari. Panoramic bird-eye view of Mysore city and Lalitha Mahal Palace.',12.2741,76.671,8.5,20,'auto',90,0,0,0,'Stone steps & hill road','07:30-14:00 & 15:30-21:00','07:30','21:00','Free general entry; Special darshan ₹100',4.8,6200,0.25,'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=600','/audio/chamundi.mp3');
INSERT INTO "activities_poi" VALUES(21,3,3,'Guru Sweets Original Mysore Pak','Heritage Sweet','The birthplace of Mysore Pak, crafted with pure desi ghee, gram flour and sugar.','Sayyaji Rao Road, Devaraja Market • ₹60 for fresh warm batch.',12.31,76.65,1.0,4,'walk',30,60,60,1,'Market street walk','09:00-22:00','09:00','22:00','Cash & UPI',4.9,4300,0.02,'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600','/audio/mysore_pak.mp3');
CREATE TABLE bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        poi_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(poi_id) REFERENCES activities_poi(id)
    );
CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT NOT NULL UNIQUE,
        icon TEXT,
        description TEXT
    );
INSERT INTO "categories" VALUES(1,'Monuments & Temples','monuments','landmark','Ancient temples, stone carvings and ruins');
INSERT INTO "categories" VALUES(2,'Hidden gems','hidden_gems','sparkles','Quiet spots, secluded trails and tranquil ruins');
INSERT INTO "categories" VALUES(3,'Local Food & Dining','food','utensils','Authentic Karnataka cuisine and local delicacies');
INSERT INTO "categories" VALUES(4,'Stays & Resorts','stays','hotel','Boutique heritage stays and riverside lodges');
INSERT INTO "categories" VALUES(5,'Nature & Sunsets','nature','sun','Boulder viewpoints, riverbanks and scenic hills');
CREATE TABLE cities (
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
INSERT INTO "cities" VALUES(1,1,'Hampi','Karnataka',15.335,76.46,'Asia/Kolkata','Hampi is the site of Vijayanagara, capital of the empire that ruled southern India from 1336 to 1565 and one of the largest cities in the world at its peak. Around 1,600 surviving monuments ? temples, bazaars, aqueducts and royal enclosures ? lie scattered across boulder hills, preserved because the capital was abandoned after 1565 and never rebuilt, which is why the ruins survive as a time capsule.','Late monsoon ? Best season October to February','October to March');
INSERT INTO "cities" VALUES(2,1,'Bengaluru','Karnataka',12.9716,77.5946,'Asia/Kolkata','Bengaluru (Bangalore), the Garden City and Silicon Capital of India, blends centuries of royal Kempe Gowda and Wodeyar history with modern high-tech culture, lush sprawling botanical parks, Neo-Dravidian architecture, and legendary South Indian coffee houses.','Pleasant year-round • Best season October to February','September to March');
INSERT INTO "cities" VALUES(3,1,'Mysuru','Karnataka',12.2958,76.6394,'Asia/Kolkata','Mysuru (Mysore), the cultural heritage capital of Karnataka, celebrated for the world-famous illuminated Mysore Palace, Chamundi Hills, sandalwood artisans, and traditional Mysore Pak confectioneries.','Winter & Dasara season • October to March','October to February');
CREATE TABLE countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        currency_code TEXT NOT NULL,
        default_locale TEXT NOT NULL
    );
INSERT INTO "countries" VALUES(1,'IN','India','INR','en_IN');
CREATE TABLE currencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        symbol TEXT NOT NULL,
        exchange_rate_to_inr REAL,
        name TEXT
    );
INSERT INTO "currencies" VALUES(1,'INR','?',1.0,'Indian Rupee');
INSERT INTO "currencies" VALUES(2,'USD','$',84.5,'US Dollar');
INSERT INTO "currencies" VALUES(3,'EUR','?',92.0,'Euro');
INSERT INTO "currencies" VALUES(4,'GBP','?',108.0,'British Pound');
CREATE TABLE events_festivals (
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
INSERT INTO "events_festivals" VALUES(1,1,'Janmashtami, 4 September','2026-09-04','2026-09-04','Virupaksha Bazaar','Night processions along Virupaksha Bazaar, then Ganesh Chaturthi rituals at the Sasivekalu Ganesha on 14 September. Hampi Utsav follows in November.','High');
INSERT INTO "events_festivals" VALUES(2,1,'Ganesh Chaturthi','2026-09-14','2026-09-14','Sasivekalu Ganesha','Special poojas and heritage gatherings at the monolithic Ganesha shrines.','Medium');
INSERT INTO "events_festivals" VALUES(3,1,'Hampi Utsav','2026-11-03','2026-11-05','Monuments','Grand cultural festival with music, lighting and dance.','Peak');
INSERT INTO "events_festivals" VALUES(4,2,'Bengaluru Sunday Soul Sante','2026-09-27','2026-09-27','Jayabheri Meadows','Handcrafted flea market, local indie live musicians, and artisanal food pop-ups.','High footfall');
INSERT INTO "events_festivals" VALUES(5,2,'Mysuru Dasara Cultural Showcase','2026-10-02','2026-10-12','Bengaluru Palace Grounds','Classical Yakshagana, Carnatic violin concerts, and illuminated royal heritage pavilions.','Peak tourism');
CREATE TABLE hotels (
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
INSERT INTO "hotels" VALUES(1,1,'Boulder-side resort','Boutique Heritage Resort',6500,4.6,'Kamalapura, 4.2 km',15.312,76.475,'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600','Level access, serene boulder surroundings');
INSERT INTO "hotels" VALUES(2,1,'Bazaar guesthouse','Heritage Homestay',1200,4.3,'Hampi Bazaar, 200 m',15.3356,76.461,'https://images.unsplash.com/photo-1582719508461-905c673771fd?w=600','Virupapur Gaddi guesthouses across the river are hard to reach while the ferry is suspended.');
INSERT INTO "hotels" VALUES(3,2,'The Taj West End','Luxury Heritage Garden Resort',12500,4.8,'Race Course Rd, 1.5 km from Cubbon Park',12.9833,77.5833,'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600','20 acres of heritage botanical flora, step-free access');
INSERT INTO "hotels" VALUES(4,2,'Olive Downtown Central B&B','Boutique City Stay',2400,4.4,'Residency Road, 800 m from MG Road',12.9698,77.6042,'https://images.unsplash.com/photo-1582719508461-905c673771fd?w=600','Close to Metro Purple Line, walkable to cafes');
CREATE TABLE itineraries (
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
INSERT INTO "itineraries" VALUES(1,1,1,'Tomorrow, 06:00 to 19:00 ? Less walking ? ends 18:40','2026-09-01','full_day','less_walking',490,337,3.3,0.7,'Under 700 m on foot per stop, with vehicle drops close to each gate.');
CREATE TABLE itinerary_items (
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
INSERT INTO "itinerary_items" VALUES(1,1,6,1,'13:05','13:45',40,'auto',10,0,0.1,'Sunken and cool, the right place to sit out the worst of the sun.',0);
INSERT INTO "itinerary_items" VALUES(2,1,3,2,'14:00','15:00',60,'auto',15,0,0.15,'Level lawns, one ticket shared with Vittala, shade along the wall.',0);
INSERT INTO "itinerary_items" VALUES(3,1,7,3,'15:15','15:45',30,'walk',5,0,0.0,'Ramayana carved in bands around the royal chapel walls.',0);
INSERT INTO "itinerary_items" VALUES(4,1,5,4,'18:00','18:40',40,'walk',10,0,0.0,'Terraced shrines two minutes above the bazaar. Easy underfoot.',0);
CREATE TABLE languages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        local_name TEXT NOT NULL,
        is_tts_supported INTEGER DEFAULT 1,
        is_default INTEGER DEFAULT 0
    );
INSERT INTO "languages" VALUES(1,'en','English','English',1,1);
INSERT INTO "languages" VALUES(2,'kn','Kannada','?????',1,0);
INSERT INTO "languages" VALUES(3,'hi','Hindi','??????',1,0);
CREATE TABLE optimizer_weights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filter_name TEXT NOT NULL UNIQUE,
        weight_time REAL,
        weight_cost REAL,
        weight_walking REAL,
        weight_carbon REAL,
        weight_value REAL,
        max_walking_distance_m INTEGER
    );
INSERT INTO "optimizer_weights" VALUES(1,'balanced',1.0,1.0,1.0,1.0,1.5,1200);
INSERT INTO "optimizer_weights" VALUES(2,'cheaper',0.8,3.0,1.0,1.0,1.2,1500);
INSERT INTO "optimizer_weights" VALUES(3,'greener',0.9,1.0,2.5,3.5,1.2,2000);
INSERT INTO "optimizer_weights" VALUES(4,'less_walking',1.2,0.8,3.5,0.5,1.5,700);
CREATE TABLE place_kb (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_id INTEGER,
        topic TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        source_citation TEXT NOT NULL,
        verified_status TEXT DEFAULT 'verified',
        created_at TEXT,
        FOREIGN KEY(city_id) REFERENCES cities(id)
    );
INSERT INTO "place_kb" VALUES(1,1,'history_and_significance','Vijayanagara Empire & UNESCO World Heritage','Hampi is the site of Vijayanagara, capital of the empire that ruled southern India from 1336 to 1565 and one of the largest cities in the world at its peak. Around 1,600 surviving monuments ? temples, bazaars, aqueducts and royal enclosures ? lie scattered across boulder hills, preserved because the capital was abandoned after 1565 and never rebuilt, which is why the ruins survive as a time capsule.','Archaeological Survey of India (ASI) Monograph & UNESCO Heritage List #241','verified','2026-08-01');
INSERT INTO "place_kb" VALUES(2,1,'ticketing_rules','ASI Combined Ticket and Timings','One ASI ticket of ?30 for Indian nationals, or ?500 for foreign nationals, covers both Vittala Temple and the Zenana enclosure on the same day, so keep the stub. Virupaksha Temple charges ?2 separately and ?50 for a camera. Matanga Hill, Hemakuta Hill and the riverside shrines are free. Under-15s enter free everywhere.','ASI ticket schedule, Hampi circle. Prices last revised before this trip ? confirm at the counter.','verified','2026-08-15');
INSERT INTO "place_kb" VALUES(3,1,'dress_code_etiquette','Temple Dress Codes and Local Customs','Active temples like Virupaksha require modest clothing with covered shoulders and knees. Ruined open-air monuments have no religious dress code, but sun hats and shoes with good grip on granite boulders are essential.','Karnataka Tourism & ASI Guidelines','verified','2026-08-10');
INSERT INTO "place_kb" VALUES(4,1,'safety_after_dark','Night Walking in the Ruins','It is not safe to wander unlit boulder trails after dark due to lack of lighting, steep drop-offs, and nocturnal wildlife. Stay near Hampi Bazaar or well-lit roads after dusk.','Vijayanagara District Tourism Advisory','verified','2026-08-20');
INSERT INTO "place_kb" VALUES(5,1,'accessibility_wheelchair','Step-Free Access in Hampi','Zenana Enclosure (Lotus Mahal & Elephant Stables) is step-free with smooth manicured lawns. Hazara Rama and the Archaeological Museum at Kamalapura are also wheelchair accessible. Battery carts run to Vittala Temple from the main parking.','Karnataka Accessible Heritage Audit','verified','2026-08-12');
INSERT INTO "place_kb" VALUES(6,2,'history_and_significance','Kempe Gowda & Silicon City Heritage','Bengaluru was founded in 1537 by Kempe Gowda I, who built a mud fort and four watchtowers marking the city boundary. Under the Kingdom of Mysore and later the British cantonment, it evolved with European-style glasshouses, wide boulevards, and scientific institutions like IISc, transforming into India capital of tech and green gardens.','Karnataka State Gazetteer & INTACH Bangalore Heritage Chapter','verified','2026-09-01');
INSERT INTO "place_kb" VALUES(7,2,'ticketing_rules','Bengaluru Heritage Monument Tickets','Lalbagh Botanical Garden charges ₹30 (Indian adults) and ₹300 (foreign nationals), free for morning walkers before 09:00. Tipu Sultan Summer Palace ASI ticket is ₹20 for Indians and ₹250 for foreigners. Cubbon Park is completely free. Bengaluru Palace charges ₹250 with audio guide included.','Department of Horticulture, Govt of Karnataka & ASI Bangalore Circle 2026','verified','2026-09-15');
INSERT INTO "place_kb" VALUES(8,2,'accessibility_wheelchair','Step-Free Places in Bengaluru','Cubbon Park and Lalbagh Botanical Garden feature miles of paved, level, step-free tree-lined paths. Battery buggies operate across Lalbagh from the West Gate. The National Gallery of Modern Art (NGMA) has ramp access and elevator service. Bengaluru Palace has traditional stone steps leading to the upper gallery.','Accessible Bengaluru Urban Heritage Audit 2025','verified','2026-09-10');
INSERT INTO "place_kb" VALUES(9,2,'local_cuisine_guide','Bengaluru Tiffin & Filter Coffee Culture','Bengaluru is famous for its classic South Indian Darshini tiffin culture. Must-try delicacies include crispy Benne Masale Dose at Vidyarthi Bhavan or CTR, fluffy Button Idlis immersed in hot Sambar at Brahmin Coffee Bar, and freshly brewed Chicory-blended Filter Kaapi.','Karnataka Culinary Guidebook','verified','2026-09-01');
CREATE TABLE poi_facts_kb (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        poi_id INTEGER,
        fact_title TEXT NOT NULL,
        fact_detail TEXT NOT NULL,
        source_name TEXT NOT NULL,
        verified INTEGER DEFAULT 1,
        tag TEXT,
        FOREIGN KEY(poi_id) REFERENCES activities_poi(id)
    );
INSERT INTO "poi_facts_kb" VALUES(1,1,'Musical Pillars','The 56 pillars in the Ranga Mandapa are known to resonate acoustic tones when tapped. ASI has cordoned them to safeguard structural integrity.','ASI Research',1,'architecture');
INSERT INTO "poi_facts_kb" VALUES(2,2,'Inverted Gopura Shadow','A pinhole opening projects the upside-down shadow of the 50m eastern gopura on an inner wall.','Virupaksha Temple Records',1,'optics');
CREATE TABLE poi_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        poi_id INTEGER,
        feedback_type TEXT, -- 'like' or 'dislike'
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE safety_advisories (
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
INSERT INTO "safety_advisories" VALUES(1,1,'Coracle crossings suspended','The Tungabhadra is in spate after upstream releases. Cross to Anegundi by the Bukkasagara road bridge instead ? 40 minutes by auto.','warning','transport',1,'2026-09-05','Bukkasagara road bridge (40 min auto)');
INSERT INTO "safety_advisories" VALUES(2,1,'High UV until 15:30','There is almost no shade on the boulder trails. Climb Matanga or Anjanadri before 10:00, and carry two litres of water.','advisory','weather_heat',1,'2026-08-31 15:30:00','Carry water, wear hats');
INSERT INTO "safety_advisories" VALUES(3,1,'Ticketed sites stop entry in 6 h 04 min','Vittala Temple and the Zenana enclosure share one ASI ticket and stop entry at 17:00. Free monuments stay open until dusk.','info','ticketing_hours',1,'2026-08-31 17:00:00','Buy shared ASI ticket before 16:30');
INSERT INTO "safety_advisories" VALUES(4,2,'Peak Traffic Hour on Central Corridors','Heavy vehicle movement on MG Road & Silk Board between 17:30 and 20:00. Namma Metro Purple & Green lines run every 4 minutes and save 45 minutes.','info','transport',1,'2026-09-22 20:00:00','Use Metro instead of cabs during peak rush');
INSERT INTO "safety_advisories" VALUES(5,2,'Cubbon Park Vehicle-Free Morning Zone','Cubbon Park avenues are strictly pedestrian & cycle only until 08:00 AM. Best time for undisturbed morning heritage runs.','advisory','leisure',1,'2026-09-22','Enter from Queen Victoria statue gate on foot');
INSERT INTO "safety_advisories" VALUES(6,2,'Lalbagh Flower Show Staging','Glass House interior staging underway for upcoming weekend exhibition. Outdoor botanical trails and lake remain fully open.','info','event',1,'2026-09-25','West Gate has ample parking and battery shuttles');
CREATE TABLE trips (
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
INSERT INTO "trips" VALUES(1,1,1,'Solo Hampi Explorer','2026-08-27','2026-08-30',1180,7,0);
CREATE TABLE user_devices (
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
INSERT INTO "user_devices" VALUES(1,1,'dev-token-aarav','android_pwa',1,15.3352,76.4603,'2026-08-31 10:56:00');
CREATE TABLE user_preferences (
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
INSERT INTO "user_preferences" VALUES(1,1,'["History", "Architecture", "Photography", "Landscape", "Food", "Living ritual"]','medium','steady',0,2.0,1,'kn',1,'2026-09-22 13:37:07');
CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        avatar_url TEXT,
        created_at TEXT
    );
INSERT INTO "users" VALUES(1,'Aarav','aarav@example.com','https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150','2026-08-25');
CREATE TABLE weather_daily (
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
INSERT INTO "weather_daily" VALUES(1,1,'2026-08-31',28,32,'Partly cloudy',74,'06:14','18:41','7h 45 Daylight left',8,'15:30','Late monsoon ? Best season October to February','The landscape is at its greenest and crowds are thin, but granite is slick after evening showers and the river is running high. May touches 40?C, so the ruins are best walked now or after October.');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('countries',1);
INSERT INTO "sqlite_sequence" VALUES('languages',3);
INSERT INTO "sqlite_sequence" VALUES('currencies',4);
INSERT INTO "sqlite_sequence" VALUES('cities',3);
INSERT INTO "sqlite_sequence" VALUES('users',1);
INSERT INTO "sqlite_sequence" VALUES('user_preferences',1);
INSERT INTO "sqlite_sequence" VALUES('user_devices',1);
INSERT INTO "sqlite_sequence" VALUES('categories',5);
INSERT INTO "sqlite_sequence" VALUES('activities_poi',21);
INSERT INTO "sqlite_sequence" VALUES('hotels',4);
INSERT INTO "sqlite_sequence" VALUES('weather_daily',1);
INSERT INTO "sqlite_sequence" VALUES('events_festivals',5);
INSERT INTO "sqlite_sequence" VALUES('safety_advisories',6);
INSERT INTO "sqlite_sequence" VALUES('place_kb',9);
INSERT INTO "sqlite_sequence" VALUES('poi_facts_kb',2);
INSERT INTO "sqlite_sequence" VALUES('optimizer_weights',4);
INSERT INTO "sqlite_sequence" VALUES('trips',1);
INSERT INTO "sqlite_sequence" VALUES('itineraries',1);
INSERT INTO "sqlite_sequence" VALUES('itinerary_items',4);
COMMIT;
