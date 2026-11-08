# Listio 🛒

> **Gestor Inteligente de Despensa, Ingesta de Recibos y Optimización de Itinerarios de Compra**

Listio es una plataforma diseñada para automatizar la gestión de compras del hogar a partir de la digitalización de tickets físicos (vía visión por computadora) y la sincronización con tiendas en línea de preferencia en México (H-E-B, Soriana, Bodega Aurrera, Sam's Club, entre otras).

---

## 🎯 Objetivos del Proyecto

1. **Digitalización e Ingesta de Recibos Futuros:** Extracción estructurada de tickets físicos con soporte para productos por peso (KG), promociones (2x1, 3x20, cuponeras), pagos divididos (*split payment*) y donaciones.
2. **Consumo Predictivo e Inventario Virtual:** Cálculo automático de la velocidad de consumo de cada producto para anticipar el agotamiento y generar listas de compras antes de que los productos se terminen.
3. **Inteligencia de Precios Omnicanal:** Monitoreo y normalización de precios físicos y de tiendas en línea en unidades estándar (\$/kg, \$/L, \$/pieza).
4. **Optimizador de Itinerarios (*Split-Cart Optimizer*):** Sugerencia de rutas eficientes dividiendo la canasta de compras entre tiendas físicas y pedidos en línea, maximizando el ahorro neto tras descontar el combustible y tiempo invertido.

---

## 📂 Estructura del Repositorio

- **`schema.sql`**: Esquema DDL en PostgreSQL con extensiones `uuid-ossp` y `pg_trgm`, llaves foráneas, índices de búsqueda difusa y vistas analíticas (`v_latest_product_prices`, `v_inventory_replenishment_needed`).
- **`seed_data.py`**: Generador y poblador de la base de datos local SQLite (`listio.db`) con las cadenas comerciales, catálogo maestro y precios reales extraídos de 75 recibos.
- **`query_demo.py`**: Demostración práctica de las consultas de reposición de inventario, comparativa multitienda y simulación del algoritmo de itinerario óptimo.
- **`listio.db`**: Base de datos SQLite inicializada y lista para pruebas locales.
- **`20261108_2-001.pdf` & `20261108_2-002.pdf`**: Recibos físicos procesados para el diseño del modelo.

---

## 🚀 Inicio Rápido

### Requisitos
- Python 3.10+
- `pandas`
- SQLite3 (incluido en Python) o PostgreSQL 14+

### Ejecución de Pruebas y Analítica

```bash
# 1. Regenerar la base de datos con datos semilla
python seed_data.py

# 2. Ejecutar la analítica de reposición e itinerarios
python query_demo.py
```

---

## 🗺️ Cadenas Comerciales Soportadas

- **H-E-B:** Frescos, lácteos, marcas propias y café especial.
- **Soriana Híper:** Carnicería en días de oferta, abarrotes y programa Soriana YA.
- **Bodega Aurrera:** Abarrotes básicos y productos de limpieza de alta economía.
- **Sam's Club:** Compras de volumen (bolsas de 2kg de congelados, quesos, membresía Plus).
- **El Más Pollo (Avipecuaria Marlan):** Carnicería de ave local con precio por kilo económico.
- **Tres Horacios:** Boutique local de carnes preparadas y quesos artesanales.
- **OXXO:** Compras de conveniencia inmediata.
