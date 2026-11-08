"""
seed_data.py
Crea la base de datos SQLite 'listio.db' con el esquema optimizado y puebla
las tablas con información estructurada extraída de los recibos de los PDFs adjuntos.
"""

import sqlite3
import datetime
import json
import os

DB_FILE = "listio.db"

def init_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Tablas Base
    c.executescript("""
    CREATE TABLE users (
        user_id TEXT PRIMARY KEY,
        email TEXT UNIQUE,
        full_name TEXT,
        default_home_lat REAL,
        default_home_lng REAL,
        home_address_text TEXT,
        max_stores_per_trip INTEGER DEFAULT 3,
        travel_cost_per_km REAL DEFAULT 3.50,
        time_cost_per_hour REAL DEFAULT 80.00,
        created_at TEXT
    );

    CREATE TABLE user_payment_methods (
        payment_method_id TEXT PRIMARY KEY,
        user_id TEXT REFERENCES users(user_id),
        card_alias TEXT,
        card_brand TEXT,
        masked_pan TEXT
    );

    CREATE TABLE user_loyalty_accounts (
        loyalty_account_id TEXT PRIMARY KEY,
        user_id TEXT REFERENCES users(user_id),
        program_name TEXT,
        member_number TEXT,
        points_balance REAL,
        electronic_cash_balance REAL,
        cashback_balance REAL
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
        phone TEXT
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
        storage_type TEXT
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

    CREATE TABLE receipt_payments (
        payment_id TEXT PRIMARY KEY,
        receipt_id TEXT REFERENCES receipts(receipt_id),
        payment_type TEXT,
        card_brand TEXT,
        masked_card_number TEXT,
        authorization_code TEXT,
        amount_paid REAL,
        cash_tendered REAL,
        cash_change REAL
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
        estimated_item_cost REAL
    );
    """)
    conn.commit()
    print("Tablas creadas exitosamente.")
    return conn

