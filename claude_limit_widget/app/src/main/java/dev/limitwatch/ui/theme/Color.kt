package dev.limitwatch.ui.theme

import androidx.compose.ui.graphics.Color

val ClaudeOrange = Color(0xFFCC785C)
val ClaudeAmber = Color(0xFFE0A050)
val ClaudeRed = Color(0xFFC24040)
val ClaudeGreen = Color(0xFF6A9F5B)

val Cream = Color(0xFFF6F0EA)
val CreamDim = Color(0xFFECE4DA)
val Ink = Color(0xFF1B1B1B)
val InkDim = Color(0xFF2A2A2A)
val Mist = Color(0xFF9A928A)

fun accentForUtilization(percent: Double?): Color = when {
    percent == null -> Mist
    percent >= 90.0 -> ClaudeRed
    percent >= 70.0 -> ClaudeAmber
    else -> ClaudeOrange
}
