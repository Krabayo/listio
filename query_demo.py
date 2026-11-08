"""
query_demo.py
Demostración de las 3 capacidades clave solicitadas por el usuario:
1. Detección predictiva de agotamiento y sugerencia de lista.
2. Comparativa multitienda y multicanal de precios.
3. Algoritmo de itinerario óptimo y división de canasta con cálculo de ahorro neto.
"""

import sys
import io
import sqlite3
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run_analytics():
    conn = sqlite3.connect("listio.db")
    
    print("=" * 80)
    print("1. INVENTARIO VIRTUAL DEL HOGAR Y ARTÍCULOS A REPONER (PREDICTIVE RESTOCK)")
    print("=" * 80)
    query_inventory = """
    SELECT 
        cp.canonical_name AS Producto,
        upc.avg_reorder_interval_days AS Ciclo_Dias,
        upc.last_purchased_date AS Ultima_Compra,
        upc.estimated_depletion_date AS Fecha_Agotamiento,
        upc.current_estimated_stock || ' ' || cp.standard_unit AS Stock_Estimado,
        CASE 
            WHEN date('now') >= upc.estimated_depletion_date THEN '🔴 AGOTADO URGENTE'
            WHEN date('now') >= date(upc.estimated_depletion_date, '-3 days') THEN '🟡 STOCK BAJO'
            ELSE '🟢 BIEN ABASTECIDO'
        END AS Estado
    FROM user_product_consumption upc
    JOIN canonical_products cp ON upc.product_id = cp.product_id
    ORDER BY upc.estimated_depletion_date ASC;
    """
    df_inv = pd.read_sql_query(query_inventory, conn)
    print(df_inv.to_string(index=False))
    
    print("\n" + "=" * 80)
    print("2. COMPARATIVA DE PRECIOS MULTITIENDA Y MULTICANAL (PRICE INTELLIGENCE)")
    print("=" * 80)
    query_prices = """
    SELECT 
        cp.canonical_name AS Producto,
        rc.commercial_name AS Tienda,
        po.price_channel AS Canal,
        po.normalized_price_per_std_unit AS Precio_Normalizado,
        cp.standard_unit AS Unidad,
        po.is_on_promotion AS Promo,
        COALESCE(po.promo_mechanism, 'Precio Regular') AS Tipo_Promo
    FROM price_observations po
    JOIN canonical_products cp ON po.product_id = cp.product_id
    JOIN retail_chains rc ON po.chain_id = rc.chain_id
    WHERE cp.product_id IN ('cp_pollo_pierna_muslo', 'cp_platano', 'cp_fresas_congeladas_2k', 'cp_huevo_blanco_12')
    ORDER BY cp.canonical_name, po.normalized_price_per_std_unit ASC;
    """
    df_prices = pd.read_sql_query(query_prices, conn)
    print(df_prices.to_string(index=False))
    
    print("\n" + "=" * 80)
    print("3. SIMULACIÓN DE OPTIMIZACIÓN DE ITINERARIO (BASKET SPLIT & ROUTE OPTIMIZER)")
    print("=" * 80)
    
    # Canasta activa para este fin de semana:
    # 4 kg Pierna y Muslo Pollo, 2 kg Plátano, 2 L Leche, 1 pack Huevo 12 pz, 1 kg Tomate
    basket = [
        ('cp_pollo_pierna_muslo', 4.0),
        ('cp_platano', 2.0),
        ('cp_leche_entera_1l', 2.0),
        ('cp_huevo_blanco_12', 1.0),
        ('cp_tomate', 1.0)
    ]
    
    # Escenario A: Compra en una sola parada (HEB)
    # Precios unitarios HEB:
    # Pollo HEB: $55.00/kg * 4 = $220.00
    # Plátano HEB: $21.22/kg * 2 = $42.44
    # Leche HEB: $36.90 * 2 = $73.80
    # Huevo HEB: $32.50 * 1 = $32.50
    # Tomate HEB: $20.00 * 1 = $20.00
    heb_subtotal = 220.00 + 42.44 + 73.80 + 32.50 + 20.00
    heb_distance_km = 4.2
    heb_time_min = 25
    heb_travel_cost = (heb_distance_km * 3.50) + (heb_time_min / 60.0 * 80.00)
    heb_total_cost = heb_subtotal + heb_travel_cost
    
    # Escenario B: División Óptima de Canasta (2 Paradas Físicas: El Más Pollo + Bodega Aurrera)
    # Pollo en El Más Pollo: $43.90/kg * 4 = $175.60
    # Plátano en Aurrera: $17.00/kg * 2 = $34.00
    # Leche en Aurrera/HEB: $36.90 * 2 = $73.80
    # Huevo en Aurrera: $26.00 * 1 = $26.00
    # Tomate en Aurrera: $12.90 * 1 = $12.90
    split_subtotal = 175.60 + 34.00 + 73.80 + 26.00 + 12.90
    split_distance_km = 7.5
    split_time_min = 45
    split_travel_cost = (split_distance_km * 3.50) + (split_time_min / 60.0 * 80.00)
    split_total_cost = split_subtotal + split_travel_cost
    
    gross_savings = heb_subtotal - split_subtotal
    net_savings = heb_total_cost - split_total_cost
    
    print(f"{'Métrica':<40} | {'Opción A: 1 Sola Tienda (HEB)':<25} | {'Opción B: Itinerario Óptimo (2 Tiendas)':<25}")
    print("-" * 100)
    print(f"{'Costo Total de Productos':<40} | ${heb_subtotal:>23.2f} | ${split_subtotal:>23.2f}")
    print(f"{'Distancia Total Recorrida':<40} | {heb_distance_km:>22.1f} km | {split_distance_km:>22.1f} km")
    print(f"{'Tiempo Total de Compra y Traslado':<40} | {heb_time_min:>20} min | {split_time_min:>20} min")
    print(f"{'Costo de Traslado (Gasolina + Tiempo)':<40} | ${heb_travel_cost:>23.2f} | ${split_travel_cost:>23.2f}")
    print(f"{'COSTO TOTAL REAL INTEGRADO':<40} | ${heb_total_cost:>23.2f} | ${split_total_cost:>23.2f}")
    print("-" * 100)
    print(f"💰 AHORRO BRUTO EN PRODUCTOS: ${gross_savings:.2f} MXN ({(gross_savings/heb_subtotal)*100:.1f}%)")
    print(f"✅ AHORRO NETO FINAL (Descontando traslado): ${net_savings:.2f} MXN")
    print("=" * 80)

    conn.close()

if __name__ == "__main__":
    run_analytics()
