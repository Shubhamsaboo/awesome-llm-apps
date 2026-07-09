package dev.limitwatch.ui.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.limitwatch.R
import dev.limitwatch.ui.main.MainViewModel

@Composable
fun SettingsScreen(viewModel: MainViewModel, onSaved: () -> Unit) {
    val credentials by viewModel.credentials.collectAsState()
    var input by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(
            text = stringResource(R.string.settings_title),
            fontSize = 26.sp,
            fontWeight = FontWeight.SemiBold,
            color = MaterialTheme.colorScheme.onBackground,
        )

        LegalCard()

        Card(shape = RoundedCornerShape(20.dp), modifier = Modifier.fillMaxWidth()) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text(
                    text = if (credentials == null)
                        stringResource(R.string.token_status_missing)
                    else
                        stringResource(R.string.token_status_ok),
                    fontWeight = FontWeight.Medium,
                )
                OutlinedTextField(
                    value = input,
                    onValueChange = { input = it },
                    label = { Text(stringResource(R.string.paste_credentials)) },
                    supportingText = { Text(stringResource(R.string.paste_credentials_hint)) },
                    modifier = Modifier.fillMaxWidth().height(180.dp),
                    minLines = 4,
                    maxLines = 10,
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = {
                            val text = input
                            viewModel.saveCredentials(text) {
                                input = ""
                                onSaved()
                            }
                        },
                        enabled = input.isNotBlank(),
                    ) { Text(stringResource(R.string.save)) }

                    if (credentials != null) {
                        OutlinedButton(onClick = {
                            viewModel.clearCredentials()
                            input = ""
                        }) { Text(stringResource(R.string.clear)) }
                    }
                }
            }
        }

        HowToCard()
    }
}

@Composable
private fun LegalCard() {
    Card(shape = RoundedCornerShape(20.dp), modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(
                text = stringResource(R.string.tos_warning_title),
                fontWeight = FontWeight.Medium,
                color = MaterialTheme.colorScheme.error,
            )
            Text(
                text = stringResource(R.string.tos_warning),
                fontSize = 13.sp,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.75f),
            )
        }
    }
}

@Composable
private fun HowToCard() {
    Card(shape = RoundedCornerShape(20.dp), modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(text = "How to get the token", fontWeight = FontWeight.Medium)
            Text(
                text = "On a desktop where Claude Code is signed in, run:\n\n" +
                    "cat ~/.claude/.credentials.json\n\n" +
                    "Copy the whole JSON (or just the value of \"accessToken\") and paste above. " +
                    "Access tokens usually last a few hours; the app will use the stored refreshToken to renew automatically. " +
                    "If refresh fails, run any claude command on the desktop to re-issue and paste again.",
                fontSize = 13.sp,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.75f),
            )
            Spacer(modifier = Modifier.height(4.dp))
        }
    }
}
