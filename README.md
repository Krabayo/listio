# Listio 🛒⚡🚲

> **App Android Inteligente de Despensa, Auditoría de Carrito Pre-Pago, Logística en Bicicleta Eléctrica e Integración con Google AI Edge Gallery**

**Listio** (`com.krabayo.listio`) es una aplicación nativa para Android (Kotlin + Jetpack Compose + SQLite pre-cargada) diseñada para sugerir listas de compras e itinerarios óptimos a partir del historial de 75 recibos reales y los precios en tiendas físicas y en línea de preferencia en **San Nicolás de los Garza, N.L.** (`H-E-B`, `Soriana Híper`, `Bodega Aurrera`, `Sam's Club`, `El Más Pollo`, `Tres Horacios` y `OXXO`).

---

## 📱 Instalación en Teléfono Android

El paquete instalable compilado se encuentra en la raíz del repositorio:
- 📦 **[`Listio.apk`](Listio.apk)** — Descárgalo directamente a tu teléfono Android y ábrelo para instalar **Listio**.
- El código fuente completo del proyecto Android se encuentra en el directorio [`android-app/`](android-app/).

---

## 🎯 Funcionalidades Principales de la App

### 1. 📋 Lista Sugerida & Física de Canasta de Bicicleta Eléctrica (E-Bike)
- **Predicción de Agotamiento:** Calcula la velocidad de consumo diario de cada producto a partir de los 75 recibos históricos y prioriza los productos en estado `AGOTADO_URGENTE` y `STOCK_BAJO`.
- **Simulador Físico de Canasta E-Bike:** Dado que las compras se realizan en locales físicos y se transportan en la canasta de una bicicleta eléctrica, Listio monitorea en tiempo real:
  - **Peso acumulado vs. Límite seguro (`15.0 kg` máx.)**
  - **Volumen ocupado vs. Capacidad útil (`28.0 L` máx.)**
- **Guía de Acomodo en 3 Capas (Estiba Anti-Aplastamiento):**
  - 🧱 **`1_BASE_HEAVY` (Fondo rígido):** Leche, arroz, detergentes, bolsas de 2 kg congeladas, cortes de carne y botellas pesadas (baja el centro de gravedad de la bicicleta).
  - 📦 **`2_MIDDLE_FIRM` (Capa media):** Quesos, carnes frías, salchichas, vegetales firmes (zanahoria, pepino, calabaza) y latas.
  - 🥚 **`3_TOP_FRAGILE` (Cima delicada):** Plátano, aguacate, tomate, pan, tostadas, huevos y fresas.

### 2. 🗺️ Itinerario Óptimo E-Bike & Cadena de Frío
- **Asignación Multitienda Inteligente (*Split-Cart*):** Compara precios históricos de tickets físicos contra catálogos de tiendas en línea (`HEB Online`, `Soriana Digital`, `Despensa Bodega Aurrera`, `Sams.com.mx`).
- **Secuencia de Paradas por Sensibilidad Térmica:** Ordena el recorrido en bicicleta eléctrica visitando **primero** tiendas de abarrotes secos (`AMBIENT`) y dejando **al final** carnicerías, lácteos (`CHILLED`) y congelados (`FROZEN`) rumbo a casa para proteger la cadena de frío.
- **Descarga de Exceso de Peso:** Si un artículo pesado (ej. detergente líquido de 5 L o bultos de volumen) hace que la canasta supere los `15.0 kg` o `28.0 L`, sugiere enviarlo a pedido en línea o a un segundo viaje.

### 3. 📸 Cámara Pre-Pago (Auditoría de Carrito) + Ingesta Continua
- **Auditoría Antes de Pasar a Caja (`cart_snapshots`):** Permite tomar fotografías del carrito o canasta de compras **antes de pagar** para:
  - Estimar el **total acumulado en MXN** antes de llegar al cajero o AutoCobro.
  - Verificar si la carga actual en el carrito **cabe en la canasta de la bicicleta eléctrica** (`kg` y `L`) y cómo acomodarla por capas.
- **Crecimiento Continuo de la Base de Datos:** Permite fotografiar **nuevos recibos post-compra** (`receipt_uploads`) y **productos/precios en anaquel** (`product_photos`), insertando automáticamente nuevas observaciones de precio y actualizando el inventario del hogar.

### 4. ✨ Integración con Google AI Edge Gallery (`com.google.ai.edge.gallery`)
- **Envío Directo de Fotos (Android Intent `ACTION_SEND`):** Envía con un toque la fotografía del carrito pre-pago o de un ticket a **Google AI Edge Gallery** junto con el prompt estructurado de auditoría para análisis multimodal *on-device* (Gemma 3n / Gemini Nano).
- **Agent Skill Nativo (`SKILL.md`):** Incluye el skill modular [`edge-gallery-skill/SKILL.md`](edge-gallery-skill/SKILL.md) que puedes cargar en Edge Gallery mediante:
  - **URL Directa (GitHub Raw):** `https://raw.githubusercontent.com/Krabayo/listio/main/edge-gallery-skill/SKILL.md`
  - **Exportación/Compartir desde la pestaña Edge AI** dentro de la app Listio.
- **Deep Link Bidireccional (`listio://edge-sync`):** Permite importar el JSON devuelto por el modelo local de Edge Gallery para registrar automáticamente el carrito o recibo en SQLite.

---

## 📂 Estructura del Repositorio

- **[`Listio.apk`](Listio.apk)**: Aplicación Android compilada e instalable.
- **[`android-app/`](android-app/)**: Proyecto Android nativo (Kotlin, Jetpack Compose, Material 3, SQLite Helper con base de datos pre-poblada en `assets/listio.db`).
- **[`edge-gallery-skill/SKILL.md`](edge-gallery-skill/SKILL.md)**: Definición del Agent Skill oficial para integrar **Google AI Edge Gallery** con Listio.
- **[`schema.sql`](schema.sql)**: Esquema relacional completo (compatible con PostgreSQL y SQLite) incluyendo tablas de física de canasta E-Bike, auditoría de carritos pre-pago (`cart_snapshots`) y fotos de productos (`product_photos`).
- **[`seed_data.py`](seed_data.py)**: Script que genera y puebla [`listio.db`](listio.db) con los datos reales extraídos de los 75 recibos, pesos, volúmenes, fragilidad, sensibilidad térmica y carritos de ejemplo.
- **[`query_demo.py`](query_demo.py)**: Demostración en consola de las vistas analíticas y el optimizador de compras.
- **[`DOCS_DATABASE_DESIGN.md`](DOCS_DATABASE_DESIGN.md)**: Documentación exhaustiva de la extracción de los 75 recibos y arquitectura de datos.
- **[`20261108_2-001.pdf`](20261108_2-001.pdf) & [`20261108_2-002.pdf`](20261108_2-002.pdf)**: Lotes de recibos físicos digitalizados.

---

## 🛠️ Compilación desde Código Fuente

```bash
# 1. Regenerar la base de datos semilla SQLite (opcional, ya incluida en assets)
python seed_data.py

# 2. Compilar el APK de Android
cd android-app
./gradlew assembleDebug
```
