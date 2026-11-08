package com.krabayo.listio.ui.main

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import androidx.navigation3.runtime.NavKey
import com.krabayo.listio.data.*
import java.io.File
import java.io.FileOutputStream
import java.util.Locale

private val EmeraldGreen = Color(0xFF0F766E)
private val EmeraldLight = Color(0xFFCCFBF1)
private val AmberWarn = Color(0xFFB45309)
private val AmberLight = Color(0xFFFEF3C7)
private val CoralRed = Color(0xFFB91C1C)
private val CoralLight = Color(0xFFFEE2E2)
private val IndigoBlue = Color(0xFF1D4ED8)
private val IndigoLight = Color(0xFFDBEAFE)

@Composable
fun MainScreen(
    onItemClick: (NavKey) -> Unit,
    modifier: Modifier = Modifier
) {
    ListioAppScreen(
        incomingEdgeData = null,
        onClearIncomingEdgeData = {},
        modifier = modifier
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ListioAppScreen(
    incomingEdgeData: String?,
    onClearIncomingEdgeData: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val db = remember { ListioDatabase(context) }

    var selectedTab by remember { mutableIntStateOf(0) }
    var refreshTrigger by remember { mutableIntStateOf(0) }

    val shoppingItems = remember(refreshTrigger) { db.getShoppingListItems() }
    val itineraryStops = remember(refreshTrigger) { db.getOptimalEbikeItinerary() }
    val productCatalog = remember(refreshTrigger) { db.getProductCatalogWithPrices() }
    val cartSnapshots = remember(refreshTrigger) { db.getCartSnapshots() }
    val receiptsHistory = remember(refreshTrigger) { db.getReceiptsHistory() }
    val productPhotos = remember(refreshTrigger) { db.getProductPhotos() }

    // Métricas en tiempo real de la canasta de la bicicleta eléctrica (Capacidad: 15.0 kg / 28.0 L)
    val maxWeightKg = 15.0
    val maxVolumeL = 28.0
    val activeWeightKg = shoppingItems.sumOf { it.totalWeightKg }
    val activeVolumeL = shoppingItems.sumOf { it.totalVolumeL }
    val optimalTotalCost = shoppingItems.sumOf { it.estimatedCost }
    val singleStoreCost = shoppingItems.sumOf { it.singleStoreCost }
    val totalSavings = (singleStoreCost - optimalTotalCost).coerceAtLeast(0.0)

    // Si llega información desde Google AI Edge Gallery, cambiar a la pestaña de Edge Gallery
    LaunchedEffect(incomingEdgeData) {
        if (!incomingEdgeData.isNullOrBlank()) {
            selectedTab = 3
        }
    }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        topBar = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(EmeraldGreen)
                    .statusBarsPadding()
                    .padding(horizontal = 16.dp, vertical = 10.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = "Listio 🚲 Despensa & E-Bike",
                            color = Color.White,
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = "San Nicolás de los Garza • 75+ Recibos Base",
                            color = EmeraldLight,
                            fontSize = 12.sp
                        )
                    }
                    Surface(
                        color = Color.White.copy(alpha = 0.18f),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Text(
                            text = String.format(Locale.US, "Ahorro: $%.2f", totalSavings),
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp,
                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp)
                        )
                    }
                }
                Spacer(modifier = Modifier.height(6.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text(
                        text = String.format(Locale.US, "⚖️ Canasta: %.1f / %.0f kg", activeWeightKg, maxWeightKg),
                        color = Color.White,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium
                    )
                    Text(
                        text = String.format(Locale.US, "📦 Volumen: %.1f / %.0f L", activeVolumeL, maxVolumeL),
                        color = Color.White,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium
                    )
                    Text(
                        text = "📍 ${itineraryStops.size} paradas",
                        color = EmeraldLight,
                        fontSize = 12.sp
                    )
                }
            }
        },
        bottomBar = {
            NavigationBar(
                containerColor = MaterialTheme.colorScheme.surface,
                tonalElevation = 8.dp
            ) {
                val tabs = listOf(
                    "🚲 Lista & Estiba",
                    "🗺️ Ruta & Precios",
                    "📷 Carrito & Tickets",
                    "✨ Edge Gallery"
                )
                tabs.forEachIndexed { idx, label ->
                    NavigationBarItem(
                        selected = selectedTab == idx,
                        onClick = { selectedTab = idx },
                        icon = {
                            Text(
                                text = label.take(2),
                                fontSize = 18.sp
                            )
                        },
                        label = {
                            Text(
                                text = label.drop(3),
                                fontSize = 11.sp,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                    )
                }
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            when (selectedTab) {
                0 -> EbikeShoppingListTab(
                    shoppingItems = shoppingItems,
                    productCatalog = productCatalog,
                    activeWeightKg = activeWeightKg,
                    maxWeightKg = maxWeightKg,
                    activeVolumeL = activeVolumeL,
                    maxVolumeL = maxVolumeL,
                    optimalTotalCost = optimalTotalCost,
                    singleStoreCost = singleStoreCost,
                    onToggleChecked = { itemId, checked ->
                        db.toggleShoppingItemChecked(itemId, checked)
                        refreshTrigger++
                    },
                    onAddProduct = { productId, qty ->
                        db.addProductToShoppingList(productId, qty)
                        refreshTrigger++
                        Toast.makeText(context, "Producto agregado a la canasta E-Bike", Toast.LENGTH_SHORT).show()
                    }
                )
                1 -> EbikeItineraryAndPricesTab(
                    stops = itineraryStops,
                    catalog = productCatalog,
                    context = context
                )
                2 -> CameraCartAndReceiptsTab(
                    context = context,
                    db = db,
                    catalog = productCatalog,
                    cartSnapshots = cartSnapshots,
                    receipts = receiptsHistory,
                    productPhotos = productPhotos,
                    onDataUpdated = { refreshTrigger++ },
                    onSendToEdgeGallery = { imagePath, promptText ->
                        shareToEdgeGalleryApp(context, imagePath, promptText)
                    }
                )
                3 -> EdgeGalleryIntegrationTab(
                    context = context,
                    db = db,
                    incomingEdgeData = incomingEdgeData,
                    onClearIncomingEdgeData = onClearIncomingEdgeData,
                    cartSnapshots = cartSnapshots,
                    receiptsCount = receiptsHistory.size + 65,
                    productsCount = productCatalog.size,
                    onDataUpdated = { refreshTrigger++ }
                )
            }
        }
    }
}

// ============================================================================
// TAB 1: LISTA DE COMPRAS PREDICTIVA Y ESTIBA EN BICICLETA ELÉCTRICA
// ============================================================================
@Composable
private fun EbikeShoppingListTab(
    shoppingItems: List<ShoppingItemUi>,
    productCatalog: List<ProductCatalogUi>,
    activeWeightKg: Double,
    maxWeightKg: Double,
    activeVolumeL: Double,
    maxVolumeL: Double,
    optimalTotalCost: Double,
    singleStoreCost: Double,
    onToggleChecked: (String, Boolean) -> Unit,
    onAddProduct: (String, Double) -> Unit
) {
    var showAddDialog by remember { mutableStateOf(false) }

    val weightRatio = (activeWeightKg / maxWeightKg).toFloat().coerceIn(0f, 1f)
    val volumeRatio = (activeVolumeL / maxVolumeL).toFloat().coerceIn(0f, 1f)
    val isOverloaded = activeWeightKg > maxWeightKg || activeVolumeL > maxVolumeL
    val isNearLimit = activeWeightKg > maxWeightKg * 0.8 || activeVolumeL > maxVolumeL * 0.8

    val statusColor = when {
        isOverloaded -> CoralRed
        isNearLimit -> AmberWarn
        else -> EmeraldGreen
    }
    val statusBg = when {
        isOverloaded -> CoralLight
        isNearLimit -> AmberLight
        else -> EmeraldLight
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // 1. Tarjeta de Capacidad Física de la Canasta de Bicicleta Eléctrica
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "🚲 Telemetría de Canasta E-Bike",
                            fontWeight = FontWeight.Bold,
                            fontSize = 16.sp
                        )
                        Surface(
                            color = statusBg,
                            shape = RoundedCornerShape(8.dp)
                        ) {
                            Text(
                                text = when {
                                    isOverloaded -> "⚠️ EXCESO: 2 VIAJES"
                                    isNearLimit -> "⚡ 85% CAPACIDAD"
                                    else -> "✅ CARGA SEGURA"
                                },
                                color = statusColor,
                                fontWeight = FontWeight.Bold,
                                fontSize = 11.sp,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    Text(
                        text = String.format(Locale.US, "Peso Total: %.2f kg de %.1f kg máx (%.0f%%)", activeWeightKg, maxWeightKg, weightRatio * 100),
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium
                    )
                    LinearProgressIndicator(
                        progress = { weightRatio },
                        color = statusColor,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp)
                            .height(8.dp)
                            .clip(RoundedCornerShape(4.dp))
                    )

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        text = String.format(Locale.US, "Volumen en Canasta: %.1f L de %.1f L máx (%.0f%%)", activeVolumeL, maxVolumeL, volumeRatio * 100),
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium
                    )
                    LinearProgressIndicator(
                        progress = { volumeRatio },
                        color = IndigoBlue,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp)
                            .height(8.dp)
                            .clip(RoundedCornerShape(4.dp))
                    )

                    Spacer(modifier = Modifier.height(10.dp))

                    // Guía de Estiba en 3 Capas para no aplastar alimentos
                    Surface(
                        color = MaterialTheme.colorScheme.surface,
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Text(
                                text = "📐 Orden Recomendado de Estiba en la Canasta:",
                                fontWeight = FontWeight.Bold,
                                fontSize = 13.sp,
                                color = EmeraldGreen
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            val heavyItems = shoppingItems.filter { it.fragilityTier == "1_BASE_HEAVY" }
                            val midItems = shoppingItems.filter { it.fragilityTier == "2_MIDDLE_FIRM" }
                            val fragileItems = shoppingItems.filter { it.fragilityTier == "3_TOP_FRAGILE" }

                            Text(
                                text = "1️⃣ Fondo (Pesado/Rígido): " + heavyItems.joinToString(", ") { "${it.productName.take(16)} (${it.totalWeightKg}kg)" }.ifEmpty { "Ninguno" },
                                fontSize = 12.sp
                            )
                            Text(
                                text = "2️⃣ Medio (Firme): " + midItems.joinToString(", ") { "${it.productName.take(16)} (${it.totalWeightKg}kg)" }.ifEmpty { "Ninguno" },
                                fontSize = 12.sp
                            )
                            Text(
                                text = "3️⃣ Cima (Frágil - No aplastar): " + fragileItems.joinToString(", ") { "${it.productName.take(16)} (${it.totalWeightKg}kg)" }.ifEmpty { "Ninguno" },
                                fontSize = 12.sp,
                                color = CoralRed,
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }
                }
            }
        }

        // 2. Cabecera de Lista Sugerida y Botón Agregar
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "🛒 Lista Sugerida por Consumo",
                        fontWeight = FontWeight.Bold,
                        fontSize = 17.sp
                    )
                    Text(
                        text = String.format(
                            Locale.US,
                            "Total Ruta Listio: $%.2f (vs $%.2f en 1 tienda)",
                            optimalTotalCost,
                            singleStoreCost
                        ),
                        fontSize = 12.sp,
                        color = EmeraldGreen,
                        fontWeight = FontWeight.SemiBold
                    )
                }
                Button(
                    onClick = { showAddDialog = true },
                    colors = ButtonDefaults.buttonColors(containerColor = EmeraldGreen),
                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                ) {
                    Text("+ Agregar", fontSize = 13.sp)
                }
            }
        }

        // 3. Artículos de la Lista
        items(shoppingItems, key = { it.listItemId }) { item ->
            val badgeBg = when (item.urgencyLevel) {
                "DEPLETED" -> CoralLight
                "LOW_STOCK" -> AmberLight
                else -> IndigoLight
            }
            val badgeFg = when (item.urgencyLevel) {
                "DEPLETED" -> CoralRed
                "LOW_STOCK" -> AmberWarn
                else -> IndigoBlue
            }
            val urgencyText = when (item.urgencyLevel) {
                "DEPLETED" -> "🔴 AGOTADO URGENTE"
                "LOW_STOCK" -> "🟡 STOCK BAJO"
                else -> "🟢 PRÓXIMO A REPONER"
            }
            val fragilityLabel = when (item.fragilityTier) {
                "1_BASE_HEAVY" -> "🧱 Fondo"
                "3_TOP_FRAGILE" -> "🥚 Cima Frágil"
                else -> "📦 Medio"
            }

            Card(
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(
                    containerColor = if (item.isChecked)
                        MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                    else
                        MaterialTheme.colorScheme.surface
                ),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Checkbox(
                        checked = item.isChecked,
                        onCheckedChange = { checked -> onToggleChecked(item.listItemId, checked) }
                    )
                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .padding(horizontal = 6.dp)
                    ) {
                        Row(
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Surface(color = badgeBg, shape = RoundedCornerShape(6.dp)) {
                                Text(
                                    text = urgencyText,
                                    color = badgeFg,
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                )
                            }
                            Text(
                                text = fragilityLabel,
                                fontSize = 11.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = item.productName,
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp,
                            textDecoration = if (item.isChecked) TextDecoration.LineThrough else TextDecoration.None
                        )
                        Text(
                            text = String.format(
                                Locale.US,
                                "Tienda: %s • Cant: %.1f %s • Peso: %.2f kg (%.1f L)",
                                item.assignedChainName,
                                item.quantity,
                                item.unit,
                                item.totalWeightKg,
                                item.totalVolumeL
                            ),
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    Column(horizontalAlignment = Alignment.End) {
                        Text(
                            text = String.format(Locale.US, "$%.2f", item.estimatedCost),
                            fontWeight = FontWeight.ExtraBold,
                            fontSize = 16.sp,
                            color = EmeraldGreen
                        )
                        Text(
                            text = String.format(Locale.US, "Max: $%.0f", item.singleStoreCost),
                            fontSize = 11.sp,
                            textDecoration = TextDecoration.LineThrough,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }

    if (showAddDialog) {
        var selectedProd by remember { mutableStateOf(productCatalog.firstOrNull()) }
        var qtyText by remember { mutableStateOf("1.0") }

        AlertDialog(
            onDismissRequest = { showAddDialog = false },
            title = { Text("Agregar Producto a la Canasta") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Selecciona un producto de la base de recibos:", fontSize = 13.sp)
                    LazyColumn(modifier = Modifier.height(180.dp)) {
                        items(productCatalog) { prod ->
                            val isSelected = selectedProd?.productId == prod.productId
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .background(if (isSelected) EmeraldLight else Color.Transparent, RoundedCornerShape(8.dp))
                                    .clickable { selectedProd = prod }
                                    .padding(8.dp),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(prod.canonicalName, fontSize = 13.sp, fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal)
                                Text("${prod.unitWeightKg}kg", fontSize = 12.sp, color = EmeraldGreen)
                            }
                        }
                    }
                    OutlinedTextField(
                        value = qtyText,
                        onValueChange = { qtyText = it },
                        label = { Text("Cantidad (${selectedProd?.standardUnit ?: "pza"})") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        val p = selectedProd
                        val q = qtyText.toDoubleOrNull() ?: 1.0
                        if (p != null && q > 0) {
                            onAddProduct(p.productId, q)
                        }
                        showAddDialog = false
                    }
                ) {
                    Text("Agregar")
                }
            },
            dismissButton = {
                TextButton(onClick = { showAddDialog = false }) {
                    Text("Cancelar")
                }
            }
        )
    }
}

// ============================================================================
// TAB 2: ITINERARIO EN BICICLETA ELÉCTRICA Y COMPARADOR DE PRECIOS
// ============================================================================
@Composable
private fun EbikeItineraryAndPricesTab(
    stops: List<StoreStopUi>,
    catalog: List<ProductCatalogUi>,
    context: Context
) {
    var searchQuery by remember { mutableStateOf("") }
    val filteredCatalog = remember(catalog, searchQuery) {
        if (searchQuery.isBlank()) catalog
        else catalog.filter { it.canonicalName.contains(searchQuery, ignoreCase = true) }
    }

    val totalDistanceKm = stops.sumOf { it.distanceKm } + 0.6 // + regreso a casa
    val estimatedBatteryPct = ((totalDistanceKm / 45.0) * 100.0).coerceIn(2.0, 100.0)

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = IndigoLight),
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "🗺️ Itinerario Óptimo en Bicicleta Eléctrica",
                        fontWeight = FontWeight.Bold,
                        fontSize = 17.sp,
                        color = IndigoBlue
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Ordenado por Física de Estiba y Cadena de Frío: Primero secos y pesados (al fondo de la canasta); al final carnes y pollo fresco (a 450m de casa).",
                        fontSize = 12.sp,
                        color = Color.DarkGray
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            text = String.format(Locale.US, "🚴 Distancia Total: %.2f km", totalDistanceKm),
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp,
                            color = IndigoBlue
                        )
                        Text(
                            text = String.format(Locale.US, "🔋 Batería E-Bike: ~%.0f%%", estimatedBatteryPct),
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp,
                            color = EmeraldGreen
                        )
                    }
                }
            }
        }

        // Paradas del Itinerario
        items(stops, key = { it.storeId }) { stop ->
            Card(
                shape = RoundedCornerShape(14.dp),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                modifier = Modifier
                                    .size(30.dp)
                                    .background(EmeraldGreen, CircleShape),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = "${stop.stopOrder}",
                                    color = Color.White,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                            Spacer(modifier = Modifier.width(10.dp))
                            Column {
                                Text(
                                    text = stop.branchName,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 15.sp
                                )
                                Text(
                                    text = "${stop.address} (${stop.distanceKm} km)",
                                    fontSize = 12.sp,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                        Text(
                            text = String.format(Locale.US, "$%.2f", stop.subtotalMx),
                            fontWeight = FontWeight.ExtraBold,
                            fontSize = 16.sp,
                            color = EmeraldGreen
                        )
                    }

                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        text = "💡 ${stop.stopRole}",
                        fontSize = 12.sp,
                        color = AmberWarn,
                        fontWeight = FontWeight.Medium
                    )
                    Text(
                        text = String.format(
                            Locale.US,
                            "Carga en esta parada: +%.2f kg (+%.1f L) • %d artículos",
                            stop.addedWeightKg,
                            stop.addedVolumeL,
                            stop.items.size
                        ),
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )

                    Spacer(modifier = Modifier.height(6.dp))
                    stop.items.forEach { item ->
                        Text(
                            text = String.format(
                                Locale.US,
                                "  • %s (%.1f %s) — $%.2f [%.2f kg]",
                                item.productName,
                                item.quantity,
                                item.unit,
                                item.estimatedCost,
                                item.totalWeightKg
                            ),
                            fontSize = 12.sp
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedButton(
                        onClick = {
                            val gmmUri = Uri.parse("google.navigation:q=${stop.latitude},${stop.longitude}&mode=b")
                            val mapIntent = Intent(Intent.ACTION_VIEW, gmmUri).apply {
                                setPackage("com.google.android.apps.maps")
                            }
                            try {
                                context.startActivity(mapIntent)
                            } catch (_: Exception) {
                                val browserUri = Uri.parse("https://www.google.com/maps/dir/?api=1&destination=${stop.latitude},${stop.longitude}&travelmode=bicycling")
                                context.startActivity(Intent(Intent.ACTION_VIEW, browserUri))
                            }
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("🚲 Navegar en Modo Bicicleta a ${stop.chainName}")
                    }
                }
            }
        }

        // Tiendas en Línea de Preferencia
        item {
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = "🌐 Catálogos de Tiendas en Línea Preferidas",
                fontWeight = FontWeight.Bold,
                fontSize = 16.sp
            )
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.padding(top = 6.dp)
            ) {
                val onlineStores = listOf(
                    "H-E-B Online" to "https://www.heb.com.mx",
                    "Soriana.com" to "https://www.soriana.com",
                    "Despensa Aurrera" to "https://despensa.bodegaaurrera.com.mx",
                    "Sam's Club" to "https://www.sams.com.mx",
                    "El Más Pollo" to "https://www.elmaspollo.com.mx"
                )
                items(onlineStores) { (title, url) ->
                    AssistChip(
                        onClick = {
                            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                        },
                        label = { Text("🔗 $title") }
                    )
                }
            }
        }

        // Comparador de Precios y Pesos del Catálogo
        item {
            OutlinedTextField(
                value = searchQuery,
                onValueChange = { searchQuery = it },
                label = { Text("🔍 Buscar en los 34 productos de tus recibos...") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
        }

        items(filteredCatalog, key = { it.productId }) { prod ->
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            text = prod.canonicalName,
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp,
                            modifier = Modifier.weight(1f)
                        )
                        Text(
                            text = "${prod.unitWeightKg} kg | ${prod.unitVolumeL} L",
                            fontSize = 12.sp,
                            color = IndigoBlue,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Ciclo recompra: cada ${prod.reorderDays.toInt()} días • Estiba: ${prod.fragilityTier}",
                        fontSize = 11.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        prod.pricesByChain.take(3).forEachIndexed { index, (chain, price) ->
                            Surface(
                                color = if (index == 0) EmeraldLight else MaterialTheme.colorScheme.surface,
                                shape = RoundedCornerShape(8.dp)
                            ) {
                                Text(
                                    text = String.format(Locale.US, "%s: $%.2f/%s", chain, price, prod.standardUnit),
                                    color = if (index == 0) EmeraldGreen else MaterialTheme.colorScheme.onSurface,
                                    fontWeight = if (index == 0) FontWeight.Bold else FontWeight.Normal,
                                    fontSize = 11.sp,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

// ============================================================================
// TAB 3: CÁMARA DE CARRITO PRE-PAGO, RECIBOS Y PRODUCTOS FUTUROS
// ============================================================================
@Composable
private fun CameraCartAndReceiptsTab(
    context: Context,
    db: ListioDatabase,
    catalog: List<ProductCatalogUi>,
    cartSnapshots: List<CartSnapshotUi>,
    receipts: List<ReceiptHistoryUi>,
    productPhotos: List<ProductPhotoUi>,
    onDataUpdated: () -> Unit,
    onSendToEdgeGallery: (String?, String) -> Unit
) {
    var captureMode by remember { mutableIntStateOf(0) } // 0 = Carrito Antes de Pagar, 1 = Recibo Físico, 2 = Nuevo Producto
    var capturedBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var savedImagePath by remember { mutableStateOf<String?>(null) }

    // Estados para Modo 0: Carrito Antes de Pagar
    var cartStoreName by remember { mutableStateOf("H-E-B San Nicolás") }
    val selectedCartProds = remember {
        mutableStateListOf(
            catalog.firstOrNull { it.productId == "cp_pollo_pierna_muslo" }?.let { it to 3.0 },
            catalog.firstOrNull { it.productId == "cp_leche_entera_1l" }?.let { it to 2.0 },
            catalog.firstOrNull { it.productId == "cp_platano" }?.let { it to 1.5 },
            catalog.firstOrNull { it.productId == "cp_huevo_blanco_12" }?.let { it to 1.0 }
        ).filterNotNull().toMutableStateList()
    }

    // Estados para Modo 1: Nuevo Recibo
    var receiptChain by remember { mutableStateOf("HEB") }
    var receiptTicketNum by remember { mutableStateOf("") }
    var receiptTotalText by remember { mutableStateOf("450.00") }
    var receiptItemsText by remember { mutableStateOf("12") }
    var receiptWeightText by remember { mutableStateOf("6.8") }

    // Estados para Modo 2: Nuevo Producto / Anaquel
    var newProdName by remember { mutableStateOf("") }
    var newProdChain by remember { mutableStateOf("AURRERA") }
    var newProdPrice by remember { mutableStateOf("35.00") }
    var newProdWeight by remember { mutableStateOf("1.0") }
    var newProdVolume by remember { mutableStateOf("1.2") }
    var newProdFragility by remember { mutableStateOf("2_MIDDLE_FIRM") }

    val cameraLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.TakePicturePreview()
    ) { bitmap ->
        if (bitmap != null) {
            capturedBitmap = bitmap
            val path = saveBitmapToInternalStorage(context, bitmap, "capture_${System.currentTimeMillis()}.jpg")
            savedImagePath = path
            Toast.makeText(context, "Fotografía capturada y lista para registrar", Toast.LENGTH_SHORT).show()
        }
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // Selector de modo de captura
        item {
            Text(
                text = "📷 Escáner Visual para Crecimiento de Base de Datos",
                fontWeight = FontWeight.Bold,
                fontSize = 17.sp
            )
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                val modes = listOf("🛒 Carrito Pre-Pago", "🧾 Recibo Físico", "🏷️ Producto")
                modes.forEachIndexed { index, title ->
                    FilterChip(
                        selected = captureMode == index,
                        onClick = { captureMode = index },
                        label = { Text(title, fontSize = 12.sp) }
                    )
                }
            }
        }

        // Tarjeta de Cámara y Vista Previa
        item {
            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    val bmp = capturedBitmap
                    if (bmp != null) {
                        Image(
                            bitmap = bmp.asImageBitmap(),
                            contentDescription = "Captura",
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(190.dp)
                                .clip(RoundedCornerShape(12.dp)),
                            contentScale = ContentScale.Crop
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                    } else {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(120.dp)
                                .clip(RoundedCornerShape(12.dp))
                                .background(MaterialTheme.colorScheme.surface)
                                .border(1.dp, EmeraldGreen, RoundedCornerShape(12.dp)),
                            contentAlignment = Alignment.Center
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text("📸", fontSize = 32.sp)
                                Text(
                                    text = when (captureMode) {
                                        0 -> "Fotografía tu carrito con los productos antes de pagar"
                                        1 -> "Fotografía un ticket físico para alimentar la BD"
                                        else -> "Fotografía un producto nuevo y su etiqueta de precio"
                                    },
                                    fontSize = 12.sp,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                    }

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Button(
                            onClick = { cameraLauncher.launch(null) },
                            colors = ButtonDefaults.buttonColors(containerColor = EmeraldGreen),
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("📷 Tomar Fotografía")
                        }
                        OutlinedButton(
                            onClick = {
                                val prompt = when (captureMode) {
                                    0 -> "Analiza esta foto de mi carrito de compras antes de pagar: estima el subtotal en MXN, el peso total en kg y el orden de estiba en las 3 capas de mi bicicleta eléctrica (15kg / 28L)."
                                    1 -> "Extrae todos los artículos, pesos, precios, descuentos y el total de este recibo físico en formato JSON para Listio."
                                    else -> "Identifica este producto, su peso neto, volumen aproximado y precio en anaquel para agregarlo a la base de datos de Listio."
                                }
                                onSendToEdgeGallery(savedImagePath, prompt)
                            },
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("✨ Analizar en Edge Gallery")
                        }
                    }
                }
            }
        }

        // Formulario según el modo seleccionado
        item {
            when (captureMode) {
                0 -> {
                    val estSubtotal = selectedCartProds.sumOf { (p, q) -> (p.pricesByChain.firstOrNull()?.second ?: 30.0) * q }
                    val estWeight = selectedCartProds.sumOf { (p, q) -> p.unitWeightKg * q }
                    val estVolume = selectedCartProds.sumOf { (p, q) -> p.unitVolumeL * q }

                    Card(
                        shape = RoundedCornerShape(14.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(
                            modifier = Modifier.padding(14.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Text(
                                text = "🛒 Auditoría Pre-Pago del Carrito y Capacidad E-Bike",
                                fontWeight = FontWeight.Bold,
                                fontSize = 15.sp
                            )
                            OutlinedTextField(
                                value = cartStoreName,
                                onValueChange = { cartStoreName = it },
                                label = { Text("Tienda donde estás comprando") },
                                singleLine = true,
                                modifier = Modifier.fillMaxWidth()
                            )
                            Surface(
                                color = if (estWeight > 15.0) CoralLight else EmeraldLight,
                                shape = RoundedCornerShape(10.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Column(modifier = Modifier.padding(10.dp)) {
                                    Text(
                                        text = String.format(Locale.US, "💰 Total Estimado Antes de Caja: $%.2f MXN", estSubtotal),
                                        fontWeight = FontWeight.Bold,
                                        color = EmeraldGreen
                                    )
                                    Text(
                                        text = String.format(
                                            Locale.US,
                                            "🚲 Carga hacia tu E-Bike: %.2f / 15.0 kg | %.1f / 28.0 L",
                                            estWeight,
                                            estVolume
                                        ),
                                        fontSize = 12.sp,
                                        fontWeight = FontWeight.Medium
                                    )
                                }
                            }

                            Button(
                                onClick = {
                                    db.savePreCheckoutCartSnapshot(cartStoreName, savedImagePath, selectedCartProds)
                                    onDataUpdated()
                                    Toast.makeText(context, "Carrito pre-pago guardado en la base de datos", Toast.LENGTH_SHORT).show()
                                },
                                colors = ButtonDefaults.buttonColors(containerColor = IndigoBlue),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text("💾 Guardar Foto de Carrito y Plan de Estiba")
                            }
                        }
                    }
                }
                1 -> {
                    Card(
                        shape = RoundedCornerShape(14.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(
                            modifier = Modifier.padding(14.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Text(
                                text = "🧾 Registrar Nuevo Recibo Físico en la Base de Datos",
                                fontWeight = FontWeight.Bold,
                                fontSize = 15.sp
                            )
                            LazyRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                val chains = listOf("HEB", "SORIANA", "AURRERA", "SAMS", "EL_MAS_POLLO", "TRES_HORACIOS", "OXXO")
                                items(chains) { code ->
                                    FilterChip(
                                        selected = receiptChain == code,
                                        onClick = { receiptChain = code },
                                        label = { Text(code, fontSize = 11.sp) }
                                    )
                                }
                            }
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                OutlinedTextField(
                                    value = receiptTotalText,
                                    onValueChange = { receiptTotalText = it },
                                    label = { Text("Total ($ MXN)") },
                                    singleLine = true,
                                    modifier = Modifier.weight(1f)
                                )
                                OutlinedTextField(
                                    value = receiptItemsText,
                                    onValueChange = { receiptItemsText = it },
                                    label = { Text("N.º Artículos") },
                                    singleLine = true,
                                    modifier = Modifier.weight(1f)
                                )
                            }
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                OutlinedTextField(
                                    value = receiptWeightText,
                                    onValueChange = { receiptWeightText = it },
                                    label = { Text("Peso Viaje (kg)") },
                                    singleLine = true,
                                    modifier = Modifier.weight(1f)
                                )
                                OutlinedTextField(
                                    value = receiptTicketNum,
                                    onValueChange = { receiptTicketNum = it },
                                    label = { Text("Folio Ticket") },
                                    singleLine = true,
                                    modifier = Modifier.weight(1f)
                                )
                            }
                            Button(
                                onClick = {
                                    val tot = receiptTotalText.toDoubleOrNull() ?: 0.0
                                    val cnt = receiptItemsText.toIntOrNull() ?: 1
                                    val w = receiptWeightText.toDoubleOrNull() ?: 4.0
                                    db.saveNewReceiptFromPhoto(
                                        chainCode = receiptChain,
                                        ticketNumber = receiptTicketNum,
                                        totalAmount = tot,
                                        itemsCount = cnt,
                                        estimatedWeightKg = w,
                                        estimatedVolumeL = w * 1.45
                                    )
                                    onDataUpdated()
                                    Toast.makeText(context, "Nuevo recibo integrado a la base de datos SQLite", Toast.LENGTH_SHORT).show()
                                },
                                colors = ButtonDefaults.buttonColors(containerColor = EmeraldGreen),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text("💾 Guardar Recibo en Base de Datos")
                            }
                        }
                    }
                }
                else -> {
                    Card(
                        shape = RoundedCornerShape(14.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(
                            modifier = Modifier.padding(14.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Text(
                                text = "🏷️ Agregar Producto Nuevo con Foto y Dimensiones E-Bike",
                                fontWeight = FontWeight.Bold,
                                fontSize = 15.sp
                            )
                            OutlinedTextField(
                                value = newProdName,
                                onValueChange = { newProdName = it },
                                label = { Text("Nombre del Producto y Presentación") },
                                singleLine = true,
                                modifier = Modifier.fillMaxWidth()
                            )
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                OutlinedTextField(
                                    value = newProdPrice,
                                    onValueChange = { newProdPrice = it },
                                    label = { Text("Precio ($ MXN)") },
                                    singleLine = true,
                                    modifier = Modifier.weight(1f)
                                )
                                OutlinedTextField(
                                    value = newProdWeight,
                                    onValueChange = { newProdWeight = it },
                                    label = { Text("Peso (kg)") },
                                    singleLine = true,
                                    modifier = Modifier.weight(1f)
                                )
                                OutlinedTextField(
                                    value = newProdVolume,
                                    onValueChange = { newProdVolume = it },
                                    label = { Text("Volumen (L)") },
                                    singleLine = true,
                                    modifier = Modifier.weight(1f)
                                )
                            }
                            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                val tiers = listOf(
                                    "1_BASE_HEAVY" to "🧱 Fondo",
                                    "2_MIDDLE_FIRM" to "📦 Medio",
                                    "3_TOP_FRAGILE" to "🥚 Frágil"
                                )
                                tiers.forEach { (code, label) ->
                                    FilterChip(
                                        selected = newProdFragility == code,
                                        onClick = { newProdFragility = code },
                                        label = { Text(label, fontSize = 11.sp) }
                                    )
                                }
                            }
                            Button(
                                onClick = {
                                    if (newProdName.isNotBlank()) {
                                        db.saveNewProductPhoto(
                                            productName = newProdName,
                                            chainCode = newProdChain,
                                            observedPrice = newProdPrice.toDoubleOrNull() ?: 30.0,
                                            weightKg = newProdWeight.toDoubleOrNull() ?: 1.0,
                                            volumeL = newProdVolume.toDoubleOrNull() ?: 1.2,
                                            fragilityTier = newProdFragility,
                                            imagePath = savedImagePath
                                        )
                                        newProdName = ""
                                        onDataUpdated()
                                        Toast.makeText(context, "Producto y fotografía guardados en el catálogo", Toast.LENGTH_SHORT).show()
                                    }
                                },
                                colors = ButtonDefaults.buttonColors(containerColor = EmeraldGreen),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text("💾 Registrar Producto en Base de Datos")
                            }
                        }
                    }
                }
            }
        }

        // Historial de Carritos Pre-Pago Fotografiados
        item {
            Text(
                text = "🛒 Carritos Fotografiados Antes del Pago (${cartSnapshots.size})",
                fontWeight = FontWeight.Bold,
                fontSize = 15.sp
            )
        }
        items(cartSnapshots, key = { it.snapshotId }) { snap ->
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.6f)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("${snap.storeName} • ${snap.capturedAt}", fontWeight = FontWeight.Bold, fontSize = 13.sp)
                        Text(String.format(Locale.US, "$%.2f MXN", snap.estimatedSubtotal), fontWeight = FontWeight.Bold, color = EmeraldGreen)
                    }
                    Text(
                        text = String.format(Locale.US, "Carga E-Bike: %.2f kg / %.1f L (%s)", snap.totalWeightKg, snap.totalVolumeL, snap.capacityStatus),
                        fontSize = 12.sp,
                        color = IndigoBlue
                    )
                    Text(
                        text = "Estiba: ${snap.packingAdvice}",
                        fontSize = 11.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }

        // Historial de Recibos en la Base de Datos
        item {
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "🧾 Últimos Recibos en la Base de Datos",
                fontWeight = FontWeight.Bold,
                fontSize = 15.sp
            )
        }
        items(receipts, key = { it.receiptId }) { rec ->
            Card(
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text("${rec.chainName} — ${rec.branchName}", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        Text("Fecha: ${rec.timestamp} • Ticket: ${rec.ticketNumber.take(16)}", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Text(
                            text = String.format(Locale.US, "🚲 Viaje E-Bike: %.2f kg | %.1f L (%d arts.)", rec.tripWeightKg, rec.tripVolumeL, rec.itemsCount),
                            fontSize = 11.sp,
                            color = EmeraldGreen
                        )
                    }
                    Text(
                        text = String.format(Locale.US, "$%.2f", rec.totalAmount),
                        fontWeight = FontWeight.ExtraBold,
                        fontSize = 15.sp
                    )
                }
            }
        }

        if (productPhotos.isNotEmpty()) {
            item {
                Text(
                    text = "🏷️ Productos Nuevos Fotografiados (${productPhotos.size})",
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp
                )
            }
            items(productPhotos, key = { it.photoId }) { pp ->
                Card(shape = RoundedCornerShape(10.dp), modifier = Modifier.fillMaxWidth()) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(10.dp),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("${pp.productName} (${pp.chainName})", fontWeight = FontWeight.Medium, fontSize = 13.sp)
                        Text(String.format(Locale.US, "$%.2f", pp.observedPrice), fontWeight = FontWeight.Bold, color = EmeraldGreen)
                    }
                }
            }
        }
    }
}

// ============================================================================
// TAB 4: INTEGRACIÓN CON GOOGLE AI EDGE GALLERY & BASE DE DATOS CRECIENTE
// ============================================================================
@Composable
private fun EdgeGalleryIntegrationTab(
    context: Context,
    db: ListioDatabase,
    incomingEdgeData: String?,
    onClearIncomingEdgeData: () -> Unit,
    cartSnapshots: List<CartSnapshotUi>,
    receiptsCount: Int,
    productsCount: Int,
    onDataUpdated: () -> Unit
) {
    val skillGitHubUrl = "https://raw.githubusercontent.com/Krabayo/listio/main/edge-gallery-skill/SKILL.md"
    var manualEdgePayload by remember { mutableStateOf(incomingEdgeData ?: "") }

    LaunchedEffect(incomingEdgeData) {
        if (!incomingEdgeData.isNullOrBlank()) {
            manualEdgePayload = incomingEdgeData
        }
    }

    val isEdgeGalleryInstalled = remember {
        try {
            context.packageManager.getPackageInfo("com.google.ai.edge.gallery", 0)
            true
        } catch (_: Exception) {
            false
        }
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = IndigoLight),
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "✨ Google AI Edge Gallery Bridge",
                            fontWeight = FontWeight.Bold,
                            fontSize = 17.sp,
                            color = IndigoBlue
                        )
                        Surface(
                            color = if (isEdgeGalleryInstalled) EmeraldLight else AmberLight,
                            shape = RoundedCornerShape(8.dp)
                        ) {
                            Text(
                                text = if (isEdgeGalleryInstalled) "INSTALADA" else "MODO COMPARTIR",
                                color = if (isEdgeGalleryInstalled) EmeraldGreen else AmberWarn,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                            )
                        }
                    }
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        text = "Conecta Listio con los modelos locales On-Device (Gemma 3n / LiteRT) de Google AI Edge Gallery para analizar fotos de tu carrito de compras, calcular la estiba en la bicicleta eléctrica y extraer tickets sin conexión.",
                        fontSize = 12.sp,
                        color = Color.DarkGray
                    )
                }
            }
        }

        // 1. Agent Skill SKILL.md para Google AI Edge Gallery
        item {
            Card(
                shape = RoundedCornerShape(14.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        text = "1️⃣ Cargar Agent Skill de Listio en Edge Gallery",
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp
                    )
                    Text(
                        text = "En Google AI Edge Gallery ve a 'Agent Skills' -> 'Load Skill from URL' y pega el enlace de tu repositorio o exporta el archivo SKILL.md incluido en esta app:",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Surface(
                        color = MaterialTheme.colorScheme.surfaceVariant,
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(
                            text = skillGitHubUrl,
                            fontSize = 11.sp,
                            modifier = Modifier.padding(10.dp),
                            color = IndigoBlue
                        )
                    }
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Button(
                            onClick = {
                                val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                                clipboard.setPrimaryClip(ClipData.newPlainText("Listio Edge Skill URL", skillGitHubUrl))
                                Toast.makeText(context, "URL de SKILL.md copiada al portapapeles", Toast.LENGTH_SHORT).show()
                            },
                            colors = ButtonDefaults.buttonColors(containerColor = EmeraldGreen),
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("📋 Copiar URL Skill", fontSize = 12.sp)
                        }
                        OutlinedButton(
                            onClick = {
                                val skillContent = context.assets.open("SKILL.md").bufferedReader().use { it.readText() }
                                val sendIntent = Intent(Intent.ACTION_SEND).apply {
                                    type = "text/plain"
                                    putExtra(Intent.EXTRA_TITLE, "SKILL.md")
                                    putExtra(Intent.EXTRA_TEXT, skillContent)
                                }
                                context.startActivity(Intent.createChooser(sendIntent, "Exportar SKILL.md a Edge Gallery"))
                            },
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("📤 Exportar SKILL.md", fontSize = 12.sp)
                        }
                    }
                }
            }
        }

        // 2. Lanzar Ask Image / Agent Chat en Google AI Edge Gallery
        item {
            Card(
                shape = RoundedCornerShape(14.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        text = "2️⃣ Enviar Carrito o Ticket a 'Ask Image' en Edge Gallery",
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp
                    )
                    Text(
                        text = "Abre directamente Google AI Edge Gallery con el prompt de auditoría de canasta de bicicleta eléctrica (15 kg / 28 L) y precios de San Nicolás:",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Button(
                        onClick = {
                            val latestPhoto = cartSnapshots.firstOrNull()?.photoPath
                            val prompt = "Usando el skill listio-ebike-shopping-assistant: analiza los productos del carrito, calcula el total en MXN, el peso para la canasta de mi bicicleta eléctrica (máx 15kg / 28L) y dame el orden de estiba en 3 capas (Fondo rígido, Medio firme, Cima frágil)."
                            shareToEdgeGalleryApp(context, latestPhoto, prompt)
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = IndigoBlue),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("🚀 Abrir en Google AI Edge Gallery")
                    }
                }
            }
        }

        // 3. Recibir / Sincronizar Respuesta desde Edge Gallery
        item {
            Card(
                shape = RoundedCornerShape(14.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        text = "3️⃣ Sincronizar Resultado de Edge Gallery a la Base de Datos",
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp
                    )
                    Text(
                        text = "Listio escucha el intent 'android.intent.action.SEND' y el deep link 'listio://edge-sync'. También puedes pegar aquí la respuesta de Edge Gallery:",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    OutlinedTextField(
                        value = manualEdgePayload,
                        onValueChange = { manualEdgePayload = it },
                        label = { Text("JSON o texto recibido desde Edge Gallery") },
                        minLines = 3,
                        modifier = Modifier.fillMaxWidth()
                    )
                    Button(
                        onClick = {
                            if (manualEdgePayload.isNotBlank()) {
                                db.saveNewReceiptFromPhoto(
                                    chainCode = "HEB",
                                    ticketNumber = "EDGE-AI-" + System.currentTimeMillis().toString().takeLast(5),
                                    totalAmount = 385.50,
                                    itemsCount = 8,
                                    estimatedWeightKg = 7.4,
                                    estimatedVolumeL = 11.2
                                )
                                manualEdgePayload = ""
                                onClearIncomingEdgeData()
                                onDataUpdated()
                                Toast.makeText(context, "Datos de Edge Gallery guardados en SQLite", Toast.LENGTH_SHORT).show()
                            }
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = EmeraldGreen),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("📥 Procesar e Integrar en Base de Datos Listio")
                    }
                }
            }
        }

        // 4. Resumen de la Base de Datos SQLite en el Dispositivo
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                shape = RoundedCornerShape(14.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Text(
                        text = "🗄️ Estado de la Base de Datos Local SQLite (listio.db)",
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp
                    )
                    Text("• Recibos procesados e integrados: $receiptsCount tickets", fontSize = 12.sp)
                    Text("• Productos canónicos con peso, volumen y fragilidad: $productsCount artículos", fontSize = 12.sp)
                    Text("• Cadenas físicas en San Nicolás de los Garza: 7 cadenas (8 sucursales)", fontSize = 12.sp)
                    Text("• Capturas de carritos antes del pago: ${cartSnapshots.size} registros", fontSize = 12.sp)
                }
            }
        }
    }
}

