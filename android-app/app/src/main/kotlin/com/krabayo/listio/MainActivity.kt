package com.krabayo.listio

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.krabayo.listio.ui.main.ListioAppScreen
import com.krabayo.listio.ui.theme.ListioTheme

class MainActivity : ComponentActivity() {

    private var incomingEdgeGalleryPayload by mutableStateOf<String?>(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        handleIncomingIntent(intent)

        enableEdgeToEdge()
        setContent {
            ListioTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    ListioAppScreen(
                        incomingEdgeData = incomingEdgeGalleryPayload,
                        onClearIncomingEdgeData = { incomingEdgeGalleryPayload = null }
                    )
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleIncomingIntent(intent)
    }

    private fun handleIncomingIntent(intent: Intent?) {
        if (intent == null) return
        when (intent.action) {
            Intent.ACTION_SEND -> {
                if (intent.type == "text/plain") {
                    val sharedText = intent.getStringExtra(Intent.EXTRA_TEXT)
                    if (!sharedText.isNullOrBlank()) {
                        incomingEdgeGalleryPayload = sharedText
                    }
                }
            }
            Intent.ACTION_VIEW -> {
                val dataUri = intent.data
                if (dataUri != null && dataUri.scheme == "listio") {
                    val payload = dataUri.getQueryParameter("payload") ?: dataUri.toString()
                    incomingEdgeGalleryPayload = payload
                }
            }
        }
    }
}
