package dev.limitwatch.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val LightColors = lightColorScheme(
    primary = ClaudeOrange,
    onPrimary = Cream,
    secondary = ClaudeAmber,
    background = Cream,
    surface = Cream,
    onBackground = Ink,
    onSurface = Ink,
    error = ClaudeRed,
)

private val DarkColors = darkColorScheme(
    primary = ClaudeOrange,
    onPrimary = Ink,
    secondary = ClaudeAmber,
    background = Ink,
    surface = InkDim,
    onBackground = Cream,
    onSurface = Cream,
    error = ClaudeRed,
)

@Composable
fun LimitWatchTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit,
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val ctx = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(ctx) else dynamicLightColorScheme(ctx)
        }
        darkTheme -> DarkColors
        else -> LightColors
    }
    val view = LocalView.current
    if (!view.isInEditMode) {
        val window = (view.context as? Activity)?.window ?: return MaterialTheme(colorScheme, content = content)
        WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
    }
    MaterialTheme(colorScheme = colorScheme, content = content)
}
