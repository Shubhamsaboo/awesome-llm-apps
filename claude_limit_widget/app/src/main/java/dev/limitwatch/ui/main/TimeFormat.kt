package dev.limitwatch.ui.main

import kotlinx.datetime.Clock
import kotlinx.datetime.Instant
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds

/**
 * Renders a duration like "3h 12m" / "42m" / "18s" for the reset countdown, and
 * "just now" / "2m ago" / "1h ago" for the last-updated line.
 */
object TimeFormat {

    fun untilReset(resetsAtIso: String): String? {
        val target = runCatching { Instant.parse(resetsAtIso) }.getOrNull() ?: return null
        val delta = target - Clock.System.now()
        return if (delta.isPositive()) formatDuration(delta) else "now"
    }

    fun sinceEpoch(fetchedAtEpochMs: Long): String {
        val delta = (System.currentTimeMillis() - fetchedAtEpochMs).milliseconds
        val minute = 60.seconds
        val hour = minute * 60
        val day = hour * 24
        return when {
            delta < minute -> "just now"
            delta < hour -> "${delta.inWholeMinutes}m ago"
            delta < day -> "${delta.inWholeHours}h ago"
            else -> "${delta.inWholeDays}d ago"
        }
    }

    private fun formatDuration(d: Duration): String {
        val totalMinutes = d.inWholeMinutes
        return when {
            totalMinutes >= 60 -> "${totalMinutes / 60}h ${totalMinutes % 60}m"
            totalMinutes >= 1 -> "${totalMinutes}m"
            else -> "${d.inWholeSeconds}s"
        }
    }
}
