package dev.limitwatch.widget

import android.content.Context
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.glance.GlanceId
import androidx.glance.GlanceModifier
import androidx.glance.GlanceTheme
import androidx.glance.LocalContext
import androidx.glance.action.clickable
import androidx.glance.appwidget.CircularProgressIndicator
import androidx.glance.appwidget.GlanceAppWidget
import androidx.glance.appwidget.LinearProgressIndicator
import androidx.glance.appwidget.SizeMode
import androidx.glance.appwidget.action.actionStartActivity
import androidx.glance.appwidget.cornerRadius
import androidx.glance.appwidget.provideContent
import androidx.glance.appwidget.updateAll
import androidx.glance.background
import androidx.glance.currentState
import androidx.glance.layout.Alignment
import androidx.glance.layout.Box
import androidx.glance.layout.Column
import androidx.glance.layout.Row
import androidx.glance.layout.Spacer
import androidx.glance.layout.fillMaxSize
import androidx.glance.layout.fillMaxWidth
import androidx.glance.layout.height
import androidx.glance.layout.padding
import androidx.glance.state.GlanceStateDefinition
import androidx.glance.text.FontWeight
import androidx.glance.text.Text
import androidx.glance.text.TextStyle
import androidx.glance.unit.ColorProvider
import dev.limitwatch.MainActivity
import dev.limitwatch.R
import dev.limitwatch.data.UsageResponse
import dev.limitwatch.data.UsageSnapshot
import dev.limitwatch.data.UsageWindow
import dev.limitwatch.ui.main.TimeFormat

class UsageWidget : GlanceAppWidget() {

    override val sizeMode: SizeMode = SizeMode.Exact
    override val stateDefinition: GlanceStateDefinition<*> = UsageWidgetStateDefinition

    override suspend fun provideGlance(context: Context, id: GlanceId) {
        provideContent {
            GlanceTheme {
                val state = currentState<WidgetState>()
                WidgetBody(state)
            }
        }
    }

    companion object {
        suspend fun updateAll(context: Context) {
            UsageWidget().updateAll(context)
        }
    }
}

@Composable
private fun WidgetBody(state: WidgetState) {
    val fg = GlanceTheme.colors.onBackground
    Box(
        modifier = GlanceModifier
            .fillMaxSize()
            .background(GlanceTheme.colors.background)
            .cornerRadius(24.dp)
            .padding(12.dp)
            .clickable(actionStartActivity<MainActivity>()),
    ) {
        when (state) {
            WidgetState.NoToken -> CenterLine(stringOf(R.string.widget_no_token), fg)
            WidgetState.Error -> CenterLine(stringOf(R.string.widget_error), fg)
            WidgetState.Loading -> Box(
                modifier = GlanceModifier.fillMaxSize(),
                contentAlignment = Alignment.Center,
            ) { CircularProgressIndicator() }
            is WidgetState.Ready -> ReadyBody(state.snapshot, fg)
        }
    }
}

@Composable
private fun ReadyBody(snapshot: UsageSnapshot, onBackground: ColorProvider) {
    val usage = snapshot.usage
    val primary = usage.fiveHour
    val secondary = usage.sevenDay
    val opusLike = usage.sevenDayOpus ?: usage.sevenDaySonnet

    Column(modifier = GlanceModifier.fillMaxSize()) {
        Text(
            text = "Claude limits",
            style = TextStyle(color = onBackground, fontSize = 12.sp, fontWeight = FontWeight.Medium),
        )
        Spacer(GlanceModifier.height(6.dp))
        Metric(label = "Session · 5h", window = primary, onBackground = onBackground)
        Spacer(GlanceModifier.height(6.dp))
        Metric(label = "Weekly", window = secondary, onBackground = onBackground)
        if (opusLike != null) {
            Spacer(GlanceModifier.height(6.dp))
            Metric(
                label = if (usage.sevenDayOpus != null) "Opus 7d" else "Sonnet 7d",
                window = opusLike,
                onBackground = onBackground,
            )
        }
    }
}

@Composable
private fun Metric(label: String, window: UsageWindow?, onBackground: ColorProvider) {
    val percent = window?.utilization
    val percentText = percent?.let { "%.0f%%".format(it) } ?: "—"
    val resetText = window?.let { TimeFormat.untilReset(it.resetsAt) }
    val barColor = ColorProvider(accentForUtilization(percent))
    val fraction = ((percent ?: 0.0) / 100.0).coerceIn(0.0, 1.0).toFloat()

    Column(modifier = GlanceModifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = label,
                style = TextStyle(color = onBackground, fontSize = 12.sp),
                modifier = GlanceModifier.defaultWeight(),
            )
            Text(
                text = percentText,
                style = TextStyle(color = onBackground, fontSize = 15.sp, fontWeight = FontWeight.Bold),
            )
        }
        Spacer(GlanceModifier.height(3.dp))
        LinearProgressIndicator(
            progress = fraction,
            modifier = GlanceModifier.fillMaxWidth().height(6.dp),
            color = barColor,
            backgroundColor = ColorProvider(Color(0x22000000)),
        )
        if (resetText != null) {
            Text(
                text = "reset $resetText",
                style = TextStyle(color = onBackground, fontSize = 10.sp),
            )
        }
    }
}

@Composable
private fun CenterLine(text: String, color: ColorProvider) {
    Box(modifier = GlanceModifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text(
            text = text,
            style = TextStyle(color = color, fontSize = 13.sp, fontWeight = FontWeight.Medium),
        )
    }
}

@Composable
private fun stringOf(resId: Int): String = LocalContext.current.getString(resId)

private fun accentForUtilization(percent: Double?): Color = when {
    percent == null -> Color(0xFF9A928A)
    percent >= 90.0 -> Color(0xFFC24040)
    percent >= 70.0 -> Color(0xFFE0A050)
    else -> Color(0xFFCC785C)
}
