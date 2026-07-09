package dev.limitwatch.data

import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.engine.okhttp.OkHttp
import io.ktor.client.plugins.HttpTimeout
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.plugins.defaultRequest
import io.ktor.client.request.get
import io.ktor.client.request.header
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.HttpResponse
import io.ktor.http.ContentType
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpStatusCode
import io.ktor.http.contentType
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.json.Json

class UsageApi(private val client: HttpClient = defaultClient()) {

    suspend fun fetchUsage(accessToken: String): ApiResult<UsageResponse> = runCatchingApi {
        val response: HttpResponse = client.get(USAGE_URL) {
            header(HttpHeaders.Authorization, "Bearer $accessToken")
            header("anthropic-beta", ANTHROPIC_BETA)
            header(HttpHeaders.Accept, ContentType.Application.Json.toString())
        }
        interpret(response) { it.body<UsageResponse>() }
    }

    suspend fun refresh(refreshToken: String): ApiResult<TokenRefreshResponse> = runCatchingApi {
        val response: HttpResponse = client.post(TOKEN_URL) {
            contentType(ContentType.Application.Json)
            setBody(
                TokenRefreshRequest(
                    refreshToken = refreshToken,
                    clientId = CLAUDE_CODE_CLIENT_ID,
                )
            )
        }
        interpret(response) { it.body<TokenRefreshResponse>() }
    }

    private suspend inline fun <T> runCatchingApi(block: () -> ApiResult<T>): ApiResult<T> =
        try {
            block()
        } catch (t: Throwable) {
            ApiResult.NetworkError(t.message ?: t::class.simpleName ?: "Network error")
        }

    private suspend inline fun <T> interpret(
        response: HttpResponse,
        crossinline decode: suspend (HttpResponse) -> T,
    ): ApiResult<T> = when (response.status) {
        HttpStatusCode.OK -> ApiResult.Success(decode(response))
        HttpStatusCode.Unauthorized, HttpStatusCode.Forbidden -> ApiResult.Unauthorized
        HttpStatusCode.TooManyRequests -> ApiResult.RateLimited
        else -> ApiResult.HttpError(response.status.value, response.status.description)
    }

    companion object {
        private const val USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
        private const val TOKEN_URL = "https://console.anthropic.com/v1/oauth/token"
        private const val ANTHROPIC_BETA = "oauth-2025-04-20"
        // Public Claude Code / Console OAuth client id, hard-coded in the CLI.
        // Source: reverse-engineered from Claude Code, see Moltis docs and multiple community write-ups.
        private const val CLAUDE_CODE_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"

        fun defaultClient(): HttpClient = HttpClient(OkHttp) {
            install(ContentNegotiation) {
                json(
                    Json {
                        ignoreUnknownKeys = true
                        explicitNulls = false
                        isLenient = true
                    }
                )
            }
            install(HttpTimeout) {
                requestTimeoutMillis = 15_000
                connectTimeoutMillis = 10_000
                socketTimeoutMillis = 15_000
            }
            defaultRequest {
                header(HttpHeaders.UserAgent, "ClaudeLimitWidget/0.1 (Android)")
            }
            expectSuccess = false
        }
    }
}

sealed interface ApiResult<out T> {
    data class Success<T>(val value: T) : ApiResult<T>
    data object Unauthorized : ApiResult<Nothing>
    data object RateLimited : ApiResult<Nothing>
    data class HttpError(val code: Int, val message: String) : ApiResult<Nothing>
    data class NetworkError(val message: String) : ApiResult<Nothing>
}
