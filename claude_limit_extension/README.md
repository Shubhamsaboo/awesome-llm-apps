# Claude Limits — browser extension

Chrome/Firefox расширение (Manifest V3), которое по клику на иконку в тулбаре
показывает текущие лимиты Claude Pro/Max: 5-часовое сессионное окно, недельные
лимиты (общий, Opus, Sonnet) и extra usage. Иконка в тулбаре показывает
процент самого нагруженного окна (badge).

Никаких токенов вставлять не надо — расширение использует **твою уже
залогиненую сессию claude.ai** через сессионную куку.

## Как это работает

Расширение делает 3–4 запроса к внутренним эндпоинтам claude.ai:

- `GET https://claude.ai/api/organizations` — определить UUID организации
- `GET https://claude.ai/api/organizations/{orgId}/usage` — лимиты
- `GET https://claude.ai/api/organizations/{orgId}/overage_spend_limit` — extra usage
- `GET https://claude.ai/api/account` — email и план (для отображения)

Все запросы уходят с флагом `credentials: "include"`, браузер сам подставляет
`sessionKey` cookie. Ничего никуда больше не отправляется — трафик идёт только
на `claude.ai`. Данные кэшируются в `browser.storage.local` (только на твоём
устройстве).

## ⚠️ Legal notice

Эндпоинты `claude.ai/api/organizations/{orgId}/usage` — **не документированные**.
Anthropic может изменить или заблокировать их без предупреждения. Расширение
делает ровно то же, что делает сам frontend claude.ai, когда показывает индикатор
лимитов — но формально это reverse engineering.

Использование "текущей сессии claude.ai" для чтения собственных данных о
лимитах — гораздо менее рискованно, чем брать OAuth-токен Claude Code и звать
`api.anthropic.com` (это был бы Consumer ToS violation). Здесь нет OAuth-токена
и нет обхода Consumer ToS: браузер просто делает `GET`, как будто ты открыл
кладку с настройками профиля.

Тем не менее — используй на свой риск.

## Установка

Полная инструкция — в [BUILD.md](./BUILD.md). Коротко:

**Chrome / Edge / Brave:**
1. `chrome://extensions` → включи **Developer mode**
2. **Load unpacked** → выбери папку `claude_limit_extension/`
3. Готово. Иконка появится в тулбаре.

**Firefox (нужен ≥ 128):**
1. `about:debugging#/runtime/this-firefox` → **Load Temporary Add-on**
2. Выбери файл `manifest.json` из `claude_limit_extension/`
3. Работает до перезапуска браузера. Для постоянной установки нужна подпись
   (см. BUILD.md).

## Использование

- Кликни по иконке в тулбаре → popup с барами использования.
- Badge на иконке показывает процент самого нагруженного окна:
  оранжевый < 70%, амбер 70–89%, красный ≥ 90%.
- Обновление автоматическое: раз в 15 минут (настраивается в Options 1–60).
- Кнопка refresh в popup — принудительно обновить.

Если ты **не залогинен** на claude.ai — popup покажет кнопку "Open claude.ai".
Логинишься там, потом снова открываешь popup — работает.

## Options

- **Auto-refresh interval** — 1–60 минут
- **Show badge on toolbar** — показывать процент прямо на иконке
- **Badge shows** — highest / session / weekly

## Ограничения

- Работает только пока сессия claude.ai активна в этом же браузере (cookie
  привязана к профилю).
- Приватные окна: не работает, если ты залогинен только в приватном окне
  (extensions по умолчанию не видят private cookies — можно включить в
  настройках расширения).
- Многоаккаунтные Google-профили: расширение видит cookie того профиля Chrome,
  в котором оно установлено. Установи расширение в каждый профиль отдельно.

## Что внутри

- Manifest V3, чистый vanilla JS (без сборщика, без npm)
- Background service worker (`chrome.alarms`-based refresh, badge painter)
- Popup (Compose-style UI без фреймворков, ~200 строк CSS)
- Options page (`chrome.storage.local`)
- Cross-browser через `browserApi` шим

Пакет — `dev.limitwatch`. Совместимо с одноимённым Android-приложением из
соседней папки `claude_limit_widget/`.

## Структура

```
claude_limit_extension/
├── manifest.json                 - MV3, host_permissions claude.ai
├── src/
│   ├── background.js             - service worker: alarms, badge, messages
│   ├── lib/
│   │   ├── browser-polyfill.js   - browserApi = browser || chrome
│   │   ├── api.js                - fetchSnapshot, ApiError
│   │   ├── storage.js            - loadSnapshot/saveSnapshot/settings
│   │   └── format.js             - untilReset, accentFor, badgePercent
│   ├── popup/
│   │   ├── popup.html
│   │   ├── popup.css
│   │   └── popup.js
│   ├── options/
│   │   ├── options.html
│   │   ├── options.css
│   │   └── options.js
│   └── icons/
│       └── icon-{16,32,48,128}.png
├── tools/
│   └── make-icons.py             - генератор PNG иконок через PIL
├── README.md
└── BUILD.md
```
