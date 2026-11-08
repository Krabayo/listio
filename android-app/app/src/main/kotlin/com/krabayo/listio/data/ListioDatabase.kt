package com.krabayo.listio.data

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.UUID

data class ShoppingItemUi(
    val listItemId: String,
    val productId: String,
    val productName: String,
    val quantity: Double,
    val unit: String,
    val urgencyLevel: String,
    val assignedChainName: String,
    val assignedChainCode: String,
    val estimatedCost: Double,
    val singleStoreCost: Double,
    val totalWeightKg: Double,
    val totalVolumeL: Double,
    val fragilityTier: String,
    val thermalSensitivity: String,
    val isChecked: Boolean = false
)

data class StoreStopUi(
    val stopOrder: Int,
    val storeId: String,
    val chainName: String,
    val branchName: String,
    val address: String,
    val distanceKm: Double,
    val latitude: Double,
    val longitude: Double,
    val stopRole: String,
    val items: List<ShoppingItemUi>,
    val subtotalMx: Double,
    val addedWeightKg: Double,
    val addedVolumeL: Double
)

data class ProductCatalogUi(
    val productId: String,
    val canonicalName: String,
    val standardUnit: String,
    val unitWeightKg: Double,
    val unitVolumeL: Double,
    val fragilityTier: String,
    val thermalSensitivity: String,
    val pricesByChain: List<Pair<String, Double>>,
    val reorderDays: Double,
    val depletionDate: String
)

data class CartSnapshotUi(
    val snapshotId: String,
    val storeName: String,
    val photoPath: String?,
    val capturedAt: String,
    val itemsCount: Int,
    val estimatedSubtotal: Double,
    val totalWeightKg: Double,
    val totalVolumeL: Double,
    val capacityStatus: String,
    val packingAdvice: String
)

data class ReceiptHistoryUi(
    val receiptId: String,
    val chainName: String,
    val branchName: String,
    val ticketNumber: String,
    val timestamp: String,
    val totalAmount: Double,
    val itemsCount: Int,
    val tripWeightKg: Double,
    val tripVolumeL: Double
)

data class ProductPhotoUi(
    val photoId: String,
    val productName: String,
    val chainName: String,
    val imagePath: String?,
    val observedPrice: Double,
    val capturedAt: String,
    val notes: String
)

class ListioDatabase(private val context: Context) {

    private val dbFile: File
        get() = context.getDatabasePath("listio.db")

    init {
        ensureSeedDatabaseCopied()
    }

    private fun ensureSeedDatabaseCopied() {
        if (!dbFile.exists() || dbFile.length() == 0L) {
            dbFile.parentFile?.mkdirs()
            context.assets.open("listio.db").use { input ->
                FileOutputStream(dbFile).use { output ->
                    input.copyTo(output)
                }
            }
        }
        // Asegurar columna is_checked en shopping_list_items si no existe
        openDb().use { db ->
            try {
                db.execSQL("ALTER TABLE shopping_list_items ADD COLUMN is_checked INTEGER DEFAULT 0")
            } catch (_: Exception) {
                // La columna ya existe
            }
        }
    }

