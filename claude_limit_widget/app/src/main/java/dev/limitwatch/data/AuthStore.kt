package dev.limitwatch.data

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json

/**
 * Persists the OAuth credentials in EncryptedSharedPreferences (Android Keystore-backed).
 * Kept as a Kotlin object so both UI (Activity/ViewModel scope) and the WorkManager
 * worker and Glance widget can hit the same instance without DI.
 */
class AuthStore private constructor(context: Context) {

    private val prefs: SharedPreferences = EncryptedSharedPreferences.create(
        context.applicationContext,
        PREFS_NAME,
        MasterKey.Builder(context.applicationContext)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build(),
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
    )

    private val _credentials = MutableStateFlow(readInternal())
    val credentials: StateFlow<OauthCredentials?> = _credentials.asStateFlow()

    fun current(): OauthCredentials? = _credentials.value

    /**
     * Accepts either:
     *  - a raw accessToken string (`sk-ant-oat01-…`)
     *  - the JSON object `{"accessToken": "…", "refreshToken": "…", "expiresAt": …}`
     *  - the full credentials.json shape `{"claudeAiOauth": {...}}`
     */
    fun saveFromPastedText(raw: String): Result<OauthCredentials> {
        val trimmed = raw.trim()
        if (trimmed.isEmpty()) return Result.failure(IllegalArgumentException("Empty input"))

        val parsed = when {
            trimmed.startsWith("{") -> parseJson(trimmed)
            else -> OauthCredentials(accessToken = trimmed)
        }
            ?: return Result.failure(IllegalArgumentException("Could not parse credentials"))

        if (parsed.accessToken.isBlank()) {
            return Result.failure(IllegalArgumentException("accessToken missing"))
        }

        writeInternal(parsed)
        _credentials.value = parsed
        return Result.success(parsed)
    }

    fun updateAfterRefresh(newAccessToken: String, newRefreshToken: String?, expiresAt: Long?) {
        val previous = _credentials.value ?: return
        val updated = previous.copy(
            accessToken = newAccessToken,
            refreshToken = newRefreshToken ?: previous.refreshToken,
            expiresAt = expiresAt ?: previous.expiresAt,
        )
        writeInternal(updated)
        _credentials.value = updated
    }

    fun clear() {
        prefs.edit().clear().apply()
        _credentials.value = null
    }

    private fun parseJson(raw: String): OauthCredentials? = try {
        val file = JSON.decodeFromString(CredentialsFile.serializer(), raw)
        file.claudeAiOauth ?: JSON.decodeFromString(OauthCredentials.serializer(), raw)
    } catch (_: SerializationException) {
        try {
            JSON.decodeFromString(OauthCredentials.serializer(), raw)
        } catch (_: SerializationException) {
            null
        }
    }

    private fun readInternal(): OauthCredentials? {
        val raw = prefs.getString(KEY_CREDENTIALS, null) ?: return null
        return try {
            JSON.decodeFromString(OauthCredentials.serializer(), raw)
        } catch (_: SerializationException) {
            null
        }
    }

    private fun writeInternal(credentials: OauthCredentials) {
        prefs.edit()
            .putString(KEY_CREDENTIALS, JSON.encodeToString(OauthCredentials.serializer(), credentials))
            .apply()
    }

    companion object {
        private const val PREFS_NAME = "limitwatch-secure"
        private const val KEY_CREDENTIALS = "credentials"
        private val JSON = Json { ignoreUnknownKeys = true; explicitNulls = false }

        @Volatile private var instance: AuthStore? = null

        fun get(context: Context): AuthStore = instance ?: synchronized(this) {
            instance ?: AuthStore(context).also { instance = it }
        }
    }
}
