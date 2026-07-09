package dev.limitwatch.ui.main

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.limitwatch.R
import dev.limitwatch.data.ExtraUsage
import dev.limitwatch.data.UsageResponse
import dev.limitwatch.data.UsageSnapshot
import dev.limitwatch.data.UsageWindow
import dev.limitwatch.ui.theme.accentForUtilization

@Composable
fun MainScreen(viewModel: MainViewModel) {
    val snapshot by viewModel.snapshot.collectAsState()
    val uiState by viewModel.uiState.collectAsState()
    val credentials by viewModel.credentials.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Header(
            loading = uiState.loading,
            snapshot = snapshot,
            onRefresh = viewModel::refresh,
        )

        val error = uiState.transientError
        if (error != null) {
            ErrorCard(error) { viewModel.refresh() }
        }

        val usage = snapshot?.usage
        when {
            credentials == null -> EmptyState(reason = stringResource(R.string.token_status_missing))
            usage == null && !uiState.loading -> EmptyState(reason = "Tap refresh to fetch usage")
            usage != null -> UsageContent(usage)
        }
    }
}

@Composable
private fun Header(loading: Boolean, snapshot: UsageSnapshot?, onRefresh: () -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = "Claude limits",
                fontSize = 26.sp,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onBackground,
            )
            val subtitle = snapshot?.let { stringResource(R.string.last_updated, TimeFormat.sinceEpoch(it.fetchedAtEpochMs)) }
                ?: "Not fetched yet"
            Text(
                text = subtitle,
                fontSize = 13.sp,
                color = MaterialTheme.colorScheme.onBackground.copy(alpha = 0.6f),
            )
        }
        if (loading) {
            CircularProgressIndicator(
                modifier = Modifier.padding(8.dp).height(24.dp).width(24.dp),
                strokeWidth = 2.dp,
                color = MaterialTheme.colorScheme.primary,
            )
        } else {
            IconButton(onClick = onRefresh) {
                Icon(Icons.Default.Refresh, contentDescription = stringResource(R.string.refresh))
            }
        }
    }
}

@Composable
private fun UsageContent(usage: UsageResponse) {
    UsageCard(title = stringResource(R.string.session_5h), window = usage.fiveHour)
    UsageCard(title = stringResource(R.string.weekly_7d), window = usage.sevenDay)
    usage.sevenDayOpus?.let { UsageCard(title = stringResource(R.string.weekly_opus), window = it) }
    usage.sevenDaySonnet?.let { UsageCard(title = stringResource(R.string.weekly_sonnet), window = it) }
    usage.extraUsage?.takeIf { it.isEnabled }?.let { ExtraUsageCard(it) }
}

@Composable
private fun UsageCard(title: String, window: UsageWindow?) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = title,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Medium,
                    modifier = Modifier.weight(1f),
                )
                Text(
                    text = window?.utilization?.let { "%.0f%%".format(it) } ?: "—",
                    fontSize = 26.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = accentForUtilization(window?.utilization),
                )
            }
            UsageBar(percent = window?.utilization)
            val reset = window?.let { TimeFormat.untilReset(it.resetsAt) }
            if (reset != null) {
                Text(
                    text = stringResource(R.string.reset_in, reset),
                    fontSize = 13.sp,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                )
            }
        }
    }
}

@Composable
private fun UsageBar(percent: Double?, modifier: Modifier = Modifier) {
    val fraction = ((percent ?: 0.0) / 100.0).coerceIn(0.0, 1.0).toFloat()
    val animated by animateFloatAsState(targetValue = fraction, animationSpec = tween(600), label = "bar")
    val track = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.08f)
    val accent = accentForUtilization(percent)
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(12.dp)
            .clip(RoundedCornerShape(6.dp))
            .background(track),
    ) {
        Box(
            modifier = Modifier
                .fillMaxHeight()
                .fillMaxWidth(animated)
                .background(accent),
        )
    }
}

@Composable
private fun ExtraUsageCard(extra: ExtraUsage) {
    Card(shape = RoundedCornerShape(20.dp), modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(
                text = stringResource(R.string.extra_usage),
                fontWeight = FontWeight.Medium,
                fontSize = 15.sp,
            )
            val monthly = extra.monthlyLimit
            val used = extra.usedCredits
            if (monthly != null && used != null) {
                Text(
                    text = "$" + "%.2f".format(used) + " / $" + "%.2f".format(monthly),
                    fontSize = 20.sp,
                    fontWeight = FontWeight.SemiBold,
                )
            }
            UsageBar(percent = extra.utilization)
        }
    }
}

@Composable
private fun ErrorCard(error: UiError, onRetry: () -> Unit) {
    Card(
        shape = RoundedCornerShape(20.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(
                text = when (error) {
                    UiError.NoCredentials -> stringResource(R.string.error_no_token)
                    UiError.Unauthorized -> stringResource(R.string.error_unauthorized)
                    is UiError.Network -> stringResource(R.string.error_generic, error.message)
                    is UiError.InvalidInput -> stringResource(R.string.error_generic, error.message)
                },
                color = MaterialTheme.colorScheme.error,
            )
            Button(onClick = onRetry) { Text(stringResource(R.string.refresh)) }
        }
    }
}

@Composable
private fun EmptyState(reason: String) {
    Card(shape = RoundedCornerShape(20.dp), modifier = Modifier.fillMaxWidth()) {
        Box(
            modifier = Modifier.padding(24.dp).fillMaxWidth(),
            contentAlignment = Alignment.Center,
        ) {
            Text(text = reason, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f))
        }
    }
}
