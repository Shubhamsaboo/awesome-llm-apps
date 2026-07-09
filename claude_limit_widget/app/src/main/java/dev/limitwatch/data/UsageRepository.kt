package dev.limitwatch.data

import android.content.Context
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.json.Json

private val Context.snapshotStore by preferencesDataStore("usage-snapshot")

/**
 * Single source of truth used by the ViewModel, the widget, and the background worker.
 * - Reads credentials from AuthStore.
 * - Talks to UsageApi; auto-refreshes the access token once on 401 if we have a refresh token.
 * - Persists the last successful response so the UI and widget can render instantly on cold start.
 */
class UsageRepository(
    private val context: Context,
    private val authStore: AuthStore = AuthStore.get(context),
    private val api: UsageApi = UsageApi(),
) {

    private val refreshMutex = Mutex()

    val snapshot: Flow<UsageSnapshot?> =
        context.snapshotStore.data.map { prefs -> readSnapshot(prefs) }

    suspend fun currentSnapshot(): UsageSnapshot? = readSnapshot(context.snapshotStore.data.first())

    suspend fun refreshNow(): FetchOutcome {
        val creds = authStore.current() ?: return FetchOutcome.NoCredentials

        val first = api.fetchUsage(creds.accessToken)
        val effective = if (first is ApiResult.Unauthorized) {
            when (val refreshed = tryRefreshAccessToken(creds)) {
                is RefreshOutcome.RefreshedTo -> api.fetchUsage(refreshed.accessToken)
                RefreshOutcome.NoRefreshToken, RefreshOutcome.Failed -> first
            }
        } else {
            first
        }

        return when (effective) {
            is ApiResult.Success -> {
                val snapshot = UsageSnapshot(
                    usage = effective.value,
                    fetchedAtEpochMs = System.currentTimeMillis(),
                )
                writeSnapshot(snapshot)
                FetchOutcome.Ok(snapshot)
            }
            ApiResult.Unauthorized -> FetchOutcome.Unauthorized
            ApiResult.RateLimited -> FetchOutcome.Failed("rate limited")
            is ApiResult.HttpError -> FetchOutcome.Failed("HTTP ${effective.code} ${effective.message}")
            is ApiResult.NetworkError -> FetchOutcome.Failed(effective.message)
        }
    }

    private suspend fun tryRefreshAccessToken(creds: OauthCredentials): RefreshOutcome =
        refreshMutex.withLock {
            val currentAfterLock = authStore.current() ?: return@withLock RefreshOutcome.Failed
            if (currentAfterLock.accessToken != creds.accessToken) {
                return@withLock RefreshOutcome.RefreshedTo(currentAfterLock.accessToken)
            }
            val refreshToken = currentAfterLock.refreshToken
                ?: return@withLock RefreshOutcome.NoRefreshToken

            when (val result = api.refresh(refreshToken)) {
                is ApiResult.Success -> {
                    val expiresAt = result.value.expiresIn
                        ?.let { System.currentTimeMillis() + it * 1000 }
                    authStore.updateAfterRefresh(
                        newAccessToken = result.value.accessToken,
                        newRefreshToken = result.value.refreshToken,
                        expiresAt = expiresAt,
                    )
                    RefreshOutcome.RefreshedTo(result.value.accessToken)
                }
                else -> RefreshOutcome.Failed
            }
        }

    private suspend fun writeSnapshot(snapshot: UsageSnapshot) {
        context.snapshotStore.edit { prefs ->
            prefs[KEY_JSON] = JSON.encodeToString(UsageResponse.serializer(), snapshot.usage)
            prefs[KEY_FETCHED_AT] = snapshot.fetchedAtEpochMs
        }
    }

    private fun readSnapshot(prefs: Preferences): UsageSnapshot? {
        val json = prefs[KEY_JSON] ?: return null
        val fetchedAt = prefs[KEY_FETCHED_AT] ?: return null
        return runCatching {
            UsageSnapshot(
                usage = JSON.decodeFromString(UsageResponse.serializer(), json),
                fetchedAtEpochMs = fetchedAt,
            )
        }.getOrNull()
    }

    companion object {
        private val KEY_JSON = stringPreferencesKey("usage_json")
        private val KEY_FETCHED_AT = longPreferencesKey("fetched_at")
        private val JSON = Json { ignoreUnknownKeys = true; explicitNulls = false }

        @Volatile private var instance: UsageRepository? = null

        fun get(context: Context): UsageRepository = instance ?: synchronized(this) {
            instance ?: UsageRepository(context.applicationContext).also { instance = it }
        }
    }
}

data class UsageSnapshot(
    val usage: UsageResponse,
    val fetchedAtEpochMs: Long,
)

sealed interface FetchOutcome {
    data class Ok(val snapshot: UsageSnapshot) : FetchOutcome
    data object NoCredentials : FetchOutcome
    data object Unauthorized : FetchOutcome
    data class Failed(val message: String) : FetchOutcome
}

private sealed interface RefreshOutcome {
    data class RefreshedTo(val accessToken: String) : RefreshOutcome
    data object NoRefreshToken : RefreshOutcome
    data object Failed : RefreshOutcome
}