    private fun openDb(): SQLiteDatabase {
        return SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READWRITE)
    }

    fun getShoppingListItems(): List<ShoppingItemUi> {
        val result = mutableListOf<ShoppingItemUi>()
        openDb().use { db ->
            val sql = """
                SELECT 
                    sli.list_item_id,
                    sli.product_id,
                    cp.canonical_name,
                    sli.suggested_quantity,
                    sli.unit,
                    sli.urgency_level,
                    rc.commercial_name,
                    rc.code,
                    sli.estimated_item_cost,
                    sli.estimated_weight_kg,
                    sli.estimated_volume_l,
                    cp.fragility_tier,
                    cp.thermal_sensitivity,
                    COALESCE(sli.is_checked, 0) as is_checked,
                    COALESCE((
                        SELECT MAX(po.normalized_price_per_std_unit)
                        FROM price_observations po
                        WHERE po.product_id = cp.product_id
                    ), sli.estimated_item_cost / sli.suggested_quantity * 1.22) as max_unit_price
                FROM shopping_list_items sli
                JOIN canonical_products cp ON sli.product_id = cp.product_id
                LEFT JOIN retail_chains rc ON sli.allocated_chain_id = rc.chain_id
                ORDER BY 
                    CASE sli.urgency_level 
                        WHEN 'DEPLETED' THEN 1 
                        WHEN 'LOW_STOCK' THEN 2 
                        ELSE 3 
                    END,
                    cp.canonical_name ASC
            """.trimIndent()
            db.rawQuery(sql, null).use { c ->
                while (c.moveToNext()) {
                    val qty = c.getDouble(3)
                    val optCost = c.getDouble(8)
                    val maxUnit = c.getDouble(14)
                    val baselineCost = maxOf(optCost * 1.15, maxUnit * qty)
                    result.add(
                        ShoppingItemUi(
                            listItemId = c.getString(0),
                            productId = c.getString(1),
                            productName = c.getString(2),
                            quantity = qty,
                            unit = c.getString(4),
                            urgencyLevel = c.getString(5),
                            assignedChainName = c.getString(6) ?: "Bodega Aurrera",
                            assignedChainCode = c.getString(7) ?: "AURRERA",
                            estimatedCost = optCost,
                            singleStoreCost = baselineCost,
                            totalWeightKg = c.getDouble(9),
                            totalVolumeL = c.getDouble(10),
                            fragilityTier = c.getString(11) ?: "2_MIDDLE_FIRM",
                            thermalSensitivity = c.getString(12) ?: "AMBIENT",
                            isChecked = c.getInt(13) == 1
                        )
                    )
                }
            }
        }
        return result
    }

    fun toggleShoppingItemChecked(listItemId: String, checked: Boolean) {
        openDb().use { db ->
            val cv = ContentValues().apply {
                put("is_checked", if (checked) 1 else 0)
            }
            db.update("shopping_list_items", cv, "list_item_id = ?", arrayOf(listItemId))
        }
    }

    fun addProductToShoppingList(productId: String, quantity: Double) {
        openDb().use { db ->
            val cursor = db.rawQuery(
                """
                SELECT cp.standard_unit, cp.unit_weight_kg, cp.unit_volume_liters,
                       COALESCE(po.chain_id, 'ch_aurrera'),
                       COALESCE(MIN(po.normalized_price_per_std_unit), 30.0)
                FROM canonical_products cp
                LEFT JOIN price_observations po ON cp.product_id = po.product_id
                WHERE cp.product_id = ?
                GROUP BY cp.product_id
                """.trimIndent(),
                arrayOf(productId)
            )
            if (cursor.moveToFirst()) {
                val unit = cursor.getString(0)
                val unitWeight = cursor.getDouble(1)
                val unitVol = cursor.getDouble(2)
                val chainId = cursor.getString(3)
                val unitPrice = cursor.getDouble(4)
                val cv = ContentValues().apply {
                    put("list_item_id", "sli_" + UUID.randomUUID().toString().take(8))
                    put("list_id", "lst_sug_01")
                    put("product_id", productId)
                    put("suggested_quantity", quantity)
                    put("unit", unit)
                    put("urgency_level", "LOW_STOCK")
                    put("allocated_chain_id", chainId)
                    put("allocated_channel", "PHYSICAL")
                    put("estimated_item_cost", unitPrice * quantity)
                    put("estimated_weight_kg", unitWeight * quantity)
                    put("estimated_volume_l", unitVol * quantity)
                    put("is_checked", 0)
                }
                db.insert("shopping_list_items", null, cv)
            }
            cursor.close()
        }
    }

    fun getOptimalEbikeItinerary(): List<StoreStopUi> {
        val items = getShoppingListItems()
        val grouped = items.groupBy { it.assignedChainCode }
        val stops = mutableListOf<StoreStopUi>()

        openDb().use { db ->
            // Orden táctico para bicicleta eléctrica:
            // 1. AURRERA / SAMS / SORIANA (Secos, abarrotes pesados y básicos al fondo de la canasta)
            // 2. HEB (Lácteos, panadería y frescos)
            // 3. EL_MAS_POLLO / TRES_HORACIOS (Carnes frescas a <0.5 km de casa para cuidar cadena de frío)
            val priorityOrder = listOf("AURRERA", "SAMS", "SORIANA", "HEB", "OXXO", "EL_MAS_POLLO", "TRES_HORACIOS")
            var orderCounter = 1
            for (code in priorityOrder) {
                val stopItems = grouped[code] ?: continue
                val storeCursor = db.rawQuery(
                    """
                    SELECT ps.store_id, rc.commercial_name, ps.branch_name, ps.street_address,
                           ps.distance_from_home_km, ps.latitude, ps.longitude
                    FROM physical_stores ps
                    JOIN retail_chains rc ON ps.chain_id = rc.chain_id
                    WHERE rc.code = ?
                    ORDER BY ps.distance_from_home_km ASC
                    LIMIT 1
                    """.trimIndent(),
                    arrayOf(code)
                )
                if (storeCursor.moveToFirst()) {
                    val roleDesc = when (code) {
                        "AURRERA", "SAMS" -> "Parada Inicial: Abarrotes pesados y básicos al fondo de canasta"
                        "HEB", "SORIANA" -> "Parada Media: Lácteos, tortillas y perecederos ligeros"
                        "EL_MAS_POLLO", "TRES_HORACIOS" -> "Última Parada (0.45 km de casa): Pollo y carne fresca (Cadena de Frío)"
                        else -> "Parada Rápida de Conveniencia"
                    }
                    stops.add(
                        StoreStopUi(
                            stopOrder = orderCounter++,
                            storeId = storeCursor.getString(0),
                            chainName = storeCursor.getString(1),
                            branchName = storeCursor.getString(2),
                            address = storeCursor.getString(3),
                            distanceKm = storeCursor.getDouble(4),
                            latitude = storeCursor.getDouble(5),
                            longitude = storeCursor.getDouble(6),
                            stopRole = roleDesc,
                            items = stopItems,
                            subtotalMx = stopItems.sumOf { it.estimatedCost },
                            addedWeightKg = stopItems.sumOf { it.totalWeightKg },
                            addedVolumeL = stopItems.sumOf { it.totalVolumeL }
                        )
                    )
                }
                storeCursor.close()
            }
        }
        return stops
    }

    fun getProductCatalogWithPrices(): List<ProductCatalogUi> {
        val list = mutableListOf<ProductCatalogUi>()
        openDb().use { db ->
            val pricesMap = mutableMapOf<String, MutableList<Pair<String, Double>>>()
            db.rawQuery(
                """
                SELECT po.product_id, rc.commercial_name, po.normalized_price_per_std_unit
                FROM price_observations po
                JOIN retail_chains rc ON po.chain_id = rc.chain_id
                ORDER BY po.normalized_price_per_std_unit ASC
                """.trimIndent(),
                null
            ).use { pc ->
                while (pc.moveToNext()) {
                    val pid = pc.getString(0)
                    val cname = pc.getString(1)
                    val price = pc.getDouble(2)
                    pricesMap.getOrPut(pid) { mutableListOf() }.add(cname to price)
                }
            }

            db.rawQuery(
                """
                SELECT cp.product_id, cp.canonical_name, cp.standard_unit,
                       cp.unit_weight_kg, cp.unit_volume_liters, cp.fragility_tier,
                       cp.thermal_sensitivity,
                       COALESCE(upc.avg_reorder_interval_days, cp.estimated_shelf_life_days),
                       COALESCE(upc.estimated_depletion_date, 'En inventario')
                FROM canonical_products cp
                LEFT JOIN user_product_consumption upc ON cp.product_id = upc.product_id
                ORDER BY cp.canonical_name ASC
                """.trimIndent(),
                null
            ).use { c ->
                while (c.moveToNext()) {
                    val pid = c.getString(0)
                    list.add(
                        ProductCatalogUi(
                            productId = pid,
                            canonicalName = c.getString(1),
                            standardUnit = c.getString(2),
                            unitWeightKg = c.getDouble(3),
                            unitVolumeL = c.getDouble(4),
                            fragilityTier = c.getString(5) ?: "2_MIDDLE_FIRM",
                            thermalSensitivity = c.getString(6) ?: "AMBIENT",
                            pricesByChain = pricesMap[pid] ?: listOf("Referencia Local" to 35.0),
                            reorderDays = c.getDouble(7),
                            depletionDate = c.getString(8)
                        )
                    )
                }
            }
        }
        return list
    }

    fun getCartSnapshots(): List<CartSnapshotUi> {
        val list = mutableListOf<CartSnapshotUi>()
        openDb().use { db ->
            db.rawQuery(
                """
                SELECT cs.snapshot_id, COALESCE(ps.branch_name, 'H-E-B San Nicolás'),
                       cs.photo_uri, cs.captured_at, cs.detected_items_count,
                       cs.estimated_subtotal, cs.estimated_total_weight_kg,
                       cs.estimated_total_volume_liters, cs.ebike_capacity_status,
                       cs.ai_packing_advice
                FROM cart_snapshots cs
                LEFT JOIN physical_stores ps ON cs.store_id = ps.store_id
                ORDER BY cs.captured_at DESC
                """.trimIndent(),
                null
            ).use { c ->
                while (c.moveToNext()) {
                    list.add(
                        CartSnapshotUi(
                            snapshotId = c.getString(0),
                            storeName = c.getString(1),
                            photoPath = c.getString(2),
                            capturedAt = c.getString(3),
                            itemsCount = c.getInt(4),
                            estimatedSubtotal = c.getDouble(5),
                            totalWeightKg = c.getDouble(6),
                            totalVolumeL = c.getDouble(7),
                            capacityStatus = c.getString(8),
                            packingAdvice = c.getString(9)
                        )
                    )
                }
            }
        }
        return list
    }

    fun savePreCheckoutCartSnapshot(
        storeName: String,
        photoPath: String?,
        selectedProducts: List<Pair<ProductCatalogUi, Double>>
    ): CartSnapshotUi {
        val now = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(Date())
        val snapId = "snap_" + UUID.randomUUID().toString().take(8)
        val totalSubtotal = selectedProducts.sumOf { (prod, qty) ->
            val unitPrice = prod.pricesByChain.firstOrNull()?.second ?: 30.0
            unitPrice * qty
        }
        val totalWeight = selectedProducts.sumOf { (prod, qty) -> prod.unitWeightKg * qty }
        val totalVolume = selectedProducts.sumOf { (prod, qty) -> prod.unitVolumeL * qty }

        val status = when {
            totalWeight > 15.0 || totalVolume > 28.0 -> "OVERLOAD_SPLIT_NEEDED"
            totalWeight > 12.0 || totalVolume > 22.0 -> "WARNING_NEAR_LIMIT"
            else -> "OK"
        }

        val baseLayer = selectedProducts.filter { it.first.fragilityTier == "1_BASE_HEAVY" }
            .joinToString(", ") { "${it.second}x ${it.first.canonicalName.take(18)}" }
            .ifEmpty { "Lácteos / Latas" }
        val midLayer = selectedProducts.filter { it.first.fragilityTier == "2_MIDDLE_FIRM" }
            .joinToString(", ") { "${it.second}x ${it.first.canonicalName.take(18)}" }
            .ifEmpty { "Tortillas / Tubérculos" }
        val topLayer = selectedProducts.filter { it.first.fragilityTier == "3_TOP_FRAGILE" }
            .joinToString(", ") { "${it.second}x ${it.first.canonicalName.take(18)}" }
            .ifEmpty { "Huevos / Plátano / Pan" }

        val advice = "Fondo (Rígido): $baseLayer | Medio: $midLayer | Cima (Frágil): $topLayer"

        openDb().use { db ->
            val cv = ContentValues().apply {
                put("snapshot_id", snapId)
                put("user_id", "usr_01")
                put("store_id", "st_heb_sn")
                put("photo_uri", photoPath ?: "")
                put("captured_at", now)
                put("detected_items_count", selectedProducts.size)
                put("estimated_subtotal", totalSubtotal)
                put("estimated_total_weight_kg", totalWeight)
                put("estimated_total_volume_liters", totalVolume)
                put("ebike_capacity_status", status)
                put("ai_packing_advice", advice)
            }
            db.insert("cart_snapshots", null, cv)
        }

        return CartSnapshotUi(
            snapshotId = snapId,
            storeName = storeName,
            photoPath = photoPath,
            capturedAt = now,
            itemsCount = selectedProducts.size,
            estimatedSubtotal = totalSubtotal,
            totalWeightKg = totalWeight,
            totalVolumeL = totalVolume,
            capacityStatus = status,
            packingAdvice = advice
        )
    }

    fun getReceiptsHistory(): List<ReceiptHistoryUi> {
        val list = mutableListOf<ReceiptHistoryUi>()
        openDb().use { db ->
            db.rawQuery(
                """
                SELECT r.receipt_id, rc.commercial_name, COALESCE(ps.branch_name, rc.commercial_name),
                       r.ticket_number, r.transaction_timestamp, r.total_amount,
                       r.total_items_count, r.estimated_trip_weight_kg, r.estimated_trip_volume_l
                FROM receipts r
                JOIN retail_chains rc ON r.chain_id = rc.chain_id
                LEFT JOIN physical_stores ps ON r.store_id = ps.store_id
                ORDER BY r.transaction_timestamp DESC
                """.trimIndent(),
                null
            ).use { c ->
                while (c.moveToNext()) {
                    list.add(
                        ReceiptHistoryUi(
                            receiptId = c.getString(0),
                            chainName = c.getString(1),
                            branchName = c.getString(2),
                            ticketNumber = c.getString(3) ?: "S/N",
                            timestamp = c.getString(4),
                            totalAmount = c.getDouble(5),
                            itemsCount = c.getInt(6),
                            tripWeightKg = c.getDouble(7),
                            tripVolumeL = c.getDouble(8)
                        )
                    )
                }
            }
        }
        return list
    }

    fun saveNewReceiptFromPhoto(
        chainCode: String,
        ticketNumber: String,
        totalAmount: Double,
        itemsCount: Int,
        estimatedWeightKg: Double,
        estimatedVolumeL: Double
    ) {
        val now = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(Date())
        val chainId = when (chainCode) {
            "HEB" -> "ch_heb"
            "SORIANA" -> "ch_soriana"
            "AURRERA" -> "ch_aurrera"
            "SAMS" -> "ch_sams"
            "EL_MAS_POLLO" -> "ch_marlan"
            "TRES_HORACIOS" -> "ch_horacios"
            else -> "ch_oxxo"
        }
        val storeId = when (chainCode) {
            "HEB" -> "st_heb_sn"
            "SORIANA" -> "st_sor_sn"
            "AURRERA" -> "st_aur_stdgo"
            "SAMS" -> "st_sams_uni"
            "EL_MAS_POLLO" -> "st_mar_sn"
            "TRES_HORACIOS" -> "st_horacios"
            else -> "st_oxxo_pino"
        }

        openDb().use { db ->
            val cv = ContentValues().apply {
                put("receipt_id", "rc_" + UUID.randomUUID().toString().take(8))
                put("user_id", "usr_01")
                put("store_id", storeId)
                put("chain_id", chainId)
                put("ticket_number", ticketNumber.ifBlank { "FOTO-" + System.currentTimeMillis().toString().takeLast(6) })
                put("transaction_timestamp", now)
                put("cashier_or_register", "Captura Cámara Android")
                put("subtotal_amount", totalAmount)
                put("discounts_total", 0.0)
                put("tax_iva_amount", 0.0)
                put("tax_ieps_amount", 0.0)
                put("rounding_or_donation_amount", 0.0)
                put("total_amount", totalAmount)
                put("total_items_count", itemsCount)
                put("estimated_trip_weight_kg", estimatedWeightKg)
                put("estimated_trip_volume_l", estimatedVolumeL)
                put("is_mathematically_balanced", 1)
            }
            db.insert("receipts", null, cv)
        }
    }

    fun getProductPhotos(): List<ProductPhotoUi> {
        val list = mutableListOf<ProductPhotoUi>()
        openDb().use { db ->
            db.rawQuery(
                """
                SELECT pp.photo_id, COALESCE(cp.canonical_name, pp.notes),
                       COALESCE(rc.commercial_name, 'Tienda Local'),
                       pp.image_uri, pp.observed_price, pp.captured_at, pp.notes
                FROM product_photos pp
                LEFT JOIN canonical_products cp ON pp.product_id = cp.product_id
                LEFT JOIN retail_chains rc ON pp.chain_id = rc.chain_id
                ORDER BY pp.captured_at DESC
                """.trimIndent(),
                null
            ).use { c ->
                while (c.moveToNext()) {
                    list.add(
                        ProductPhotoUi(
                            photoId = c.getString(0),
                            productName = c.getString(1) ?: "Producto Nuevo",
                            chainName = c.getString(2),
                            imagePath = c.getString(3),
                            observedPrice = c.getDouble(4),
                            capturedAt = c.getString(5),
                            notes = c.getString(6) ?: ""
                        )
                    )
                }
            }
        }
        return list
    }

    fun saveNewProductPhoto(
        productName: String,
        chainCode: String,
        observedPrice: Double,
        weightKg: Double,
        volumeL: Double,
        fragilityTier: String,
        imagePath: String?
    ) {
        val now = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(Date())
        val prodId = "cp_" + UUID.randomUUID().toString().take(8)
        val chainId = when (chainCode) {
            "HEB" -> "ch_heb"
            "SORIANA" -> "ch_soriana"
            "AURRERA" -> "ch_aurrera"
            "SAMS" -> "ch_sams"
            "EL_MAS_POLLO" -> "ch_marlan"
            "TRES_HORACIOS" -> "ch_horacios"
            else -> "ch_oxxo"
        }

        openDb().use { db ->
            val cvProd = ContentValues().apply {
                put("product_id", prodId)
                put("category_id", "cat_abarrotes")
                put("canonical_name", productName)
                put("standard_unit", "piece")
                put("brand", "Capturado en Tienda")
                put("estimated_shelf_life_days", 14)
                put("is_perishable", 1)
                put("storage_type", "ROOM_TEMP")
                put("unit_weight_kg", weightKg)
                put("unit_volume_liters", volumeL)
                put("fragility_tier", fragilityTier)
                put("thermal_sensitivity", "AMBIENT")
            }
            db.insert("canonical_products", null, cvProd)

            val cvPrice = ContentValues().apply {
                put("observation_id", "po_" + UUID.randomUUID().toString().take(8))
                put("product_id", prodId)
                put("chain_id", chainId)
                put("price_channel", "IN_STORE_PHOTO")
                put("price_date", now.take(10))
                put("regular_unit_price", observedPrice)
                put("promo_unit_price", observedPrice)
                put("is_on_promotion", 0)
                put("normalized_price_per_std_unit", observedPrice)
            }
            db.insert("price_observations", null, cvPrice)

            val cvPhoto = ContentValues().apply {
                put("photo_id", "pho_" + UUID.randomUUID().toString().take(8))
                put("product_id", prodId)
                put("chain_id", chainId)
                put("image_uri", imagePath ?: "")
                put("observed_price", observedPrice)
                put("captured_at", now)
                put("notes", "$productName ($weightKg kg / $volumeL L / $fragilityTier)")
            }
            db.insert("product_photos", null, cvPhoto)
        }
    }
}