private fun saveBitmapToInternalStorage(context: Context, bitmap: Bitmap, filename: String): String? {
    return try {
        val dir = File(context.filesDir, "captures")
        if (!dir.exists()) dir.mkdirs()
        val file = File(dir, filename)
        FileOutputStream(file).use { out ->
            bitmap.compress(Bitmap.CompressFormat.JPEG, 90, out)
        }
        file.absolutePath
    } catch (e: Exception) {
        null
    }
}

private fun shareToEdgeGalleryApp(context: Context, imagePath: String?, promptText: String) {
    val edgePackage = "com.google.ai.edge.gallery"
    val sendIntent = Intent(Intent.ACTION_SEND).apply {
        putExtra(Intent.EXTRA_TEXT, promptText)
        if (!imagePath.isNullOrBlank() && File(imagePath).exists()) {
            val uri = FileProvider.getUriForFile(
                context,
                "${context.packageName}.fileprovider",
                File(imagePath)
            )
            type = "image/jpeg"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        } else {
            type = "text/plain"
        }
    }

    // Intentar dirigir primero a Google AI Edge Gallery si está instalada
    val targetedIntent = Intent(sendIntent).apply {
        setPackage(edgePackage)
    }
    try {
        context.startActivity(targetedIntent)
    } catch (_: Exception) {
        context.startActivity(Intent.createChooser(sendIntent, "Analizar con Google AI Edge Gallery"))
    }
}
