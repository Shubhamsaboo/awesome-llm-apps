package dev.limitwatch.widget

import android.content.Context
import androidx.glance.appwidget.GlanceAppWidgetManager
import androidx.glance.appwidget.state.updateAppWidgetState
import dev.limitwatch.data.FetchOutcome
import dev.limitwatch.data.UsageRepository

/**
 * Writes a [WidgetState] to every placed widget's DataStore, then triggers Glance
 * to redraw. This is what the ViewModel, worker, and receiver all call.
 */
class WidgetPublisher(private val context: Context) {

    suspend fun publishFrom(outcome: FetchOutcome, hasToken: Boolean) {
        val state = when (outcome) {
            is FetchOutcome.Ok -> WidgetState.Ready(outcome.snapshot)
            FetchOutcome.NoCredentials -> WidgetState.NoToken
            FetchOutcome.Unauthorized -> WidgetState.Error
            is FetchOutcome.Failed -> {
                // Prefer to keep showing the last-known snapshot on transient errors.
                val cached = UsageRepository.get(context).currentSnapshot()
                if (cached != null) WidgetState.Ready(cached)
                else if (!hasToken) WidgetState.NoToken
                else WidgetState.Error
            }
        }
        publish(state)
    }

    suspend fun publishNoToken() = publish(WidgetState.NoToken)

    suspend fun publish(state: WidgetState) {
        val manager = GlanceAppWidgetManager(context)
        val ids = manager.getGlanceIds(UsageWidget::class.java)
        if (ids.isEmpty()) return
        val widget = UsageWidget()
        ids.forEach { id ->
            updateAppWidgetState(context, UsageWidgetStateDefinition, id) { state }
            widget.update(context, id)
        }
    }
}
