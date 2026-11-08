"""
seed_data.py
Crea la base de datos SQLite 'listio.db' con el esquema completo (incluyendo física de canasta
de bicicleta eléctrica, escaneo de carritos pre-pago e integración con Google AI Edge Gallery)
y puebla las tablas con la información real extraída de los 75 recibos adjuntos.
"""

import sqlite3
import json
import os

DB_FILE = "listio.db"

def init_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.executescript("""
    CREATE TABLE users (
        user_id TEXT PRIMARY KEY,
        email TEXT UNIQUE,
        full_name TEXT,
        default_home_lat REAL,
        default_home_lng REAL,
        home_address_text TEXT,
        max_stores_per_trip INTEGER DEFAULT 3,
        ebike_max_weight_kg REAL DEFAULT 15.0,
        ebike_max_volume_liters REAL DEFAULT 28.0,
        ebike_battery_range_km REAL DEFAULT 45.0,
        created_at TEXT
    );

    CREATE TABLE retail_chains (
        chain_id TEXT PRIMARY KEY,
        code TEXT UNIQUE,
        legal_name TEXT,
        commercial_name TEXT,
        tax_id_rfc TEXT,
        primary_category TEXT
    );

    CREATE TABLE physical_stores (
        store_id TEXT PRIMARY KEY,
        chain_id TEXT REFERENCES retail_chains(chain_id),
        branch_name TEXT,
        branch_internal_code TEXT,
        street_address TEXT,
        neighborhood TEXT,
        municipality TEXT,
        state TEXT,
        postal_code TEXT,
        latitude REAL,
        longitude REAL,
        distance_from_home_km REAL,
        has_bike_parking BOOLEAN DEFAULT 1
    );

    CREATE TABLE online_stores (
        online_store_id TEXT PRIMARY KEY,
        chain_id TEXT REFERENCES retail_chains(chain_id),
        platform_name TEXT,
        base_url TEXT,
        standard_shipping_fee REAL,
        free_shipping_threshold REAL,
        typical_delivery_hours INTEGER,
        has_pickup_option BOOLEAN
    );

    CREATE TABLE product_categories (
        category_id TEXT PRIMARY KEY,
        name TEXT,
        slug TEXT UNIQUE,
        default_shelf_life_days INTEGER
    );

    CREATE TABLE canonical_products (
        product_id TEXT PRIMARY KEY,
        category_id TEXT REFERENCES product_categories(category_id),
        canonical_name TEXT,
        standard_unit TEXT,
        brand TEXT,
        estimated_shelf_life_days INTEGER,
        is_perishable BOOLEAN,
        storage_type TEXT,
        unit_weight_kg REAL DEFAULT 1.0,
        unit_volume_liters REAL DEFAULT 1.2,
        fragility_tier TEXT DEFAULT '2_MIDDLE_FIRM', -- '1_BASE_HEAVY', '2_MIDDLE_FIRM', '3_TOP_FRAGILE'
        thermal_sensitivity TEXT DEFAULT 'AMBIENT' -- 'AMBIENT', 'CHILLED', 'FROZEN'
    );

    CREATE TABLE store_products (
        store_product_id TEXT PRIMARY KEY,
        chain_id TEXT REFERENCES retail_chains(chain_id),
        product_id TEXT REFERENCES canonical_products(product_id),
        raw_ticket_description TEXT,
        store_sku TEXT,
        barcode_ean_upc TEXT,
        is_weighable BOOLEAN,
        pack_size_quantity REAL,
        pack_unit TEXT,
        tax_type TEXT
    );

    CREATE TABLE receipts (
        receipt_id TEXT PRIMARY KEY,
        user_id TEXT REFERENCES users(user_id),
        store_id TEXT REFERENCES physical_stores(store_id),
        chain_id TEXT REFERENCES retail_chains(chain_id),
        ticket_number TEXT,
        transaction_timestamp TEXT,
        cashier_or_register TEXT,
        subtotal_amount REAL,
        discounts_total REAL,
        tax_iva_amount REAL,
        tax_ieps_amount REAL,
        rounding_or_donation_amount REAL,
        total_amount REAL,
        total_items_count INTEGER,
        estimated_trip_weight_kg REAL DEFAULT 0.0,
        estimated_trip_volume_l REAL DEFAULT 0.0,
        is_mathematically_balanced BOOLEAN
    );

    CREATE TABLE receipt_items (
        receipt_item_id TEXT PRIMARY KEY,
        receipt_id TEXT REFERENCES receipts(receipt_id),
        store_product_id TEXT REFERENCES store_products(store_product_id),
        product_id TEXT REFERENCES canonical_products(product_id),
        raw_description TEXT,
        quantity REAL,
        unit_of_measure TEXT,
        regular_unit_price REAL,
        promotional_unit_price REAL,
        discount_amount REAL,
        line_total_amount REAL,
        tax_indicator TEXT,
        is_cancelled BOOLEAN
    );

    CREATE TABLE price_observations (
        observation_id TEXT PRIMARY KEY,
        product_id TEXT REFERENCES canonical_products(product_id),
        store_product_id TEXT REFERENCES store_products(store_product_id),
        chain_id TEXT REFERENCES retail_chains(chain_id),
        price_channel TEXT,
        price_date TEXT,
        regular_unit_price REAL,
        promo_unit_price REAL,
        is_on_promotion BOOLEAN,
        promo_mechanism TEXT,
        normalized_price_per_std_unit REAL
    );

    CREATE TABLE user_product_consumption (
        consumption_id TEXT PRIMARY KEY,
        user_id TEXT REFERENCES users(user_id),
        product_id TEXT REFERENCES canonical_products(product_id),
        avg_reorder_interval_days REAL,
        avg_purchase_quantity REAL,
        daily_consumption_rate REAL,
        total_purchases_count INTEGER,
        last_purchased_date TEXT,
        estimated_depletion_date TEXT,
        current_estimated_stock REAL,
        preferred_store_or_chain TEXT REFERENCES retail_chains(chain_id)
    );

    CREATE TABLE shopping_lists (
        list_id TEXT PRIMARY KEY,
        user_id TEXT REFERENCES users(user_id),
        title TEXT,
        status TEXT,
        generated_by TEXT,
        target_budget REAL,
        planned_date TEXT
    );

    CREATE TABLE shopping_list_items (
        list_item_id TEXT PRIMARY KEY,
        list_id TEXT REFERENCES shopping_lists(list_id),
        product_id TEXT REFERENCES canonical_products(product_id),
        suggested_quantity REAL,
        unit TEXT,
        urgency_level TEXT,
        allocated_chain_id TEXT REFERENCES retail_chains(chain_id),
        allocated_channel TEXT,
        estimated_item_cost REAL,
        estimated_weight_kg REAL,
        estimated_volume_l REAL
    );

    -- Tabla para Fotografías de Carritos de Compra Antes del Pago (Pre-Checkout Vision)
    CREATE TABLE cart_snapshots (
        snapshot_id TEXT PRIMARY KEY,
        user_id TEXT REFERENCES users(user_id),
        store_id TEXT REFERENCES physical_stores(store_id),
        photo_uri TEXT,
        captured_at TEXT,
        detected_items_count INTEGER,
        estimated_subtotal REAL,
        estimated_total_weight_kg REAL,
        estimated_total_volume_liters REAL,
        ebike_capacity_status TEXT, -- 'OK', 'WARNING_NEAR_LIMIT', 'OVERLOAD_SPLIT_NEEDED'
        ai_packing_advice TEXT
    );

    CREATE TABLE cart_snapshot_items (
        snapshot_item_id TEXT PRIMARY KEY,
        snapshot_id TEXT REFERENCES cart_snapshots(snapshot_id),
        product_id TEXT REFERENCES canonical_products(product_id),
        detected_name TEXT,
        estimated_qty REAL,
        unit_price_at_store REAL,
        cheaper_store_alert TEXT,
        weight_kg REAL,
        volume_l REAL,
        fragility_tier TEXT
    );

    -- Tabla para Fotografías de Productos Futuros y Precios en Anaquel
    CREATE TABLE product_photos (
        photo_id TEXT PRIMARY KEY,
        product_id TEXT REFERENCES canonical_products(product_id),
        chain_id TEXT REFERENCES retail_chains(chain_id),
        image_uri TEXT,
        observed_price REAL,
        captured_at TEXT,
        notes TEXT
    );
    """)
    conn.commit()
    return conn

