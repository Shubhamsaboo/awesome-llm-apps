package dev.limitwatch.work

import android.content.Context
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import dev.limitwatch.data.AuthStore
import dev.limitwatch.data.FetchOutcome
import dev.limitwatch.data.UsageRepository
import dev.limitwatch.widget.WidgetPublisher
import java.util.concurrent.TimeUnit

/**
 * Periodic worker that refreshes the usage snapshot and pushes fresh state into the widget.
 * Runs at most every ~15 min per Android policy; the actual cadence is up to the OS.
 */
class RefreshWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val ctx = applicationContext
        val hasToken = AuthStore.get(ctx).current() != null
        val outcome: FetchOutcome = if (!hasToken) {
            FetchOutcome.NoCredentials
        } else {
            UsageRepository.get(ctx).refreshNow()
        }

        WidgetPublisher(ctx).publishFrom(outcome, hasToken)

        return when (outcome) {
            is FetchOutcome.Ok, FetchOutcome.NoCredentials -> Result.success()
            FetchOutcome.Unauthorized -> Result.success() // don't retry a rejected token
            is FetchOutcome.Failed -> Result.retry()
        }
    }
}

object RefreshScheduler {

    private const val PERIODIC_WORK_NAME = "limitwatch.periodic.refresh"
    private const val ONE_OFF_WORK_NAME = "limitwatch.oneoff.refresh"
    private const val INTERVAL_MINUTES = 15L
    private const val FLEX_MINUTES = 5L

    fun ensureScheduled(context: Context) {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()

        val request = PeriodicWorkRequestBuilder<RefreshWorker>(
            INTERVAL_MINUTES, TimeUnit.MINUTES,
            FLEX_MINUTES, TimeUnit.MINUTES,
        )
            .setConstraints(constraints)
            .build()

        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            PERIODIC_WORK_NAME,
            ExistingPeriodicWorkPolicy.KEEP,
            request,
        )
    }

    fun kickOnce(context: Context) {
        val request = OneTimeWorkRequestBuilder<RefreshWorker>()
            .setConstraints(
                Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()
            )
            .build()
        WorkManager.getInstance(context).enqueueUniqueWork(
            ONE_OFF_WORK_NAME,
            ExistingWorkPolicy.REPLACE,
            request,
        )
    }

    fun cancel(context: Context) {
        WorkManager.getInstance(context).cancelUniqueWork(PERIODIC_WORK_NAME)
    }
}
