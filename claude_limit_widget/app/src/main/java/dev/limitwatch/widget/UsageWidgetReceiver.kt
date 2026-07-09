package dev.limitwatch.widget

import android.appwidget.AppWidgetManager
import android.content.Context
import androidx.glance.appwidget.GlanceAppWidget
import androidx.glance.appwidget.GlanceAppWidgetReceiver
import dev.limitwatch.data.AuthStore
import dev.limitwatch.data.FetchOutcome
import dev.limitwatch.data.UsageRepository
import dev.limitwatch.work.RefreshScheduler
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class UsageWidgetReceiver : GlanceAppWidgetReceiver() {

    override val glanceAppWidget: GlanceAppWidget = UsageWidget()

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    override fun onUpdate(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetIds: IntArray,
    ) {
        super.onUpdate(context, appWidgetManager, appWidgetIds)
        // Kick a one-off worker to actually hit the network; meanwhile publish whatever
        // cached snapshot we already have so the widget doesn't sit on "Loading" for long.
        RefreshScheduler.kickOnce(context)
        scope.launch { publishCurrentState(context) }
    }

    override fun onEnabled(context: Context) {
        super.onEnabled(context)
        RefreshScheduler.ensureScheduled(context)
    }

    override fun onDisabled(context: Context) {
        super.onDisabled(context)
        RefreshScheduler.cancel(context)
    }

    private suspend fun publishCurrentState(context: Context) {
        val hasToken = AuthStore.get(context).current() != null
        val cached = UsageRepository.get(context).currentSnapshot()
        val outcome = if (cached != null) FetchOutcome.Ok(cached) else FetchOutcome.NoCredentials
        WidgetPublisher(context).publishFrom(outcome, hasToken)
    }
}
