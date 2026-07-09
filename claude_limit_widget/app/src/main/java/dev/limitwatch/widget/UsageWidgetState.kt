package dev.limitwatch.widget

import android.content.Context
import androidx.datastore.core.CorruptionException
import androidx.datastore.core.DataStore
import androidx.datastore.core.DataStoreFactory
import androidx.datastore.core.Serializer
import androidx.datastore.dataStoreFile
import androidx.glance.state.GlanceStateDefinition
import dev.limitwatch.data.UsageResponse
import dev.limitwatch.data.UsageSnapshot
import kotlinx.serialization.SerializationException
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import java.io.File
import java.io.InputStream
import java.io.OutputStream

sealed interface WidgetState {
    data object Loading : WidgetState
    data object NoToken : WidgetState
    data object Error : WidgetState
    data class Ready(val snapshot: UsageSnapshot) : WidgetState
}

@Serializable
private data class PersistedState(
    val kind: String,
    val usage: UsageResponse? = null,
    val fetchedAtEpochMs: Long? = null,
)

/**
 * Glance stores widget state per-widget in a DataStore file. We use Kotlinx Serialization
 * to persist [WidgetState] so the widget can render its last-known snapshot on cold start
 * without hitting the network.
 */
object UsageWidgetStateDefinition : GlanceStateDefinition<WidgetState> {

    private val JSON = Json { ignoreUnknownKeys = true; explicitNulls = false }

    override suspend fun getDataStore(context: Context, fileKey: String): DataStore<WidgetState> {
        return DataStoreFactory.create(
            serializer = WidgetStateSerializer,
            produceFile = { context.dataStoreFile("widget_state_$fileKey") },
        )
    }

    override fun getLocation(context: Context, fileKey: String): File =
        context.dataStoreFile("widget_state_$fileKey")

    private object WidgetStateSerializer : Serializer<WidgetState> {
        override val defaultValue: WidgetState = WidgetState.Loading

        override suspend fun readFrom(input: InputStream): WidgetState {
            return try {
                val bytes = input.readBytes()
                if (bytes.isEmpty()) return defaultValue
                val persisted = JSON.decodeFromString(PersistedState.serializer(), bytes.decodeToString())
                when (persisted.kind) {
                    "ready" -> {
                        val usage = persisted.usage ?: return WidgetState.Error
                        val fetchedAt = persisted.fetchedAtEpochMs ?: return WidgetState.Error
                        WidgetState.Ready(UsageSnapshot(usage, fetchedAt))
                    }
                    "loading" -> WidgetState.Loading
                    "no_token" -> WidgetState.NoToken
                    "error" -> WidgetState.Error
                    else -> defaultValue
                }
            } catch (_: SerializationException) {
                throw CorruptionException("Corrupt widget state")
            }
        }

        override suspend fun writeTo(t: WidgetState, output: OutputStream) {
            val persisted = when (t) {
                WidgetState.Loading -> PersistedState(kind = "loading")
                WidgetState.NoToken -> PersistedState(kind = "no_token")
                WidgetState.Error -> PersistedState(kind = "error")
                is WidgetState.Ready -> PersistedState(
                    kind = "ready",
                    usage = t.snapshot.usage,
                    fetchedAtEpochMs = t.snapshot.fetchedAtEpochMs,
                )
            }
            output.write(JSON.encodeToString(PersistedState.serializer(), persisted).encodeToByteArray())
        }
    }
}
