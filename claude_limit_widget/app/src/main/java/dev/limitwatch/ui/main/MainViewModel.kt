package dev.limitwatch.ui.main

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.CreationExtras
import dev.limitwatch.data.AuthStore
import dev.limitwatch.data.FetchOutcome
import dev.limitwatch.data.OauthCredentials
import dev.limitwatch.data.UsageRepository
import dev.limitwatch.data.UsageSnapshot
import dev.limitwatch.widget.WidgetPublisher
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class MainViewModel(
    private val repository: UsageRepository,
    private val authStore: AuthStore,
    private val widgetPublisher: WidgetPublisher,
) : ViewModel() {

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    val snapshot: StateFlow<UsageSnapshot?> = repository.snapshot
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    val credentials: StateFlow<OauthCredentials?> = authStore.credentials

    fun refresh() {
        if (_uiState.value.loading) return
        _uiState.value = _uiState.value.copy(loading = true, transientError = null)
        viewModelScope.launch {
            val outcome = repository.refreshNow()
            _uiState.value = when (outcome) {
                is FetchOutcome.Ok -> _uiState.value.copy(loading = false, transientError = null)
                FetchOutcome.NoCredentials -> _uiState.value.copy(loading = false, transientError = UiError.NoCredentials)
                FetchOutcome.Unauthorized -> _uiState.value.copy(loading = false, transientError = UiError.Unauthorized)
                is FetchOutcome.Failed -> _uiState.value.copy(loading = false, transientError = UiError.Network(outcome.message))
            }
            widgetPublisher.publishFrom(outcome, authStore.current() != null)
        }
    }

    fun refreshIfStale(maxAgeMs: Long = 5 * 60_000L) {
        val fetched = snapshot.value?.fetchedAtEpochMs
        if (fetched == null || System.currentTimeMillis() - fetched > maxAgeMs) refresh()
    }

    fun saveCredentials(pastedText: String, onSaved: () -> Unit) {
        viewModelScope.launch {
            val result = authStore.saveFromPastedText(pastedText)
            if (result.isSuccess) {
                onSaved()
                refresh()
            } else {
                _uiState.value = _uiState.value.copy(
                    transientError = UiError.InvalidInput(
                        result.exceptionOrNull()?.message ?: "invalid"
                    )
                )
            }
        }
    }

    fun clearCredentials() {
        authStore.clear()
        _uiState.value = UiState()
        viewModelScope.launch { widgetPublisher.publishNoToken() }
    }

    companion object {
        fun factory(context: Context): ViewModelProvider.Factory = object : ViewModelProvider.Factory {
            override fun <T : ViewModel> create(modelClass: Class<T>, extras: CreationExtras): T {
                @Suppress("UNCHECKED_CAST")
                return MainViewModel(
                    repository = UsageRepository.get(context),
                    authStore = AuthStore.get(context),
                    widgetPublisher = WidgetPublisher(context),
                ) as T
            }
        }
    }
}

data class UiState(
    val loading: Boolean = false,
    val transientError: UiError? = null,
)

sealed interface UiError {
    data object NoCredentials : UiError
    data object Unauthorized : UiError
    data class Network(val message: String) : UiError
    data class InvalidInput(val message: String) : UiError
}

