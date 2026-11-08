-- ============================================================================
-- PROYECTO: LISTIO - SISTEMA INTELIGENTE DE COMPRAS Y OPTIMIZACIÓN DE ITINERARIOS
-- SCHEMA: PostgreSQL DDL para Ingesta de Recibos, Consumo Predictivo y Precios Omnicanal
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Búsqueda difusa para normalización de texto OCR

-- ----------------------------------------------------------------------------
-- 1. USUARIOS Y PREFERENCIAS
-- ----------------------------------------------------------------------------
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    default_home_lat NUMERIC(10, 7),
    default_home_lng NUMERIC(10, 7),
    home_address_text TEXT,
    max_stores_per_trip INT DEFAULT 3,
    travel_cost_per_km NUMERIC(6, 2) DEFAULT 3.50, -- Costo estimado gasolina + desgaste en MXN/km
    time_cost_per_hour NUMERIC(6, 2) DEFAULT 80.00, -- Valor subjetivo del tiempo del usuario en MXN/h
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_payment_methods (
    payment_method_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    card_alias VARCHAR(50), -- Ej: 'Bancomer Crédito Term 8813', 'Broxel Débito', 'Santander 3903'
    card_brand VARCHAR(50), -- VISA, MASTERCARD, PROSA, CARNET
    masked_pan VARCHAR(20), -- '************8813', '**03 I'
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_loyalty_accounts (
    loyalty_account_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    program_name VARCHAR(100) NOT NULL, -- 'Soriana YA', 'Sams Club PLUS', 'Puntos BBVA'
    member_number VARCHAR(100),
    points_balance NUMERIC(10, 2) DEFAULT 0.0,
    electronic_cash_balance NUMERIC(10, 2) DEFAULT 0.0, -- Dinero electrónico disponible (ej. Soriana)
    cashback_balance NUMERIC(10, 2) DEFAULT 0.0, -- Recompensa acumulada Sam's
    expiration_date DATE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. CADENAS, TIENDAS FÍSICAS Y TIENDAS EN LÍNEA (OMNICANAL)
-- ----------------------------------------------------------------------------
CREATE TABLE retail_chains (
    chain_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL, -- 'HEB', 'SORIANA', 'AURRERA', 'SAMS', 'OXXO', 'EL_MAS_POLLO', 'TRES_HORACIOS'
    legal_name VARCHAR(255) NOT NULL, -- 'Tiendas Soriana S.A. de C.V.', 'Nueva Wal Mart de Mexico'
    commercial_name VARCHAR(255) NOT NULL,
    tax_id_rfc VARCHAR(20), -- 'TS0991022PB6', 'NWM9709244W4', 'AML8910189F0', 'CCO-860523-1N4'
    primary_category VARCHAR(100) DEFAULT 'SUPERMARKET', -- SUPERMARKET, WHOLESALE_CLUB, BUTCHER, CONVENIENCE
    logo_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE physical_stores (
    store_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id UUID NOT NULL REFERENCES retail_chains(chain_id),
    branch_name VARCHAR(255) NOT NULL, -- 'H San Nicolas (12)', 'Unidad Sams Universidad Monterrey', 'Unidad Santo Domingo'
    branch_internal_code VARCHAR(50), -- 'TDA#4727', 'H 12', 'TDA#3801', 'SUC_SANNICOLAS'
    street_address TEXT NOT NULL,
    neighborhood VARCHAR(150), -- 'El Roble', 'Chapultepec', 'Centro', 'Santo Domingo'
    municipality VARCHAR(150) DEFAULT 'San Nicolás de los Garza',
    state VARCHAR(100) DEFAULT 'Nuevo León',
    postal_code VARCHAR(10) DEFAULT '66450',
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    phone VARCHAR(50),
    has_self_checkout BOOLEAN DEFAULT FALSE,
    opening_time TIME DEFAULT '07:00:00',
    closing_time TIME DEFAULT '22:00:00',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE online_stores (
    online_store_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id UUID NOT NULL REFERENCES retail_chains(chain_id),
    platform_name VARCHAR(100) NOT NULL, -- 'HEB Online', 'Soriana Digital', 'Despensa Bodega Aurrera', 'Sams.com.mx'
    base_url TEXT NOT NULL,
    standard_shipping_fee NUMERIC(8, 2) DEFAULT 49.00,
    free_shipping_threshold NUMERIC(8, 2) DEFAULT 800.00,
    typical_delivery_hours INT DEFAULT 24,
    has_pickup_option BOOLEAN DEFAULT TRUE,
    pickup_fee NUMERIC(8, 2) DEFAULT 0.00,
    scraper_source_code VARCHAR(50), -- Identificador del extractor o webhook de precios online
    is_active BOOLEAN DEFAULT TRUE
);

-- ----------------------------------------------------------------------------
-- 3. CATÁLOGO CANÓNICO DE PRODUCTOS Y MAPEO MULTITIENDA
-- ----------------------------------------------------------------------------
CREATE TABLE product_categories (
    category_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID REFERENCES product_categories(category_id),
    name VARCHAR(100) NOT NULL, -- 'Carnes y Aves', 'Frutas y Verduras', 'Lácteos y Huevos', 'Abarrotes', 'Limpieza'
    slug VARCHAR(100) UNIQUE NOT NULL,
    default_shelf_life_days INT DEFAULT 30 -- Vida útil promedio estimada de la categoría
);

CREATE TABLE canonical_products (
    product_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id UUID REFERENCES product_categories(category_id),
    canonical_name VARCHAR(255) NOT NULL, -- 'Plátano Cavendish / Tabasco', 'Pechuga de Pollo Deshuesada'
    standard_unit VARCHAR(20) NOT NULL, -- 'kg', 'g', 'l', 'ml', 'piece', 'pack'
    brand VARCHAR(100), -- 'HEB', 'Great Value', 'Alpura', 'SuKarne', 'Lala', 'Genérico'
    estimated_shelf_life_days INT, -- Días antes de caducar/agotarse en casa (ej. Plátano=5, Leche=7, Arroz=90)
    is_perishable BOOLEAN DEFAULT TRUE,
    storage_type VARCHAR(50) DEFAULT 'ROOM_TEMP', -- 'ROOM_TEMP', 'REFRIGERATED', 'FROZEN'
    unit_weight_kg NUMERIC(6, 3) DEFAULT 0.500, -- Peso estimado por unidad estándar para cálculo de canasta E-Bike
    unit_volume_liters NUMERIC(6, 3) DEFAULT 0.800, -- Volumen ocupado en litros (capacidad máxima 28.0 L)
    fragility_tier VARCHAR(30) DEFAULT '2_MIDDLE_FIRM', -- '1_BASE_HEAVY', '2_MIDDLE_FIRM', '3_TOP_FRAGILE'
    thermal_sensitivity VARCHAR(30) DEFAULT 'AMBIENT', -- 'AMBIENT', 'CHILLED', 'FROZEN' (para orden de paradas)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Mapeo de artículos tal como aparecen en los tickets o tiendas en línea
CREATE TABLE store_products (
    store_product_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id UUID NOT NULL REFERENCES retail_chains(chain_id),
    product_id UUID REFERENCES canonical_products(product_id), -- Vínculo canónico normalizado
    raw_ticket_description VARCHAR(255) NOT NULL, -- 'PLATANO', 'PLATANO CHIA', 'PLATANO KG', 'PIERNA DE CERDO C H REB'
    store_sku VARCHAR(100), -- '40112', '002', '980000690', '13143'
    barcode_ean_upc VARCHAR(50), -- '7501518461190', '7501791666787'
    is_weighable BOOLEAN DEFAULT FALSE, -- TRUE si se vende por peso (KG), FALSE si es pieza fija
    pack_size_quantity NUMERIC(10, 3) DEFAULT 1.0, -- Tamaño del paquete en unidades estándar (ej: 2.0 para bolsa 2kg)
    pack_unit VARCHAR(20) DEFAULT 'piece',
    tax_type VARCHAR(20) DEFAULT 'EXEMPT', -- 'IVA_16', 'IEPS_8', 'IEPS_53', 'EXEMPT'
    confidence_score NUMERIC(4, 3) DEFAULT 1.0, -- Confianza del emparejamiento con el producto canónico
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product_aliases (
    alias_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES canonical_products(product_id) ON DELETE CASCADE,
    alias_text VARCHAR(255) NOT NULL, -- 'PLATANO ROATAN', 'BANANA', 'GUINEO'
    source VARCHAR(50) DEFAULT 'OCR_LEARNING'
);

-- ----------------------------------------------------------------------------
-- 4. INGESTA DE FOTOGRAFÍAS DE RECIBOS (OCR & MACHINE LEARNING PIPELINE)
-- ----------------------------------------------------------------------------
CREATE TABLE receipt_uploads (
    upload_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    file_storage_url TEXT NOT NULL,
    file_sha256 VARCHAR(64) NOT NULL, -- Prevención de recibos duplicados
    file_size_bytes INT,
    mime_type VARCHAR(50) DEFAULT 'image/jpeg',
    status VARCHAR(50) DEFAULT 'PENDING', -- 'PENDING', 'PROCESSING', 'EXTRACTED', 'VALIDATED', 'FAILED'
    ocr_engine VARCHAR(50) DEFAULT 'GEMINI_VISION',
    raw_ocr_json JSONB, -- Estructura completa devuelta por el modelo de visión
    parsing_error_log TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE raw_receipt_lines (
    raw_line_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_id UUID NOT NULL REFERENCES receipt_uploads(upload_id) ON DELETE CASCADE,
    line_number INT NOT NULL,
    bounding_box JSONB, -- [x_min, y_min, x_max, y_max] para interfaz de corrección visual
    raw_text TEXT NOT NULL,
    detected_item_desc TEXT,
    detected_qty NUMERIC(10, 3),
    detected_unit_price NUMERIC(10, 2),
    detected_total_price NUMERIC(10, 2),
    is_cancelled BOOLEAN DEFAULT FALSE,
    confidence_score NUMERIC(4, 3)
);

-- ----------------------------------------------------------------------------
-- 4B. AUDITORÍA VISUAL DE CARRITO PRE-PAGO Y FOTOS DE PRODUCTOS (E-BIKE & EDGE GALLERY)
-- ----------------------------------------------------------------------------
CREATE TABLE cart_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    chain_id UUID REFERENCES retail_chains(chain_id),
    photo_uri TEXT NOT NULL, -- Fotografía tomada al carrito antes de pasar a caja
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    estimated_total_mxn NUMERIC(10, 2) DEFAULT 0.0,
    estimated_weight_kg NUMERIC(6, 2) DEFAULT 0.0, -- Límite de canasta E-Bike: 15.0 kg
    estimated_volume_liters NUMERIC(6, 2) DEFAULT 0.0, -- Límite de canasta E-Bike: 28.0 L
    ebike_capacity_status VARCHAR(30) DEFAULT 'OPTIMAL', -- 'OPTIMAL', 'WARNING_NEAR_LIMIT', 'EXCEEDS_BASKET'
    edge_gallery_analysis_json JSONB, -- Respuesta del modelo local en Google AI Edge Gallery
    notes TEXT
);

CREATE TABLE cart_snapshot_items (
    snapshot_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_id UUID NOT NULL REFERENCES cart_snapshots(snapshot_id) ON DELETE CASCADE,
    product_id UUID REFERENCES canonical_products(product_id),
    detected_name VARCHAR(255) NOT NULL,
    quantity NUMERIC(10, 3) DEFAULT 1.0,
    estimated_subtotal_mxn NUMERIC(10, 2) DEFAULT 0.0,
    estimated_weight_kg NUMERIC(6, 3) DEFAULT 0.0,
    estimated_volume_liters NUMERIC(6, 3) DEFAULT 0.0,
    stacking_layer VARCHAR(30) DEFAULT '2_MIDDLE_FIRM' -- '1_BASE_HEAVY', '2_MIDDLE_FIRM', '3_TOP_FRAGILE'
);

CREATE TABLE product_photos (
    photo_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES canonical_products(product_id),
    chain_id UUID REFERENCES retail_chains(chain_id),
    photo_uri TEXT NOT NULL,
    captured_price_mxn NUMERIC(10, 2),
    captured_weight_kg NUMERIC(6, 3),
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50) DEFAULT 'CAMERA_CAPTURE' -- 'CAMERA_CAPTURE', 'EDGE_GALLERY_SYNC'
);

-- ----------------------------------------------------------------------------
-- 5. TRANSACCIONES DE COMPRA (RECIBOS VALIDADOS)
-- ----------------------------------------------------------------------------
CREATE TABLE receipts (
    receipt_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_id UUID UNIQUE REFERENCES receipt_uploads(upload_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    store_id UUID REFERENCES physical_stores(store_id),
    chain_id UUID NOT NULL REFERENCES retail_chains(chain_id),
    ticket_number VARCHAR(100), -- '519938', '1005 7215...', 'TC#1314032...'
    transaction_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    cashier_or_register VARCHAR(100), -- 'Cajero AutoCobro #2', 'Caja: Lampazos', 'Horacio J'
    
    -- Balances Financieros
    subtotal_amount NUMERIC(10, 2) NOT NULL,
    discounts_total NUMERIC(10, 2) DEFAULT 0.0, -- Total ahorrado reflejado en ticket
    tax_iva_amount NUMERIC(10, 2) DEFAULT 0.0,
    tax_ieps_amount NUMERIC(10, 2) DEFAULT 0.0,
    rounding_or_donation_amount NUMERIC(10, 2) DEFAULT 0.0, -- Redondeos/Donaciones (Hambre Cero, Down, etc.)
    total_amount NUMERIC(10, 2) NOT NULL,
    total_items_count INT,
    
    -- Validación Contable
    is_mathematically_balanced BOOLEAN DEFAULT TRUE, -- (Subtotal - Ahorros + Impuestos + Donación == Total)
    user_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE receipt_items (
    receipt_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    receipt_id UUID NOT NULL REFERENCES receipts(receipt_id) ON DELETE CASCADE,
    store_product_id UUID REFERENCES store_products(store_product_id),
    product_id UUID REFERENCES canonical_products(product_id), -- Desnormalizado para analítica ágil
    
    raw_description VARCHAR(255) NOT NULL,
    department_or_category VARCHAR(100), -- 'QUESOS Y EMBUTIDOS', 'FRUTAS Y VERDURAS', 'QUIMICOS'
    quantity NUMERIC(10, 3) NOT NULL, -- Cantidad (ej. 1.0 pza o 1.545 kg)
    unit_of_measure VARCHAR(20) DEFAULT 'PIECE', -- 'KG', 'PIECE', 'PACK', 'GRAMS'
    regular_unit_price NUMERIC(10, 2), -- Precio regular unitario
    promotional_unit_price NUMERIC(10, 2), -- Precio promoción unitario (si aplica)
    discount_amount NUMERIC(10, 2) DEFAULT 0.0, -- Rebaja específica en esta línea
    line_total_amount NUMERIC(10, 2) NOT NULL,
    tax_indicator VARCHAR(10), -- 'T' (IVA 16%), 'A' (Exento), 'C' (IEPS)
    is_cancelled BOOLEAN DEFAULT FALSE -- Línea cancelada durante el cobro
);

CREATE TABLE receipt_payments (
    payment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    receipt_id UUID NOT NULL REFERENCES receipts(receipt_id) ON DELETE CASCADE,
    payment_type VARCHAR(50) NOT NULL, -- 'CREDIT_CARD', 'DEBIT_CARD', 'CASH', 'BBVA_POINTS', 'SORIANA_POINTS', 'ELECTRONIC_WALLET'
    card_brand VARCHAR(50), -- 'VISA', 'MASTERCARD', 'PROSA', 'BANCOMER', 'BROXEL'
    masked_card_number VARCHAR(20),
    authorization_code VARCHAR(50),
    amount_paid NUMERIC(10, 2) NOT NULL,
    cash_tendered NUMERIC(10, 2), -- 'Su Pago: $500.00'
    cash_change NUMERIC(10, 2) -- 'Su Cambio: $133.00'
);

CREATE TABLE receipt_loyalty_logs (
    loyalty_log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    receipt_id UUID NOT NULL REFERENCES receipts(receipt_id) ON DELETE CASCADE,
    program_name VARCHAR(100) NOT NULL,
    points_earned NUMERIC(10, 2) DEFAULT 0.0,
    points_redeemed NUMERIC(10, 2) DEFAULT 0.0,
    electronic_cash_earned NUMERIC(10, 2) DEFAULT 0.0,
    reward_earned NUMERIC(10, 2) DEFAULT 0.0 -- Ej: Recompensa Plus Sam's Club
);

-- ----------------------------------------------------------------------------
-- 6. INTELIGENCIA DE PRECIOS Y PROMOCIONES (HISTORIAL FÍSICO Y ONLINE)
-- ----------------------------------------------------------------------------
CREATE TABLE price_observations (
    observation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES canonical_products(product_id),
    store_product_id UUID REFERENCES store_products(store_product_id),
    chain_id UUID NOT NULL REFERENCES retail_chains(chain_id),
    physical_store_id UUID REFERENCES physical_stores(store_id),
    online_store_id UUID REFERENCES online_stores(online_store_id),
    price_channel VARCHAR(20) NOT NULL, -- 'IN_STORE_RECEIPT' vs 'ONLINE_CATALOG'
    
    price_date DATE NOT NULL,
    regular_unit_price NUMERIC(10, 2) NOT NULL,
    promo_unit_price NUMERIC(10, 2),
    is_on_promotion BOOLEAN DEFAULT FALSE,
    promo_mechanism VARCHAR(50), -- 'DIRECT_DISCOUNT', '2X1', '3X20', 'POINTS_DISCOUNT', 'COUPON'
    normalized_price_per_std_unit NUMERIC(10, 2) NOT NULL, -- Normalizado a $/kg o $/litro o $/pza para comparación directa
    
    source_receipt_id UUID REFERENCES receipts(receipt_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 7. CONSUMO PREDICTIVO E INVENTARIO VIRTUAL DEL HOGAR
-- ----------------------------------------------------------------------------
CREATE TABLE user_product_consumption (
    consumption_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    product_id UUID NOT NULL REFERENCES canonical_products(product_id),
    
    avg_reorder_interval_days NUMERIC(6, 2) NOT NULL, -- Ciclo promedio de compra (ej: cada 5.2 días compra plátanos)
    avg_purchase_quantity NUMERIC(10, 3) NOT NULL, -- Cantidad típica por ciclo
    daily_consumption_rate NUMERIC(10, 4) NOT NULL, -- Tasa de agotamiento diario (kg/día o unidades/día)
    
    total_purchases_count INT DEFAULT 1,
    last_purchased_date DATE NOT NULL,
    estimated_depletion_date DATE NOT NULL, -- Fecha estimada en que se acabará el producto en casa
    current_estimated_stock NUMERIC(10, 3) DEFAULT 0.0,
    
    user_is_subscribed BOOLEAN DEFAULT TRUE, -- Si el usuario desea sugerencias automáticas para este producto
    preferred_store_or_chain UUID REFERENCES retail_chains(chain_id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, product_id)
);

-- ----------------------------------------------------------------------------
-- 8. GENERADOR DE LISTAS DE COMPRA INTELIGENTES
-- ----------------------------------------------------------------------------
CREATE TABLE shopping_lists (
    list_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    title VARCHAR(150) NOT NULL DEFAULT 'Lista de Super Sugerida',
    status VARCHAR(50) DEFAULT 'SUGGESTED', -- 'SUGGESTED', 'ACTIVE', 'PLANNED', 'COMPLETED', 'ARCHIVED'
    generated_by VARCHAR(50) DEFAULT 'AUTO_PREDICTOR', -- 'AUTO_PREDICTOR', 'USER_MANUAL', 'HYBRID'
    target_budget NUMERIC(10, 2),
    planned_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE shopping_list_items (
    list_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    list_id UUID NOT NULL REFERENCES shopping_lists(list_id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES canonical_products(product_id),
    
    suggested_quantity NUMERIC(10, 3) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    urgency_level VARCHAR(20) DEFAULT 'NORMAL', -- 'DEPLETED', 'LOW_STOCK', 'UPCOMING', 'OPTIONAL'
    is_checked BOOLEAN DEFAULT FALSE,
    allocated_chain_id UUID REFERENCES retail_chains(chain_id), -- Tienda óptima asignada
    allocated_channel VARCHAR(20) DEFAULT 'PHYSICAL', -- 'PHYSICAL' vs 'ONLINE_DELIVERY'
    estimated_item_cost NUMERIC(10, 2)
);

-- ----------------------------------------------------------------------------
-- 9. OPTIMIZADOR DE ITINERARIOS Y ASIGNACIÓN DE CANASTA (ROUTE & TSP OPTIMIZER)
-- ----------------------------------------------------------------------------
CREATE TABLE trip_itineraries (
    itinerary_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    list_id UUID NOT NULL REFERENCES shopping_lists(list_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    
    strategy VARCHAR(50) DEFAULT 'OPTIMAL_SPLIT', -- 'SINGLE_STORE_FASTEST', 'OPTIMAL_SPLIT', 'HYBRID_ONLINE_PHYSICAL'
    total_estimated_product_cost NUMERIC(10, 2) NOT NULL,
    single_store_baseline_cost NUMERIC(10, 2), -- Costo si comprara todo en la tienda más cara/única
    gross_product_savings NUMERIC(10, 2) GENERATED ALWAYS AS (single_store_baseline_cost - total_estimated_product_cost) STORED,
    
    total_travel_distance_km NUMERIC(6, 2) DEFAULT 0.0,
    total_travel_time_minutes INT DEFAULT 0,
    estimated_fuel_cost NUMERIC(8, 2) DEFAULT 0.0,
    net_savings NUMERIC(10, 2), -- Ahorro bruto en productos menos costo de traslado
    
    itinerary_status VARCHAR(50) DEFAULT 'PROPOSED', -- 'PROPOSED', 'ACCEPTED', 'EXECUTED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE itinerary_stops (
    stop_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    itinerary_id UUID NOT NULL REFERENCES trip_itineraries(itinerary_id) ON DELETE CASCADE,
    stop_sequence INT NOT NULL, -- 1, 2, 3...
    physical_store_id UUID REFERENCES physical_stores(store_id),
    online_store_id UUID REFERENCES online_stores(online_store_id),
    stop_type VARCHAR(20) NOT NULL, -- 'PHYSICAL_VISIT' vs 'ONLINE_ORDER'
    estimated_stop_duration_min INT DEFAULT 20,
    items_to_buy_count INT NOT NULL,
    subtotal_for_stop NUMERIC(10, 2) NOT NULL
);

CREATE TABLE itinerary_item_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stop_id UUID NOT NULL REFERENCES itinerary_stops(stop_id) ON DELETE CASCADE,
    list_item_id UUID NOT NULL REFERENCES shopping_list_items(list_item_id),
    allocated_store_product_id UUID REFERENCES store_products(store_product_id),
    expected_unit_price NUMERIC(10, 2) NOT NULL,
    expected_total_price NUMERIC(10, 2) NOT NULL,
    reason_for_assignment TEXT -- 'Mejor precio por kilo ($43.90 vs $89.00 en HEB)' o 'Promoción 2x1 activa'
);

-- ----------------------------------------------------------------------------
-- 10. ÍNDICES ESTRATÉGICOS Y VISTAS ANALÍTICAS
-- ----------------------------------------------------------------------------
CREATE INDEX idx_receipts_user_date ON receipts(user_id, transaction_timestamp);
CREATE INDEX idx_receipt_items_product ON receipt_items(product_id);
CREATE INDEX idx_store_products_lookup ON store_products(chain_id, store_sku, barcode_ean_upc);
CREATE INDEX idx_raw_ticket_trgm ON store_products USING gin (raw_ticket_description gin_trgm_ops);
CREATE INDEX idx_price_observations_prod_date ON price_observations(product_id, price_date);
CREATE INDEX idx_receipt_uploads_sha ON receipt_uploads(file_sha256);

-- Vista: Comparativa de Precios más recientes por Producto en distintas tiendas
CREATE OR REPLACE VIEW v_latest_product_prices AS
WITH ranked_prices AS (
    SELECT 
        po.product_id,
        cp.canonical_name,
        rc.commercial_name AS chain_name,
        po.price_channel,
        po.price_date,
        po.regular_unit_price,
        po.promo_unit_price,
        po.is_on_promotion,
        po.normalized_price_per_std_unit,
        cp.standard_unit,
        ROW_NUMBER() OVER (
            PARTITION BY po.product_id, po.chain_id, po.price_channel 
            ORDER BY po.price_date DESC, po.created_at DESC
        ) as rn
    FROM price_observations po
    JOIN canonical_products cp ON po.product_id = cp.product_id
    JOIN retail_chains rc ON po.chain_id = rc.chain_id
)
SELECT 
    product_id,
    canonical_name,
    chain_name,
    price_channel,
    price_date,
    COALESCE(promo_unit_price, regular_unit_price) AS effective_unit_price,
    normalized_price_per_std_unit,
    standard_unit,
    is_on_promotion
FROM ranked_prices
WHERE rn = 1;

-- Vista: Estado del Inventario Virtual y Artículos a Reponer
CREATE OR REPLACE VIEW v_inventory_replenishment_needed AS
SELECT 
    upc.user_id,
    cp.canonical_name,
    cat.name AS category_name,
    upc.last_purchased_date,
    upc.avg_reorder_interval_days,
    upc.current_estimated_stock,
    cp.standard_unit,
    upc.estimated_depletion_date,
    (CURRENT_DATE - upc.last_purchased_date) AS days_since_last_purchase,
    CASE 
        WHEN CURRENT_DATE >= upc.estimated_depletion_date THEN 'AGOTADO_URGENTE'
        WHEN CURRENT_DATE >= (upc.estimated_depletion_date - INTERVAL '2 days') THEN 'STOCK_BAJO'
        ELSE 'NORMAL'
    END AS replenishment_status
FROM user_product_consumption upc
JOIN canonical_products cp ON upc.product_id = cp.product_id
LEFT JOIN product_categories cat ON cp.category_id = cat.category_id
WHERE upc.user_is_subscribed = TRUE
ORDER BY upc.estimated_depletion_date ASC;