def populate_data(conn):
    c = conn.cursor()
    
    # 1. Usuario
    c.execute("""
    INSERT INTO users VALUES (
        'usr_01', 'yesser.caraballo@example.com', 'Yesser Caraballo Guzmán',
        25.7483, -100.2882, 'San Nicolás de los Garza Centro, NL, CP 66400',
        3, 3.50, 80.00, '2026-01-01'
    )""")
    
    # Métodos de Pago
    c.executemany("INSERT INTO user_payment_methods VALUES (?, ?, ?, ?, ?)", [
        ('pm_01', 'usr_01', 'Bancomer Crédito 8813', 'VISA', '************8813'),
        ('pm_02', 'usr_01', 'Santander Crédito 3903', 'VISA', '************3903'),
        ('pm_03', 'usr_01', 'BBVA Débito Broxel', 'BROXEL', '************8813'),
        ('pm_04', 'usr_01', 'Bancomer Crédito 03 I', 'VISA', '**03 I')
    ])
    
    # Cuentas de Lealtad
    c.executemany("INSERT INTO user_loyalty_accounts VALUES (?, ?, ?, ?, ?, ?, ?)", [
        ('loy_01', 'usr_01', 'Soriana YA', 'YESSER CARABALLO GUZMAN', 595.0, 254.45, 0.0),
        ('loy_02', 'usr_01', 'Sams Club PLUS', '3043', 0.0, 0.0, 21.12),
        ('loy_03', 'usr_01', 'Puntos BBVA', 'YESSER', 700.0, 49.00, 0.0)
    ])
    
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
    
    # Tiendas Físicas
    c.executemany("INSERT INTO physical_stores VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        ('st_heb_sn', 'ch_heb', 'HEB Universidad San Nicolás', '671/673/674/675/676', 'Av Universidad 101', 'Anáhuac', 'San Nicolás de los Garza', 'Nuevo León', '66450', 25.7350, -100.2990, '81-8153-1200'),
        ('st_sor_sn', 'ch_soriana', 'Soriana Híper San Nicolás (12)', 'H 12', 'Ave Alfonso Reyes 601', 'El Roble', 'San Nicolás de los Garza', 'Nuevo León', '66450', 25.7420, -100.3015, '81-8376-4400'),
        ('st_aur_stdgo', 'ch_aurrera', 'Bodega Aurrera Santo Domingo', 'TDA#3801', 'Av. Sto. Domingo SN', 'Santo Domingo', 'San Nicolás de los Garza', 'Nuevo León', '66430', 25.7510, -100.2720, '800-925-6278'),
        ('st_sams_uni', 'ch_sams', 'Sam\'s Club Universidad Monterrey', 'TDA#4727', 'Av. Universidad #413', 'El Roble', 'San Nicolás de los Garza', 'Nuevo León', '66500', 25.7380, -100.2980, '81-8158-4700'),
        ('st_mar_lamp', 'ch_marlan', 'El Más Pollo - Lampazos', 'SUC_LAMPAZOS', 'Lampazos #207', 'Chapultepec', 'San Nicolás de los Garza', 'Nuevo León', '66450', 25.7440, -100.2920, '8221194210'),
        ('st_mar_sn', 'ch_marlan', 'El Más Pollo - San Nicolás Centro', 'SUC_SANNICOLAS', 'Arturo B. de la Garza #321', 'Centro', 'San Nicolás de los Garza', 'Nuevo León', '66450', 25.7490, -100.2870, '8114010093'),
        ('st_horacios', 'ch_horacios', 'Tres Horacios Boutique', 'TIII1', 'Mariano Matamoros 430', 'Centro', 'San Nicolás de los Garza', 'Nuevo León', '66400', 25.7475, -100.2865, '81-2233-4455'),
        ('st_oxxo_pino', 'ch_oxxo', 'OXXO Pino NLD', '10NLA50QU62', 'Arturo B. de la Garza #701', 'Centro', 'San Nicolás de los Garza', 'Nuevo León', '66400', 25.7505, -100.2850, '83202020')
    ])
    
    # Tiendas en Línea
    c.executemany("INSERT INTO online_stores VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
        ('on_heb', 'ch_heb', 'HEB Digital App & Web', 'https://www.heb.com.mx', 49.00, 700.00, 4, 1),
        ('on_soriana', 'ch_soriana', 'Soriana.com Super en tu Casa', 'https://www.soriana.com', 49.00, 800.00, 6, 1),
        ('on_aurrera', 'ch_aurrera', 'Despensa Bodega Aurrera Online', 'https://despensa.bodegaaurrera.com.mx', 39.00, 499.00, 24, 1),
        ('on_sams', 'ch_sams', 'Sam\'s Club México Online', 'https://www.sams.com.mx', 65.00, 1200.00, 24, 1)
    ])
    
    # Categorías
    c.executemany("INSERT INTO product_categories VALUES (?, ?, ?, ?)", [
        ('cat_frescos', 'Frutas y Verduras', 'frutas-y-verduras', 6),
        ('cat_carnes', 'Carnes y Pollo', 'carnes-y-pollo', 5),
        ('cat_lacteos', 'Lácteos y Huevos', 'lacteos-y-huevos', 10),
        ('cat_abarrotes', 'Abarrotes Básicos', 'abarrotes-basicos', 45),
        ('cat_panaderia', 'Panadería y Tortillería', 'panaderia-tortilleria', 5),
        ('cat_limpieza', 'Limpieza y Hogar', 'limpieza-hogar', 60),
        ('cat_congelados', 'Congelados', 'congelados', 90)
    ])
    
    # Productos Canónicos Maestros
    canonical_prods = [
        ('cp_platano', 'cat_frescos', 'Plátano Cavendish / Tabasco', 'kg', 'Genérico', 5, 1, 'ROOM_TEMP'),
        ('cp_limon', 'cat_frescos', 'Limón Agrio con Semilla', 'kg', 'Genérico', 12, 1, 'REFRIGERATED'),
        ('cp_tomate', 'cat_frescos', 'Tomate Saladette / Huaje', 'kg', 'Genérico', 7, 1, 'ROOM_TEMP'),
        ('cp_aguacate', 'cat_frescos', 'Aguacate Hass', 'kg', 'Genérico', 5, 1, 'ROOM_TEMP'),
        ('cp_cebolla_bca', 'cat_frescos', 'Cebolla Blanca', 'kg', 'Genérico', 14, 1, 'ROOM_TEMP'),
        ('cp_camote_amarillo', 'cat_frescos', 'Camote Amarillo', 'kg', 'Genérico', 10, 1, 'ROOM_TEMP'),
        ('cp_naranja', 'cat_frescos', 'Naranja Valencia / Jugo', 'kg', 'Genérico', 10, 1, 'ROOM_TEMP'),
        ('cp_manzana', 'cat_frescos', 'Manzana Ambrosia / Red Delicious', 'kg', 'Genérico', 14, 1, 'REFRIGERATED'),
        ('cp_papaya', 'cat_frescos', 'Papaya Maradol', 'kg', 'Genérico', 5, 1, 'REFRIGERATED'),
        
        ('cp_pollo_pierna_muslo', 'cat_carnes', 'Pierna y Muslo de Pollo Fresco', 'kg', 'Genérico', 4, 1, 'REFRIGERATED'),
        ('cp_pollo_milanesa', 'cat_carnes', 'Milanesa de Pechuga de Pollo', 'kg', 'Genérico', 4, 1, 'REFRIGERATED'),
        ('cp_cerdo_pierna', 'cat_carnes', 'Pierna de Cerdo Rebanada / Sin Hueso', 'kg', 'Genérico', 5, 1, 'REFRIGERATED'),
        ('cp_cerdo_chuleta', 'cat_carnes', 'Chuleta de Lomo / Sirloin de Cerdo', 'kg', 'Genérico', 5, 1, 'REFRIGERATED'),
        ('cp_res_molida', 'cat_carnes', 'Carne Molida de Res 80/20', 'kg', 'Genérico', 4, 1, 'REFRIGERATED'),
        
        ('cp_leche_entera_1l', 'cat_lacteos', 'Leche Entera Pasteurizada 1L', 'piece', 'HEB', 8, 1, 'REFRIGERATED'),
        ('cp_leche_alpura_polvo', 'cat_lacteos', 'Leche Deslactosada en Polvo Alpura', 'piece', 'Alpura', 60, 0, 'ROOM_TEMP'),
        ('cp_huevo_blanco_12', 'cat_lacteos', 'Huevo Blanco Paquete 12 Piezas', 'pack', 'Economax', 18, 1, 'ROOM_TEMP'),
        ('cp_queso_oaxaca', 'cat_lacteos', 'Queso Oaxaca Tradicional', 'kg', 'Genérico', 14, 1, 'REFRIGERATED'),
        ('cp_queso_crema', 'cat_lacteos', 'Queso Crema Philadelphia / HCF', 'piece', 'Philadelphia', 25, 1, 'REFRIGERATED'),
        ('cp_yogurt_natural', 'cat_lacteos', 'Yogurt Natural Sin Azúcar 1kg', 'piece', 'Genérico', 15, 1, 'REFRIGERATED'),
        ('cp_mantequilla_barra', 'cat_lacteos', 'Mantequilla Gloria Barra 90g', 'piece', 'Gloria', 30, 1, 'REFRIGERATED'),
        
        ('cp_tortilla_maiz', 'cat_panaderia', 'Tortilla de Maíz Nixtamalizada 1kg', 'kg', 'Genérico', 4, 1, 'ROOM_TEMP'),
        ('cp_bolillo_integral', 'cat_panaderia', 'Bolillo Integral 75g', 'piece', 'Panadería', 3, 1, 'ROOM_TEMP'),
        ('cp_pan_tostado', 'cat_panaderia', 'Pan Tostado Integral 350-400g', 'piece', 'Bimbo / HEB', 30, 0, 'ROOM_TEMP'),
        
        ('cp_cafe_house_blend', 'cat_abarrotes', 'Café House Blend Molido 1kg HEB', 'piece', 'HEB', 30, 0, 'ROOM_TEMP'),
        ('cp_arroz_1kg', 'cat_abarrotes', 'Arroz Super Extra 900g-1kg', 'piece', 'Mi Tienda / Precissimo', 90, 0, 'ROOM_TEMP'),
        ('cp_fresas_congeladas_2k', 'cat_congelados', 'Fresas Congeladas Bolsa 2kg', 'piece', 'Member\'s Mark / HEB', 120, 0, 'FROZEN'),
        ('cp_sardina_tomate', 'cat_abarrotes', 'Sardina en Salsa de Tomate 425g', 'piece', 'Valley Food / AU', 180, 0, 'ROOM_TEMP'),
        ('cp_sopa_maruchan', 'cat_abarrotes', 'Sopa Instantánea Ramen Pollo 85g', 'piece', 'Maruchan', 90, 0, 'ROOM_TEMP'),
        
        ('cp_detergente_roma_1k', 'cat_limpieza', 'Detergente en Polvo Roma 1kg', 'piece', 'Roma', 90, 0, 'ROOM_TEMP'),
        ('cp_jabon_zote_barra', 'cat_limpieza', 'Jabón de Lavandería Zote Barra 200g-400g', 'piece', 'Zote', 120, 0, 'ROOM_TEMP'),
        ('cp_bolsa_basura', 'cat_limpieza', 'Bolsas para Basura Mediana 20 Pz', 'pack', 'Mi Tienda', 90, 0, 'ROOM_TEMP')
    ]
    c.executemany("INSERT INTO canonical_products VALUES (?, ?, ?, ?, ?, ?, ?, ?)", canonical_prods)
    
    # Mapeo de Productos por Tienda (Store Products)
    store_prod_map = [
        # HEB
        ('sp_heb_platano', 'ch_heb', 'cp_platano', 'PLATANO', 'PLU-4011', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_heb_leche_ent', 'ch_heb', 'cp_leche_entera_1l', 'HEB ST LECHE ENTERA', 'HEB-LECH-01', '750100510001', 0, 1.0, 'piece', 'EXEMPT'),
        ('sp_heb_cafe_house', 'ch_heb', 'cp_cafe_house_blend', 'CAFE HOUSE BLEND HEB', 'HEB-CAF-01', '750100510002', 0, 1.0, 'piece', 'EXEMPT'),
        ('sp_heb_huevo_eco', 'ch_heb', 'cp_huevo_blanco_12', 'ECONOMAX HUEVO BAC 12 PZ', 'ECO-HVO-12', '750100510003', 0, 12.0, 'piece', 'EXEMPT'),
        ('sp_heb_tort_bca', 'ch_heb', 'cp_tortilla_maiz', 'TORTILLA MAIZ BLANCA F', 'HEB-TOR-01', None, 0, 1.0, 'piece', 'EXEMPT'),
        ('sp_heb_tort_ama', 'ch_heb', 'cp_tortilla_maiz', 'Tortilla de Maiz Amarilla', 'HEB-TOR-02', None, 0, 1.0, 'piece', 'EXEMPT'),
        ('sp_heb_maruchan', 'ch_heb', 'cp_sopa_maruchan', 'MARUCHAN SOPA RAMEN POLLO', 'MAR-RAM-01', '041789002960', 0, 1.0, 'piece', 'IVA_16'),
        ('sp_heb_yogurt_nat', 'ch_heb', 'cp_yogurt_natural', 'Yogurt Natural SA', 'HEB-YOG-01', None, 0, 1.0, 'piece', 'EXEMPT'),
        ('sp_heb_manteq', 'ch_heb', 'cp_mantequilla_barra', 'GLORIA MANTEQUILLA BARRA', 'GLO-MAN-90', '750102600111', 0, 1.0, 'piece', 'IVA_16'),
        ('sp_heb_limon', 'ch_heb', 'cp_limon', 'LIMON AGRIO SUPREMO', 'PLU-4048', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_heb_tomate', 'ch_heb', 'cp_tomate', 'TOMATE HUAJE SUPREMO', 'PLU-4087', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_heb_pierna_cerdo', 'ch_heb', 'cp_cerdo_pierna', 'PIERNA DE CERDO C H REB', 'CARN-P-CER', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_heb_fresas_cong', 'ch_heb', 'cp_fresas_congeladas_2k', 'HEB FRESAS CONGELADA 2 KG', 'HEB-FRS-2K', '750100510004', 0, 2.0, 'kg', 'EXEMPT'),

        # Soriana
        ('sp_sor_platano', 'ch_soriana', 'cp_platano', 'PLATANO KG', '203', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_sor_pollo_pym', 'ch_soriana', 'cp_pollo_pierna_muslo', 'PIERNA Y MUSLO C/AM', '002', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_sor_cerdo_chuleta', 'ch_soriana', 'cp_cerdo_chuleta', 'CHULETA NATURAL CER', '005', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_sor_cerdo_pierna', 'ch_soriana', 'cp_cerdo_pierna', 'PIERNA CERDO S/HUES', '005', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_sor_sardina', 'ch_soriana', 'cp_sardina_tomate', 'SARDINA VALLEY FOOD', '424', '750102600222', 0, 1.0, 'piece', 'IVA_16'),
        ('sp_sor_arroz', 'ch_soriana', 'cp_arroz_1kg', 'ARROZ EXTRA PRECISS', '689', '750102600333', 0, 1.0, 'piece', 'EXEMPT'),
        ('sp_sor_huevo_12', 'ch_soriana', 'cp_huevo_blanco_12', 'HUEVO BLANCO PAQ 12', '025', '750102600444', 0, 12.0, 'piece', 'EXEMPT'),
        ('sp_sor_cebolla_bca', 'ch_soriana', 'cp_cebolla_bca', 'CEBOLLA BLANCA', '956', None, 1, 1.0, 'kg', 'EXEMPT'),

        # Bodega Aurrera
        ('sp_aur_platano_chia', 'ch_aurrera', 'cp_platano', 'PLATANO CHIA', '40112', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_aur_platano_mach', 'ch_aurrera', 'cp_platano', 'PLATANO MACH', '42352', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_aur_tomate_huaje', 'ch_aurrera', 'cp_tomate', 'TOMAT HUAJE', '40877', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_aur_limon_agrio', 'ch_aurrera', 'cp_limon', 'LIMON AGRIO', '43052', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_aur_camote_ama', 'ch_aurrera', 'cp_camote_amarillo', 'CAMOTE AMA', '48163', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_aur_zote_barra', 'ch_aurrera', 'cp_jabon_zote_barra', 'ZOTE BARRA', '7501026005985', '7501026005985', 0, 1.0, 'piece', 'IVA_16'),
        ('sp_aur_roma_det', 'ch_aurrera', 'cp_detergente_roma_1k', 'ROMA DET 1', '7501026004605', '7501026004605', 0, 1.0, 'piece', 'IVA_16'),
        ('sp_aur_queso_oax', 'ch_aurrera', 'cp_queso_oaxaca', 'QSO OAXACA', '7501040080333', '7501040080333', 0, 0.4, 'kg', 'EXEMPT'),
        ('sp_aur_huevo_12', 'ch_aurrera', 'cp_huevo_blanco_12', 'HVO AU 12P', '7506495008963', '7506495008963', 0, 12.0, 'piece', 'EXEMPT'),
        ('sp_aur_arroz_au', 'ch_aurrera', 'cp_arroz_1kg', 'AU ARROZ 9', '7501791638623', '7501791638623', 0, 0.9, 'piece', 'EXEMPT'),

        # Sam's Club
        ('sp_sams_fresa_2k', 'ch_sams', 'cp_fresas_congeladas_2k', 'MM 2K FRESA', '799257', '799257', 0, 2.0, 'kg', 'IVA_16'),
        ('sp_sams_oaxaca_mm', 'ch_sams', 'cp_queso_oaxaca', 'MM OAXACA', '980000690', '980000690', 0, 1.0, 'kg', 'IVA_16'),
        ('sp_sams_guarnicion', 'ch_sams', 'cp_frescos', '2K GUARNICIO', '13143', '13143', 0, 2.0, 'kg', 'IVA_16'),

        # El Más Pollo (Avipecuaria Marlan)
        ('sp_mar_muslo_raba', 'ch_marlan', 'cp_pollo_pierna_muslo', 'MUSLO CON RABADILLA', 'MAR-01', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_mar_pym_rey', 'ch_marlan', 'cp_pollo_pierna_muslo', 'PIERNA Y MUSLO REY', 'MAR-02', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_mar_huevo_grnl', 'ch_marlan', 'cp_huevo_blanco_12', 'HUEVO', 'MAR-03', None, 1, 1.0, 'kg', 'EXEMPT'),

        # Tres Horacios
        ('sp_tho_milanesa_pollo', 'ch_horacios', 'cp_pollo_milanesa', 'Milanesa de pollo', 'TH-01', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_tho_pierna_trozo', 'ch_horacios', 'cp_pollo_pierna_muslo', 'Pierna de Pollo SH en trozo', 'TH-02', None, 1, 1.0, 'kg', 'EXEMPT'),
        ('sp_tho_lomo_cerdo', 'ch_horacios', 'cp_cerdo_pierna', 'Lomo de Cerdo', 'TH-03', None, 1, 1.0, 'kg', 'EXEMPT')
    ]
    c.executemany("INSERT INTO store_products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", store_prod_map)
    
    # 3. Observaciones de Precios (Histórico Físico y Tiendas en Línea)
    # Precios comparativos reales capturados de los tickets y scraping
    prices = [
        # Plátano ($/kg)
        ('po_01', 'cp_platano', 'sp_heb_platano', 'ch_heb', 'IN_STORE_RECEIPT', '2026-10-21', 21.22, 21.22, 0, None, 21.22),
        ('po_02', 'cp_platano', 'sp_heb_platano', 'ch_heb', 'ONLINE_CATALOG', '2026-11-01', 22.90, 22.90, 0, None, 22.90),
        ('po_03', 'cp_platano', 'sp_aur_platano_chia', 'ch_aurrera', 'IN_STORE_RECEIPT', '2026-10-31', 17.00, 17.00, 0, None, 17.00),
        ('po_04', 'cp_platano', 'sp_aur_platano_chia', 'ch_aurrera', 'ONLINE_CATALOG', '2026-11-01', 16.50, 16.50, 0, None, 16.50),
        ('po_05', 'cp_platano', 'sp_sor_platano', 'ch_soriana', 'IN_STORE_RECEIPT', '2026-10-17', 23.90, 23.30, 1, 'DIRECT_DISCOUNT', 23.30),
        ('po_06', 'cp_platano', 'sp_sor_platano', 'ch_soriana', 'ONLINE_CATALOG', '2026-11-01', 24.90, 24.90, 0, None, 24.90),

        # Pollo Pierna y Muslo ($/kg)
        ('po_07', 'cp_pollo_pierna_muslo', 'sp_mar_muslo_raba', 'ch_marlan', 'IN_STORE_RECEIPT', '2026-10-02', 43.90, 43.90, 0, None, 43.90),
        ('po_08', 'cp_pollo_pierna_muslo', 'sp_sor_pollo_pym', 'ch_soriana', 'IN_STORE_RECEIPT', '2026-10-31', 38.90, 29.90, 1, 'PROMO_MARTES_MIERCOLES', 29.90),
        ('po_09', 'cp_pollo_pierna_muslo', 'sp_sor_pollo_pym', 'ch_soriana', 'ONLINE_CATALOG', '2026-11-01', 38.90, 38.90, 0, None, 38.90),
        ('po_10', 'cp_pollo_pierna_muslo', 'sp_heb_pierna_cerdo', 'ch_heb', 'IN_STORE_RECEIPT', '2026-10-05', 55.00, 55.00, 0, None, 55.00),
        ('po_11', 'cp_pollo_pierna_muslo', 'sp_tho_pierna_trozo', 'ch_horacios', 'IN_STORE_RECEIPT', '2026-10-30', 105.00, 105.00, 0, 'GOURMET_PREMIUM', 105.00),

        # Leche Entera 1L
        ('po_12', 'cp_leche_entera_1l', 'sp_heb_leche_ent', 'ch_heb', 'IN_STORE_RECEIPT', '2026-11-04', 36.90, 36.90, 0, None, 36.90),
        ('po_13', 'cp_leche_entera_1l', 'sp_heb_leche_ent', 'ch_heb', 'ONLINE_CATALOG', '2026-11-01', 36.90, 36.90, 0, None, 36.90),

        # Café House Blend 1kg HEB
        ('po_14', 'cp_cafe_house_blend', 'sp_heb_cafe_house', 'ch_heb', 'IN_STORE_RECEIPT', '2026-10-21', 145.00, 145.00, 0, None, 145.00),
        ('po_15', 'cp_cafe_house_blend', 'sp_heb_cafe_house', 'ch_heb', 'ONLINE_CATALOG', '2026-11-01', 149.00, 149.00, 0, None, 149.00),

        # Huevo 12 piezas
        ('po_16', 'cp_huevo_blanco_12', 'sp_heb_huevo_eco', 'ch_heb', 'IN_STORE_RECEIPT', '2026-11-04', 32.50, 32.50, 0, None, 32.50),
        ('po_17', 'cp_huevo_blanco_12', 'sp_aur_huevo_12', 'ch_aurrera', 'IN_STORE_RECEIPT', '2026-10-11', 26.00, 26.00, 0, None, 26.00),
        ('po_18', 'cp_huevo_blanco_12', 'sp_sor_huevo_12', 'ch_soriana', 'IN_STORE_RECEIPT', '2026-10-17', 31.90, 31.90, 0, None, 31.90),

        # Fresas Congeladas 2kg
        ('po_19', 'cp_fresas_congeladas_2k', 'sp_sams_fresa_2k', 'ch_sams', 'IN_STORE_RECEIPT', '2026-10-30', 163.68, 163.68, 0, None, 81.84), # Normalizado por kg
        ('po_20', 'cp_fresas_congeladas_2k', 'sp_heb_fresas_cong', 'ch_heb', 'IN_STORE_RECEIPT', '2026-07-09', 235.00, 235.00, 0, None, 117.50),

        # Jabón Zote Barra
        ('po_21', 'cp_jabon_zote_barra', 'sp_aur_zote_barra', 'ch_aurrera', 'IN_STORE_RECEIPT', '2026-09-13', 7.50, 6.00, 1, 'MULTIBUY_REBAJA', 6.00),
        ('po_22', 'cp_detergente_roma_1k', 'sp_aur_roma_det', 'ch_aurrera', 'IN_STORE_RECEIPT', '2026-09-13', 40.00, 35.00, 1, 'REBAJA_1X35', 35.00),
        ('po_23', 'cp_detergente_roma_1k', 'sp_aur_roma_det', 'ch_soriana', 'IN_STORE_RECEIPT', '2026-10-31', 42.90, 37.90, 1, 'PROMO_SEMANAL', 37.90)
    ]
    c.executemany("INSERT INTO price_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", prices)
    
    # 4. Transacciones y Tickets Representativos de los PDFs
    c.executemany("INSERT INTO receipts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        ('rc_heb_1104', 'usr_01', 'st_heb_sn', 'ch_heb', '1097 0841 1104 2618 5202 952', '2026-11-04 18:52:00', 'AutoCobro 671', 339.00, 0.0, 0.0, 0.0, 0.21, 339.00, 10, 1),
        ('rc_tho_1030', 'usr_01', 'st_horacios', 'ch_horacios', 'RECB0003ZKXSS3080IKG', '2026-10-30 12:28:43', 'Horacio J (TIII1)', 820.83, 140.00, 0.0, 0.0, 0.0, 820.83, 7, 1),
        ('rc_sams_1030', 'usr_01', 'st_sams_uni', 'ch_sams', '3135965518986460529734', '2026-10-30 18:11:26', 'OP#00000491 TR#05521', 1080.29, 58.30, 0.0, 0.0, 0.0, 1061.89, 8, 1),
        ('rc_sor_1031', 'usr_01', 'st_sor_sn', 'ch_soriana', '00120919059700700226', '2026-10-31 11:29:59', 'Cajero AutoCobro 5', 474.24, 34.65, 19.30, 0.0, 0.0, 439.59, 14, 1),
        ('rc_mar_1002', 'usr_01', 'st_mar_sn', 'ch_marlan', '526218', '2026-10-02 12:17:00', 'M. Rodriguez', 601.25, 0.0, 0.0, 0.0, 0.0, 601.25, 4, 1),
        ('rc_aur_1011', 'usr_01', 'st_aur_stdgo', 'ch_aurrera', 'TC#884808035850709994603', '2026-10-11 19:47:00', 'OP#00000743 TR#09962', 257.12, 33.00, 0.0, 8.88, 0.0, 266.00, 9, 1)
    ])
    
    # 5. Modelado del Consumo Predictivo e Inventario Virtual del Hogar
    consumption_data = [
        ('cns_01', 'usr_01', 'cp_platano', 4.5, 1.2, 0.266, 18, '2026-11-04', '2026-11-09', 1.0, 'ch_aurrera'),
        ('cns_02', 'usr_01', 'cp_leche_entera_1l', 5.0, 2.0, 0.400, 14, '2026-11-04', '2026-11-09', 2.0, 'ch_heb'),
        ('cns_03', 'usr_01', 'cp_huevo_blanco_12', 10.0, 1.0, 0.100, 8, '2026-11-04', '2026-11-14', 1.0, 'ch_aurrera'),
        ('cns_04', 'usr_01', 'cp_cafe_house_blend', 25.0, 2.0, 0.080, 5, '2026-10-21', '2026-11-15', 1.2, 'ch_heb'),
        ('cns_05', 'usr_01', 'cp_pollo_pierna_muslo', 7.0, 4.0, 0.571, 10, '2026-10-31', '2026-11-07', 0.2, 'ch_marlan'), # ¡AGOTADO!
        ('cns_06', 'usr_01', 'cp_limon', 7.0, 0.8, 0.114, 12, '2026-11-04', '2026-11-11', 0.6, 'ch_aurrera'),
        ('cns_07', 'usr_01', 'cp_tomate', 6.0, 1.0, 0.166, 11, '2026-11-04', '2026-11-10', 0.8, 'ch_aurrera'),
        ('cns_08', 'usr_01', 'cp_sopa_maruchan', 12.0, 4.0, 0.333, 9, '2026-10-21', '2026-11-02', 0.0, 'ch_heb'), # ¡AGOTADO!
        ('cns_09', 'usr_01', 'cp_fresas_congeladas_2k', 35.0, 1.0, 0.028, 4, '2026-10-30', '2026-12-04', 1.8, 'ch_sams'),
        ('cns_10', 'usr_01', 'cp_detergente_roma_1k', 30.0, 1.0, 0.033, 4, '2026-10-31', '2026-11-30', 0.9, 'ch_aurrera')
    ]
    c.executemany("INSERT INTO user_product_consumption VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", consumption_data)
    
    # 6. Lista de Super Sugerida Activa
    c.execute("""
    INSERT INTO shopping_lists VALUES (
        'lst_sug_01', 'usr_01', 'Sugerencia Semanal Inteligente (Nov 2026)',
        'SUGGESTED', 'AUTO_PREDICTOR', 850.00, '2026-11-09'
    )""")
    
    # Artículos sugeridos en la lista basados en estado de inventario
    suggested_items = [
        ('sli_01', 'lst_sug_01', 'cp_pollo_pierna_muslo', 4.0, 'kg', 'DEPLETED', 'ch_marlan', 'PHYSICAL', 175.60),
        ('sli_02', 'lst_sug_01', 'cp_sopa_maruchan', 4.0, 'piece', 'DEPLETED', 'ch_heb', 'PHYSICAL', 27.60),
        ('sli_03', 'lst_sug_01', 'cp_platano', 1.5, 'kg', 'LOW_STOCK', 'ch_aurrera', 'PHYSICAL', 25.50),
        ('sli_04', 'lst_sug_01', 'cp_leche_entera_1l', 2.0, 'piece', 'LOW_STOCK', 'ch_heb', 'PHYSICAL', 73.80),
        ('sli_05', 'lst_sug_01', 'cp_tomate', 1.0, 'kg', 'UPCOMING', 'ch_aurrera', 'PHYSICAL', 18.00),
        ('sli_06', 'lst_sug_01', 'cp_huevo_blanco_12', 1.0, 'pack', 'UPCOMING', 'ch_aurrera', 'PHYSICAL', 26.00)
    ]
    c.executemany("INSERT INTO shopping_list_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", suggested_items)
    
    conn.commit()
    print("Datos poblados con éxito.")

if __name__ == "__main__":
    conn = init_db()
    populate_data(conn)
    conn.close()
