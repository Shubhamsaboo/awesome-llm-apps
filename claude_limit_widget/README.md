# Claude Limit Widget (Android)

Android-приложение и home-screen виджет для мониторинга лимитов Claude Pro/Max:
5-часовое сессионное окно, недельные лимиты (общий, Opus, Sonnet) и extra usage.

Данные берутся с недокументированного эндпоинта
`GET https://api.anthropic.com/api/oauth/usage`, который использует сам Claude Code.
Тот же самый ответ, что показывается в status line у Claude Code.

## ⚠️ Legal notice — прочитай перед использованием

В феврале 2026 Anthropic обновил Consumer Terms of Service: OAuth-токены,
получаемые в Claude Free/Pro/Max, предназначены **исключительно** для использования
в Claude Code и claude.ai. Использование этих токенов в любом другом продукте
(включая это приложение) формально нарушает Consumer ToS.

Это приложение читает **только твои собственные данные об использовании** и не
делает инференс. Многие публичные проекты (например,
[ohugonnot/claude-code-statusline](https://github.com/ohugonnot/claude-code-statusline))
используют тот же эндпоинт для тех же целей. Но помни: гарантий стабильности
эндпоинта нет, и Anthropic вправе заблокировать твой аккаунт.

Используй на свой страх и риск.

## Что показывает

- **Session · 5h** — процент 5-часового окна и время до сброса
- **Weekly · 7d** — общий недельный лимит
- **Weekly · Opus** — 7-дневный лимит Opus (если применим)
- **Weekly · Sonnet** — 7-дневный лимит Sonnet (если применим)
- **Extra usage** — балансы платного превышения (если включено)

Виджет 2×2 показывает три главные метрики: session, weekly, Opus/Sonnet.

## Установка

Полная пошаговая инструкция — в [BUILD.md](./BUILD.md). Она покрывает
Android Studio path, чистый CLI, установку по USB и Wireless, отладку.

Короткая версия:

```bash
# 1. Открой claude_limit_widget/ в Android Studio → Sync.
# 2. Подключи телефон (Developer options → USB debugging).
# 3. ▶ Run 'app'
```

Или CLI:

```bash
cd claude_limit_widget
gradle wrapper --gradle-version 8.11.1
./gradlew :app:installDebug
```

## Как получить токен

1. На компьютере, где ты залогинен в Claude Code:

   ```bash
   cat ~/.claude/.credentials.json
   ```

2. Скопируй весь JSON (или только значение поля `accessToken`).
3. В приложении: вкладка **Settings** → вставь в поле → **Save**.
4. Приложение сохранит токен в `EncryptedSharedPreferences` (Android Keystore) и
   попытается автоматически обновлять его через `refreshToken`.

Access token обычно живёт несколько часов. Если auto-refresh не удался (например,
Anthropic ротировал client_id), просто повтори шаги 1–3: запустишь `claude`
на десктопе, он обновит `credentials.json`, ты перепастишь.

## Что внутри

- **Kotlin 2.1** + **Jetpack Compose** — UI
- **Glance 1.1** — home-screen виджет
- **Ktor 3.0** + **kotlinx.serialization** — HTTP-клиент
- **WorkManager** — периодический background refresh (раз в 15 мин)
- **DataStore** — кэш последнего снапшота
- **EncryptedSharedPreferences** — хранение OAuth токенов
- **Material3 dynamic color** — тема подстраивается под систему

Пакет: `dev.limitwatch`. Namespace тот же, `applicationId` тот же.

## Структура

```
claude_limit_widget/
├── app/
│   └── src/main/
│       ├── java/dev/limitwatch/
│       │   ├── LimitWatchApp.kt          — Application, warm-up singletons
│       │   ├── MainActivity.kt           — единственная Activity, tabs
│       │   ├── data/
│       │   │   ├── UsageModels.kt        — data-классы ответа /api/oauth/usage
│       │   │   ├── UsageApi.kt           — Ktor client, refresh flow
│       │   │   ├── AuthStore.kt          — encrypted storage OAuth
│       │   │   └── UsageRepository.kt    — glue, DataStore-кэш, retry-on-401
│       │   ├── ui/
│       │   │   ├── theme/                — Material3 тема, палитра
│       │   │   ├── main/                 — MainScreen, MainViewModel, TimeFormat
│       │   │   └── settings/             — SettingsScreen (paste-token UI)
│       │   ├── widget/                   — Glance widget + Receiver + state store
│       │   └── work/                     — WorkManager RefreshWorker/Scheduler
│       └── res/                          — strings, colors, xml, drawable
├── build.gradle.kts + settings.gradle.kts + libs.versions.toml
└── README.md
```

## Endpoints

- Usage: `GET https://api.anthropic.com/api/oauth/usage`
  - Headers: `Authorization: Bearer <access_token>`, `anthropic-beta: oauth-2025-04-20`
- Refresh: `POST https://console.anthropic.com/v1/oauth/token`
  - Body: `{"grant_type":"refresh_token","refresh_token":"…","client_id":"9d1c250a-e61b-44d9-88ed-5944d1962f5e"}`

Client ID (`9d1c250a-…`) — публично известный OAuth client Claude Code.

## Ограничения текущей версии

- Auto-refresh access token может не работать, если Anthropic изменит client_id
  или flow. Fallback — ручной re-paste.
- Обновление виджета не может быть чаще одного раза в 15 минут (Android policy).
  В Doze-режиме может быть реже.
- Мы не показываем `subscriptionType` / `rateLimitTier` — только числа. Легко
  добавить, если понадобится.
- Нет OAuth-flow из самого приложения (PKCE в мобильный клиент — отдельный
  большой кусок). Пока только paste-from-desktop.

## Возможные расширения

- Уведомление при 90%+ на любом окне.
- Отдельный размер виджета 4×2 с extra_usage и подробным reset countdown.
- Диаграмма истории использования (нужен свой персистентный store).
- Автоматический OAuth login с PKCE (требует, чтобы наш `client_id` был принят
  Anthropic — сейчас нет).
