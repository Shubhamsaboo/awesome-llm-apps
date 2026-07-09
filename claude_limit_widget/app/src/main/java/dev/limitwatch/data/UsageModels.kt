package dev.limitwatch.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * Response from GET https://api.anthropic.com/api/oauth/usage.
 * Every window may be null when the account doesn't have that limit type.
 */
@Serializable
data class UsageResponse(
    @SerialName("five_hour") val fiveHour: UsageWindow? = null,
    @SerialName("seven_day") val sevenDay: UsageWindow? = null,
    @SerialName("seven_day_opus") val sevenDayOpus: UsageWindow? = null,
    @SerialName("seven_day_sonnet") val sevenDaySonnet: UsageWindow? = null,
    @SerialName("extra_usage") val extraUsage: ExtraUsage? = null,
)

@Serializable
data class UsageWindow(
    val utilization: Double,
    @SerialName("resets_at") val resetsAt: String,
)

@Serializable
data class ExtraUsage(
    @SerialName("is_enabled") val isEnabled: Boolean = false,
    @SerialName("monthly_limit") val monthlyLimit: Double? = null,
    @SerialName("used_credits") val usedCredits: Double? = null,
    val utilization: Double? = null,
)

/**
 * Structure of ~/.claude/.credentials.json produced by the Claude Code CLI.
 * We accept either the whole file or just the inner claudeAiOauth object,
 * so the outer wrapper is optional.
 */
@Serializable
data class CredentialsFile(
    val claudeAiOauth: OauthCredentials? = null,
)

@Serializable
data class OauthCredentials(
    val accessToken: String,
    val refreshToken: String? = null,
    val expiresAt: Long? = null,
    val scopes: List<String>? = null,
    val subscriptionType: String? = null,
)

/**
 * OAuth token refresh request/response for console.anthropic.com.
 */
@Serializable
data class TokenRefreshRequest(
    @SerialName("grant_type") val grantType: String = "refresh_token",
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("client_id") val clientId: String,
)

@Serializable
data class TokenRefreshResponse(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String? = null,
    @SerialName("expires_in") val expiresIn: Long? = null,
    @SerialName("token_type") val tokenType: String? = null,
)