def populate_data(conn):
    c = conn.cursor()
    
    # 1. Usuario con Perfil de Bicicleta Eléctrica (Canasta 15 kg / 28 Litros)
    c.execute("""
    INSERT INTO users VALUES (
        'usr_01', 'krabayo@gmail.com', 'Yesser Caraballo Guzmán',
        25.7483, -100.2882, 'San Nicolás de los Garza Centro, NL, CP 66400',
        3, 15.0, 28.0, 45.0, '2026-03-01'
    )""")
    
    # 2. Cadenas Comerciales
    c.executemany("INSERT INTO retail_chains VALUES (?, ?, ?, ?, ?, ?)", [
        ('ch_heb', 'HEB', 'Supermercados Internacionales HEB S.A. de C.V.', 'H-E-B', 'SIH961129KY2', 'SUPERMARKET'),
        ('ch_soriana', 'SORIANA', 'Tiendas Soriana, S.A. de C.V.', 'Soriana Híper', 'TS0991022PB6', 'SUPERMARKET'),
        ('ch_aurrera', 'AURRERA', 'Nueva Wal Mart de Mexico S. de R.L. de C.V.', 'Bodega Aurrera', 'NWM9709244W4', 'DISCOUNT_SUPERMARKET'),
        ('ch_sams', 'SAMS', 'Nueva Wal Mart de Mexico S. de R.L. de C.V.', 'Sam\'s Club', 'NWM9709244W4', 'WHOLESALE_CLUB'),
        ('ch_marlan', 'EL_MAS_POLLO', 'Avipecuaria Marlan S.A. de C.V.', 'El Más Pollo', 'AML8910189F0', 'BUTCHER'),
        ('ch_horacios', 'TRES_HORACIOS', 'Tres Horacios Carnicería', 'Tres Horacios', 'THO202020AAA', 'GOURMET_BUTCHER'),
        ('ch_oxxo', 'OXXO', 'Cadena Comercial Oxxo, S.A. de C.V.', 'OXXO', 'CCO-860523-1N4', 'CONVENIENCE')
    ])
    
    # 3. Tiendas Físicas con Distancias para Bicicleta Eléctrica
    c.executemany("INSERT INTO physical_stores VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        ('st_mar_sn', 'ch_marlan', 'El Más Pollo - San Nicolás Centro', 'SUC_SANNICOLAS', 'Arturo B. de la Garza #321', 'Centro', 'San Nicolás de los Garza', 'Nuevo León', '66450', 25.7490, -100.2870, 0.45, 1),
        ('st_horacios', 'ch_horacios', 'Tres Horacios Boutique', 'TIII1', 'Mariano Matamoros 430', 'Centro', 'San Nicolás de los Garza', 'Nuevo León', '66400', 25.7475, -100.2865, 0.35, 1),
        ('st_oxxo_pino', 'ch_oxxo', 'OXXO Pino NLD', '10NLA50QU62', 'Arturo B. de la Garza #701', 'Centro', 'San Nicolás de los Garza', 'Nuevo León', '66400', 25.7505, -100.2850, 0.50, 1),
        ('st_mar_lamp', 'ch_marlan', 'El Más Pollo - Lampazos', 'SUC_LAMPAZOS', 'Lampazos #207', 'Chapultepec', 'San Nicolás de los Garza', 'Nuevo León', '66450', 25.7440, -100.2920, 0.85, 1),
        ('st_sor_sn', 'ch_soriana', 'Soriana Híper San Nicolás (12)', 'H 12', 'Ave Alfonso Reyes 601', 'El Roble', 'San Nicolás de los Garza', 'Nuevo León', '66450', 25.7420, -100.3015, 1.65, 1),
        ('st_sams_uni', 'ch_sams', 'Sam\'s Club Universidad Monterrey', 'TDA#4727', 'Av. Universidad #413', 'El Roble', 'San Nicolás de los Garza', 'Nuevo León', '66500', 25.7380, -100.2980, 1.80, 1),
        ('st_heb_sn', 'ch_heb', 'H-E-B San Nicolás AutoCobro', '671/673/674/675/676', 'Av. Universidad / Sendero', 'Anáhuac', 'San Nicolás de los Garza', 'Nuevo León', '66450', 25.7350, -100.2990, 2.10, 1),
        ('st_aur_stdgo', 'ch_aurrera', 'Bodega Aurrera Santo Domingo', 'TDA#3801', 'Av. Sto. Domingo SN', 'Santo Domingo', 'San Nicolás de los Garza', 'Nuevo León', '66430', 25.7510, -100.2720, 1.95, 1)
    ])
    
    # 4. Tiendas en Línea
    c.executemany("INSERT INTO online_stores VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
        ('on_heb', 'ch_heb', 'H-E-B Digital App & Web', 'https://www.heb.com.mx', 49.00, 700.00, 4, 1),
        ('on_soriana', 'ch_soriana', 'Soriana.com Super en tu Casa', 'https://www.soriana.com', 49.00, 800.00, 6, 1),
        ('on_aurrera', 'ch_aurrera', 'Despensa Bodega Aurrera Online', 'https://despensa.bodegaaurrera.com.mx', 39.00, 499.00, 24, 1),
        ('on_sams', 'ch_sams', 'Sam\'s Club México Online', 'https://www.sams.com.mx', 65.00, 1200.00, 24, 1)
    ])
    
    # 5. Categorías
    c.executemany("INSERT INTO product_categories VALUES (?, ?, ?, ?)", [
        ('cat_frescos', 'Frutas y Verduras', 'frutas-y-verduras', 6),
        ('cat_carnes', 'Carnes y Pollo', 'carnes-y-pollo', 5),
        ('cat_lacteos', 'Lácteos y Huevos', 'lacteos-y-huevos', 10),
        ('cat_abarrotes', 'Abarrotes Básicos', 'abarrotes-basicos', 45),
        ('cat_panaderia', 'Panadería y Tortillería', 'panaderia-tortilleria', 5),
        ('cat_limpieza', 'Limpieza y Hogar', 'limpieza-hogar', 60),
        ('cat_congelados', 'Congelados', 'congelados', 90)
    ])
    
    # 6. Productos Canónicos con Peso (kg), Volumen (L), Fragilidad y Sensibilidad Térmica para E-Bike
    canonical_prods = [
        ('cp_platano', 'cat_frescos', 'Plátano Cavendish / Tabasco', 'kg', 'Genérico', 5, 1, 'ROOM_TEMP', 1.0, 1.8, '3_TOP_FRAGILE', 'AMBIENT'),
        ('cp_limon', 'cat_frescos', 'Limón Agrio con Semilla', 'kg', 'Genérico', 12, 1, 'REFRIGERATED', 1.0, 1.3, '2_MIDDLE_FIRM', 'AMBIENT'),
        ('cp_tomate', 'cat_frescos', 'Tomate Saladette / Huaje', 'kg', 'Genérico', 7, 1, 'ROOM_TEMP', 1.0, 1.5, '3_TOP_FRAGILE', 'AMBIENT'),
        ('cp_aguacate', 'cat_frescos', 'Aguacate Hass', 'kg', 'Genérico', 5, 1, 'ROOM_TEMP', 1.0, 1.5, '3_TOP_FRAGILE', 'AMBIENT'),
        ('cp_cebolla_bca', 'cat_frescos', 'Cebolla Blanca', 'kg', 'Genérico', 14, 1, 'ROOM_TEMP', 1.0, 1.4, '2_MIDDLE_FIRM', 'AMBIENT'),
        ('cp_camote_amarillo', 'cat_frescos', 'Camote Amarillo / Morado', 'kg', 'Genérico', 10, 1, 'ROOM_TEMP', 1.0, 1.3, '1_BASE_HEAVY', 'AMBIENT'),
        ('cp_naranja', 'cat_frescos', 'Naranja Valencia', 'kg', 'Genérico', 10, 1, 'ROOM_TEMP', 1.0, 1.4, '2_MIDDLE_FIRM', 'AMBIENT'),
        ('cp_manzana', 'cat_frescos', 'Manzana Ambrosia / Red Delicious', 'kg', 'Genérico', 14, 1, 'REFRIGERATED', 1.0, 1.6, '2_MIDDLE_FIRM', 'AMBIENT'),
        ('cp_papaya', 'cat_frescos', 'Papaya Maradol', 'kg', 'Genérico', 5, 1, 'REFRIGERATED', 1.0, 1.5, '3_TOP_FRAGILE', 'AMBIENT'),
        ('cp_papa_russet', 'cat_frescos', 'Papa Russet Bolsa 3 lb (1.36 kg)', 'pack', 'Genérico', 21, 1, 'ROOM_TEMP', 1.36, 1.9, '1_BASE_HEAVY', 'AMBIENT'),
        
        ('cp_pollo_pierna_muslo', 'cat_carnes', 'Pierna y Muslo de Pollo Fresco', 'kg', 'Genérico', 4, 1, 'REFRIGERATED', 1.0, 1.15, '1_BASE_HEAVY', 'CHILLED'),
        ('cp_pollo_milanesa', 'cat_carnes', 'Milanesa de Pechuga de Pollo', 'kg', 'Tres Horacios', 4, 1, 'REFRIGERATED', 1.0, 1.2, '2_MIDDLE_FIRM', 'CHILLED'),
        ('cp_cerdo_pierna', 'cat_carnes', 'Pierna / Lomo de Cerdo Sin Hueso', 'kg', 'Genérico', 5, 1, 'REFRIGERATED', 1.0, 1.15, '1_BASE_HEAVY', 'CHILLED'),
        ('cp_cerdo_chuleta', 'cat_carnes', 'Chuleta Natural / Sirloin de Cerdo', 'kg', 'Genérico', 5, 1, 'REFRIGERATED', 1.0, 1.25, '2_MIDDLE_FIRM', 'CHILLED'),
        ('cp_res_molida', 'cat_carnes', 'Carne Molida de Res / Cerdo', 'kg', 'Genérico', 4, 1, 'REFRIGERATED', 1.0, 1.15, '2_MIDDLE_FIRM', 'CHILLED'),
        
        ('cp_leche_entera_1l', 'cat_lacteos', 'Leche Entera Pasteurizada 1L', 'piece', 'HEB', 8, 1, 'REFRIGERATED', 1.04, 1.1, '1_BASE_HEAVY', 'CHILLED'),
        ('cp_leche_alpura_polvo', 'cat_lacteos', 'Leche Deslactosada en Polvo Alpura', 'piece', 'Alpura', 60, 0, 'ROOM_TEMP', 0.46, 0.9, '2_MIDDLE_FIRM', 'AMBIENT'),
        ('cp_huevo_blanco_12', 'cat_lacteos', 'Huevo Blanco Paquete 12 Piezas', 'pack', 'Economax / AU', 18, 1, 'ROOM_TEMP', 0.78, 2.4, '3_TOP_FRAGILE', 'AMBIENT'),
        ('cp_queso_oaxaca', 'cat_lacteos', 'Queso Oaxaca Tradicional (500g-1kg)', 'kg', 'Member\'s Mark / Villita', 14, 1, 'REFRIGERATED', 1.0, 1.2, '2_MIDDLE_FIRM', 'CHILLED'),
        ('cp_queso_crema', 'cat_lacteos', 'Queso Crema Philadelphia 200g', 'piece', 'Philadelphia', 25, 1, 'REFRIGERATED', 0.20, 0.3, '2_MIDDLE_FIRM', 'CHILLED'),
        ('cp_yogurt_natural', 'cat_lacteos', 'Yogurt Natural Sin Azúcar 900g-1kg', 'piece', 'HEB / Danone', 15, 1, 'REFRIGERATED', 0.95, 1.1, '2_MIDDLE_FIRM', 'CHILLED'),
        ('cp_mantequilla_barra', 'cat_lacteos', 'Mantequilla Gloria Barra 90g', 'piece', 'Gloria', 30, 1, 'REFRIGERATED', 0.09, 0.15, '2_MIDDLE_FIRM', 'CHILLED'),
        
        ('cp_tortilla_maiz', 'cat_panaderia', 'Tortilla de Maíz Blanca / Amarilla 800g', 'pack', 'HEB / Tortillería', 5, 1, 'ROOM_TEMP', 0.80, 0.9, '2_MIDDLE_FIRM', 'AMBIENT'),
        ('cp_bolillo_integral', 'cat_panaderia', 'Bolillo Integral / Telera (Paq 6 pz)', 'pack', 'Panadería', 3, 1, 'ROOM_TEMP', 0.45, 2.5, '3_TOP_FRAGILE', 'AMBIENT'),
        ('cp_pan_tostado', 'cat_panaderia', 'Pan Tostado Integral 360g', 'piece', 'Bimbo / HEB', 30, 0, 'ROOM_TEMP', 0.36, 2.2, '3_TOP_FRAGILE', 'AMBIENT'),
        
        ('cp_cafe_house_blend', 'cat_abarrotes', 'Café House Blend Tostado y Molido 1kg', 'piece', 'HEB', 30, 0, 'ROOM_TEMP', 1.0, 1.8, '2_MIDDLE_FIRM', 'AMBIENT'),
        ('cp_arroz_1kg', 'cat_abarrotes', 'Arroz Super Extra 900g-1kg', 'piece', 'Mi Tienda / Precissimo', 90, 0, 'ROOM_TEMP', 0.95, 1.1, '1_BASE_HEAVY', 'AMBIENT'),
        ('cp_fresas_congeladas_2k', 'cat_congelados', 'Fresas Congeladas Bolsa 2kg', 'piece', 'Member\'s Mark / HEB', 120, 0, 'FROZEN', 2.0, 3.4, '1_BASE_HEAVY', 'FROZEN'),
        ('cp_pimiento_mix_cong', 'cat_congelados', 'Pimiento Mix Congelado Bolsa 1.5kg', 'piece', 'Member\'s Mark', 120, 0, 'FROZEN', 1.5, 2.6, '2_MIDDLE_FIRM', 'FROZEN'),
        ('cp_sardina_tomate', 'cat_abarrotes', 'Sardina en Salsa de Tomate 425g', 'piece', 'Valley Food / AU', 180, 0, 'ROOM_TEMP', 0.45, 0.5, '1_BASE_HEAVY', 'AMBIENT'),
        ('cp_sopa_maruchan', 'cat_abarrotes', 'Sopa Instantánea Ramen Pollo 85g', 'piece', 'Maruchan', 90, 0, 'ROOM_TEMP', 0.085, 0.35, '3_TOP_FRAGILE', 'AMBIENT'),
        
        ('cp_detergente_roma_1k', 'cat_limpieza', 'Detergente en Polvo Roma 1kg', 'piece', 'Roma', 90, 0, 'ROOM_TEMP', 1.0, 1.6, '1_BASE_HEAVY', 'AMBIENT'),
        ('cp_jabon_zote_barra', 'cat_limpieza', 'Jabón Zote Barra 200g-400g', 'piece', 'Zote', 120, 0, 'ROOM_TEMP', 0.30, 0.35, '1_BASE_HEAVY', 'AMBIENT'),
        ('cp_bolsa_basura', 'cat_limpieza', 'Bolsas para Basura Mediana 20 Pz', 'pack', 'Mi Tienda', 90, 0, 'ROOM_TEMP', 0.35, 0.5, '1_BASE_HEAVY', 'AMBIENT')
    ]
    c.executemany("INSERT INTO canonical_products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", canonical_prods)
    
    # 7. Store Products
    store_prod_map = [
        ('sp_heb_platano', 'ch_heb', 'cp_platano', 'PLATANO', 'PLU-4011', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_heb_leche_ent', 'ch_heb', 'cp_leche_entera_1l', 'HEB ST LECHE ENTERA', 'HEB-LECH-01', '750100510001', 0, 1.0, 'piece', 'EXEMPT'),
        ('sp_heb_cafe_house', 'ch_heb', 'cp_cafe_house_blend', 'CAFE HOUSE BLEND HEB', 'HEB-CAF-01', '750100510002', 0, 1.0, 'piece', 'EXEMPT'),
        ('sp_heb_huevo_eco', 'ch_heb', 'cp_huevo_blanco_12', 'ECONOMAX HUEVO BAC 12 PZ', 'ECO-HVO-12', '750100510003', 0, 12.0, 'piece', 'EXEMPT'),
        ('sp_heb_tort_bca', 'ch_heb', 'cp_tortilla_maiz', 'TORTILLA MAIZ BLANCA F', 'HEB-TOR-01', None, 0, 1.0, 'pack', 'EXEMPT'),
        ('sp_heb_maruchan', 'ch_heb', 'cp_sopa_maruchan', 'MARUCHAN SOPA RAMEN POLLO', 'MAR-RAM-01', '041789002960', 0, 1.0, 'piece', 'IVA_16'),
        ('sp_heb_yogurt_nat', 'ch_heb', 'cp_yogurt_natural', 'Yogurt Natural SA', 'HEB-YOG-01', None, 0, 1.0, 'piece', 'EXEMPT'),
        ('sp_heb_manteq', 'ch_heb', 'cp_mantequilla_barra', 'GLORIA MANTEQUILLA BARRA', 'GLO-MAN-90', '750102600111', 0, 1.0, 'piece', 'IVA_16'),
        ('sp_heb_limon', 'ch_heb', 'cp_limon', 'LIMON AGRIO SUPREMO', 'PLU-4048', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_heb_tomate', 'ch_heb', 'cp_tomate', 'TOMATE HUAJE SUPREMO', 'PLU-4087', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_heb_pierna_cerdo', 'ch_heb', 'cp_cerdo_pierna', 'PIERNA DE CERDO C H REB', 'CARN-P-CER', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_heb_fresas_cong', 'ch_heb', 'cp_fresas_congeladas_2k', 'HEB FRESAS CONGELADA 2 KG', 'HEB-FRS-2K', '750100510004', 0, 2.0, 'kg', 'EXEMPT'),
        ('sp_sor_platano', 'ch_soriana', 'cp_platano', 'PLATANO KG', '203', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_sor_pollo_pym', 'ch_soriana', 'cp_pollo_pierna_muslo', 'PIERNA Y MUSLO C/AM', '002', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_sor_cerdo_chuleta', 'ch_soriana', 'cp_cerdo_chuleta', 'CHULETA NATURAL CER', '005', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_sor_cerdo_pierna', 'ch_soriana', 'cp_cerdo_pierna', 'PIERNA CERDO S/HUES', '005', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_sor_sardina', 'ch_soriana', 'cp_sardina_tomate', 'SARDINA VALLEY FOOD', '424', '750102600222', 0, 1.0, 'piece', 'IVA_16'),
        ('sp_sor_arroz', 'ch_soriana', 'cp_arroz_1kg', 'ARROZ EXTRA PRECISS', '689', '750102600333', 0, 1.0, 'piece', 'EXEMPT'),
        ('sp_sor_huevo_12', 'ch_soriana', 'cp_huevo_blanco_12', 'HUEVO BLANCO PAQ 12', '025', '750102600444', 0, 12.0, 'piece', 'EXEMPT'),
        ('sp_aur_platano_chia', 'ch_aurrera', 'cp_platano', 'PLATANO CHIA', '40112', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_aur_tomate_huaje', 'ch_aurrera', 'cp_tomate', 'TOMAT HUAJE', '40877', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_aur_limon_agrio', 'ch_aurrera', 'cp_limon', 'LIMON AGRIO', '43052', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_aur_zote_barra', 'ch_aurrera', 'cp_jabon_zote_barra', 'ZOTE BARRA', '7501026005985', '7501026005985', 0, 1.0, 'piece', 'IVA_16'),
        ('sp_aur_roma_det', 'ch_aurrera', 'cp_detergente_roma_1k', 'ROMA DET 1', '7501026004605', '7501026004605', 0, 1.0, 'piece', 'IVA_16'),
        ('sp_aur_queso_oax', 'ch_aurrera', 'cp_queso_oaxaca', 'QSO OAXACA', '7501040080333', '7501040080333', 0, 0.4, 'kg', 'EXEMPT'),
        ('sp_aur_huevo_12', 'ch_aurrera', 'cp_huevo_blanco_12', 'HVO AU 12P', '7506495008963', '7506495008963', 0, 12.0, 'piece', 'EXEMPT'),
        ('sp_aur_arroz_au', 'ch_aurrera', 'cp_arroz_1kg', 'AU ARROZ 9', '7501791638623', '7501791638623', 0, 0.9, 'piece', 'EXEMPT'),
        ('sp_sams_fresa_2k', 'ch_sams', 'cp_fresas_congeladas_2k', 'MM 2K FRESA', '799257', '799257', 0, 2.0, 'kg', 'IVA_16'),
        ('sp_sams_oaxaca_mm', 'ch_sams', 'cp_queso_oaxaca', 'MM OAXACA', '980000690', '980000690', 0, 1.0, 'kg', 'IVA_16'),
        ('sp_mar_muslo_raba', 'ch_marlan', 'cp_pollo_pierna_muslo', 'MUSLO CON RABADILLA', 'MAR-01', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_tho_milanesa_pollo', 'ch_horacios', 'cp_pollo_milanesa', 'Milanesa de pollo', 'TH-01', None, 1, 1.0, 'kg', 'EXEMPT')
    ]
    c.executemany("INSERT INTO store_products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", store_prod_map)
    
    # 8. Observaciones de Precios
    prices = [
        ('po_01', 'cp_platano', 'sp_heb_platano', 'ch_heb', 'IN_STORE_RECEIPT', '2026-11-04', 21.53, 21.53, 0, None, 21.53),
        ('po_02', 'cp_platano', 'sp_aur_platano_chia', 'ch_aurrera', 'IN_STORE_RECEIPT', '2026-10-31', 17.00, 17.00, 0, None, 17.00),
        ('po_03', 'cp_platano', 'sp_sor_platano', 'ch_soriana', 'IN_STORE_RECEIPT', '2026-10-17', 23.90, 23.30, 1, 'DIRECT_DISCOUNT', 23.30),
        ('po_04', 'cp_pollo_pierna_muslo', 'sp_mar_muslo_raba', 'ch_marlan', 'IN_STORE_RECEIPT', '2026-10-02', 43.90, 43.90, 0, None, 43.90),
        ('po_05', 'cp_pollo_pierna_muslo', 'sp_sor_pollo_pym', 'ch_soriana', 'IN_STORE_RECEIPT', '2026-10-31', 38.90, 29.90, 1, 'MARTES_MIERCOLES_CAMPO', 29.90),
        ('po_06', 'cp_pollo_pierna_muslo', 'sp_heb_pierna_cerdo', 'ch_heb', 'IN_STORE_RECEIPT', '2026-09-05', 55.00, 55.00, 0, None, 55.00),
        ('po_07', 'cp_leche_entera_1l', 'sp_heb_leche_ent', 'ch_heb', 'IN_STORE_RECEIPT', '2026-11-04', 36.90, 36.90, 0, None, 36.90),
        ('po_08', 'cp_cafe_house_blend', 'sp_heb_cafe_house', 'ch_heb', 'IN_STORE_RECEIPT', '2026-10-21', 145.00, 145.00, 0, None, 145.00),
        ('po_09', 'cp_huevo_blanco_12', 'sp_heb_huevo_eco', 'ch_heb', 'IN_STORE_RECEIPT', '2026-11-04', 32.50, 32.50, 0, None, 32.50),
        ('po_10', 'cp_huevo_blanco_12', 'sp_aur_huevo_12', 'ch_aurrera', 'IN_STORE_RECEIPT', '2026-10-31', 27.00, 27.00, 0, None, 27.00),
        ('po_11', 'cp_huevo_blanco_12', 'sp_sor_huevo_12', 'ch_soriana', 'IN_STORE_RECEIPT', '2026-10-17', 31.90, 31.90, 0, None, 31.90),
        ('po_12', 'cp_fresas_congeladas_2k', 'sp_sams_fresa_2k', 'ch_sams', 'IN_STORE_RECEIPT', '2026-10-30', 163.68, 163.68, 0, None, 81.84),
        ('po_13', 'cp_fresas_congeladas_2k', 'sp_heb_fresas_cong', 'ch_heb', 'IN_STORE_RECEIPT', '2026-07-09', 235.00, 235.00, 0, None, 117.50),
        ('po_14', 'cp_jabon_zote_barra', 'sp_aur_zote_barra', 'ch_aurrera', 'IN_STORE_RECEIPT', '2026-09-13', 7.50, 6.00, 1, 'REBAJA_4X24', 6.00),
        ('po_15', 'cp_detergente_roma_1k', 'sp_aur_roma_det', 'ch_aurrera', 'IN_STORE_RECEIPT', '2026-09-13', 40.00, 35.00, 1, 'REBAJA_1X35', 35.00),
        ('po_16', 'cp_sardina_tomate', 'sp_sor_sardina', 'ch_soriana', 'IN_STORE_RECEIPT', '2026-10-31', 17.00, 17.00, 0, None, 17.00),
        ('po_17', 'cp_sopa_maruchan', 'sp_heb_maruchan', 'ch_heb', 'IN_STORE_RECEIPT', '2026-10-21', 6.90, 6.90, 0, None, 6.90),
        ('po_18', 'cp_tomate', 'sp_aur_tomate_huaje', 'ch_aurrera', 'IN_STORE_RECEIPT', '2026-08-25', 12.90, 12.90, 0, None, 12.90),
        ('po_19', 'cp_tomate', 'sp_heb_tomate', 'ch_heb', 'IN_STORE_RECEIPT', '2026-10-21', 13.90, 13.90, 0, None, 13.90)
    ]
    c.executemany("INSERT INTO price_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", prices)
    
    # 9. Recibos Históricos con Peso y Volumen de Viaje en Bicicleta Eléctrica
    c.executemany("INSERT INTO receipts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        ('rc_heb_1104', 'usr_01', 'st_heb_sn', 'ch_heb', '1097 0841 1104 2618 5202 952', '2026-11-04 18:52:00', 'AutoCobro 671', 339.00, 0.0, 0.0, 0.0, 0.21, 339.00, 10, 5.45, 9.20, 1),
        ('rc_sor_1031', 'usr_01', 'st_sor_sn', 'ch_soriana', '00120919059700700226', '2026-10-31 11:29:59', 'Cajero AutoCobro 5', 474.24, 34.65, 19.30, 0.0, 0.0, 439.59, 14, 11.80, 16.40, 1),
        ('rc_sams_1030', 'usr_01', 'st_sams_uni', 'ch_sams', '3135965518986460529734', '2026-10-30 18:11:26', 'OP#00000491 TR#05521', 1080.29, 58.30, 0.0, 0.0, 0.0, 1061.89, 8, 10.60, 18.50, 1),
        ('rc_tho_1030', 'usr_01', 'st_horacios', 'ch_horacios', 'RECB0003ZKXSS3080IKG', '2026-10-30 12:28:43', 'Horacio J (TIII1)', 820.83, 140.00, 0.0, 0.0, 0.0, 820.83, 7, 4.48, 5.90, 1),
        ('rc_heb_1021', 'usr_01', 'st_heb_sn', 'ch_heb', '1088 7082 1021 2621 1502 952', '2026-10-21 21:15:00', 'AutoCobro 675', 1252.00, 145.00, 0.0, 0.0, 0.43, 1107.00, 28, 11.20, 17.80, 1),
        ('rc_sor_1017', 'usr_01', 'st_sor_sn', 'ch_soriana', '00121017003903902091', '2026-10-17 18:27:07', 'Cajero AutoCobro 5', 681.00, 34.65, 14.05, 0.0, 0.93, 681.00, 23, 12.10, 17.20, 1),
        ('rc_aur_1011', 'usr_01', 'st_aur_stdgo', 'ch_aurrera', 'TC#884808035850709994603', '2026-10-11 19:47:00', 'OP#00000743 TR#09962', 257.12, 33.00, 0.0, 8.88, 0.0, 266.00, 9, 4.90, 6.80, 1),
        ('rc_mar_1002', 'usr_01', 'st_mar_sn', 'ch_marlan', '526218', '2026-10-02 12:17:00', 'M. Rodriguez', 601.25, 0.0, 0.0, 0.0, 0.0, 601.25, 4, 9.53, 11.00, 1),
        ('rc_mar_0711', 'usr_01', 'st_mar_sn', 'ch_marlan', '528207', '2026-07-11 14:48:00', 'M. Rodriguez', 367.00, 0.0, 0.0, 0.0, 0.0, 367.00, 1, 8.36, 9.60, 1),
        ('rc_oxxo_0705', 'usr_01', 'st_oxxo_pino', 'ch_oxxo', '469615', '2026-07-05 15:38:00', 'Pino NLD', 82.00, 6.50, 0.0, 0.0, 0.0, 82.00, 3, 1.55, 2.10, 1)
    ])
    
    # 10. Consumo Predictivo
    consumption_data = [
        ('cns_01', 'usr_01', 'cp_pollo_pierna_muslo', 7.0, 4.0, 0.571, 12, '2026-10-31', '2026-11-07', 0.2, 'ch_marlan'),
        ('cns_02', 'usr_01', 'cp_sopa_maruchan', 12.0, 4.0, 0.333, 9, '2026-10-21', '2026-11-02', 0.0, 'ch_heb'),
        ('cns_03', 'usr_01', 'cp_platano', 4.5, 1.4, 0.311, 24, '2026-11-04', '2026-11-09', 0.3, 'ch_aurrera'),
        ('cns_04', 'usr_01', 'cp_leche_entera_1l', 5.0, 2.0, 0.400, 19, '2026-11-04', '2026-11-09', 0.4, 'ch_heb'),
        ('cns_05', 'usr_01', 'cp_tomate', 6.0, 1.0, 0.166, 15, '2026-10-21', '2026-11-08', 0.1, 'ch_aurrera'),
        ('cns_06', 'usr_01', 'cp_tortilla_maiz', 5.0, 1.6, 0.320, 18, '2026-11-04', '2026-11-09', 0.3, 'ch_heb'),
        ('cns_07', 'usr_01', 'cp_limon', 7.0, 0.8, 0.114, 16, '2026-11-04', '2026-11-11', 0.5, 'ch_aurrera'),
        ('cns_08', 'usr_01', 'cp_huevo_blanco_12', 10.0, 1.0, 0.100, 10, '2026-11-04', '2026-11-14', 0.6, 'ch_aurrera'),
        ('cns_09', 'usr_01', 'cp_cafe_house_blend', 25.0, 2.0, 0.080, 6, '2026-10-21', '2026-11-15', 0.7, 'ch_heb'),
        ('cns_10', 'usr_01', 'cp_detergente_roma_1k', 30.0, 1.0, 0.033, 5, '2026-10-31', '2026-11-30', 0.8, 'ch_aurrera'),
        ('cns_11', 'usr_01', 'cp_fresas_congeladas_2k', 35.0, 1.0, 0.028, 4, '2026-10-30', '2026-12-04', 1.5, 'ch_sams')
    ]
    c.executemany("INSERT INTO user_product_consumption VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", consumption_data)
    
    # 11. Lista Sugerida con Peso y Volumen para la Canasta de la Bicicleta Eléctrica
    c.execute("""
    INSERT INTO shopping_lists VALUES (
        'lst_sug_01', 'usr_01', 'Ruta en Bicicleta Eléctrica (Semanal)',
        'SUGGESTED', 'AUTO_PREDICTOR', 650.00, '2026-11-09'
    )""")
    
    suggested_items = [
        ('sli_01', 'lst_sug_01', 'cp_pollo_pierna_muslo', 4.0, 'kg', 'DEPLETED', 'ch_marlan', 'PHYSICAL', 175.60, 4.00, 4.60),
        ('sli_02', 'lst_sug_01', 'cp_sopa_maruchan', 4.0, 'piece', 'DEPLETED', 'ch_heb', 'PHYSICAL', 27.60, 0.34, 1.40),
        ('sli_03', 'lst_sug_01', 'cp_tomate', 1.2, 'kg', 'DEPLETED', 'ch_aurrera', 'PHYSICAL', 15.48, 1.20, 1.80),
        ('sli_04', 'lst_sug_01', 'cp_platano', 1.5, 'kg', 'LOW_STOCK', 'ch_aurrera', 'PHYSICAL', 25.50, 1.50, 2.70),
        ('sli_05', 'lst_sug_01', 'cp_leche_entera_1l', 2.0, 'piece', 'LOW_STOCK', 'ch_heb', 'PHYSICAL', 73.80, 2.08, 2.20),
        ('sli_06', 'lst_sug_01', 'cp_tortilla_maiz', 2.0, 'pack', 'LOW_STOCK', 'ch_heb', 'PHYSICAL', 37.00, 1.60, 1.80),
        ('sli_07', 'lst_sug_01', 'cp_huevo_blanco_12', 1.0, 'pack', 'UPCOMING', 'ch_aurrera', 'PHYSICAL', 27.00, 0.78, 2.40)
    ]
    c.executemany("INSERT INTO shopping_list_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", suggested_items)

    # 12. Ejemplo de Fotografía de Carrito Antes de Pagar (Pre-Checkout Snapshot)
    c.execute("""
    INSERT INTO cart_snapshots VALUES (
        'snap_01', 'usr_01', 'st_heb_sn', 'content://listio/cart_snapshots/heb_20261108.jpg',
        '2026-11-08 14:30:00', 5, 381.90, 8.72, 11.70, 'OK',
        'Fondo (Base Rígida): 2x Leche Entera 1L, 4kg Pierna/Muslo | Nivel Medio: 2x Tortilla Maíz | Cima (Frágil): 12 Huevos y 1.5kg Plátanos'
    )""")

    conn.commit()
    print("Base de datos 'listio.db' actualizada con métricas de E-Bike y Pre-Checkout Cart Vision.")

if __name__ == "__main__":
    conn = init_db()
    populate_data(conn)
    conn.close()
