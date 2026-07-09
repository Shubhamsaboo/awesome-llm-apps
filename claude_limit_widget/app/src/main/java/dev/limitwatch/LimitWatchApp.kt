package dev.limitwatch

import android.app.Application
import dev.limitwatch.data.AuthStore
import dev.limitwatch.data.UsageRepository
import dev.limitwatch.work.RefreshScheduler

class LimitWatchApp : Application() {

    override fun onCreate() {
        super.onCreate()
        // Warm up singletons before the widget provider needs them.
        AuthStore.get(this)
        UsageRepository.get(this)
        RefreshScheduler.ensureScheduled(this)
    }
}
