# Build & run — Claude Limit Widget

Пошаговая инструкция как собрать APK и поставить его на свой Android-телефон.
Всё делается один раз, потом — только `./gradlew installDebug` при изменениях.

---

## 0. Что понадобится

| Что | Версия | Зачем |
|---|---|---|
| **JDK** | 17 (LTS) | Компиляция Kotlin/AGP |
| **Android Studio** | Ladybug (2024.2.1)+ или Meerkat | Легчайший путь, тянет за собой SDK |
| **Android SDK** | Platform 35, Build-Tools 35.0.0+ | Собрать APK |
| **Kotlin plugin** | 2.1.0 (идёт с Studio) | Уже в проекте |
| Телефон | Android 8.0+ (API 26) | Наш `minSdk = 26` |

Всё остальное (Gradle 8.11.1, все зависимости) Studio скачает автоматически.

---

## 1. Путь через Android Studio (рекомендую)

### 1.1 Импорт

1. **File → Open** → выбери папку `claude_limit_widget/` (не подпапку `app/`).
2. Studio увидит `settings.gradle.kts` и запустит **Trust Project** — подтверди.
3. Дождись **Gradle Sync** — первый прогон качает ~800 МБ (SDK, Kotlin, AGP, Compose).
   Полоска внизу экрана; займёт 3–15 минут в зависимости от сети.
4. Если Studio предложит **Update Gradle wrapper** — соглашайся.
   Она сгенерирует `gradle/wrapper/gradle-wrapper.jar` + `gradlew` / `gradlew.bat`.
5. Если жалуется "SDK not found" — **Tools → SDK Manager** → **SDK Platforms** →
   поставить галку у **Android 15 (API 35)** → OK → Apply.

### 1.2 Подключить телефон

**Вариант A: USB (быстрее)**
1. На телефоне: **Settings → About phone → Build number** → тапнуть 7 раз →
   появится "Developer options".
2. **Settings → Developer options** →
   - **USB debugging** → ON
   - (опционально) **Install via USB** → ON
3. Подключи USB, разреши "Allow USB debugging" в popup на телефоне.
4. В Studio вверху справа появится название телефона в дропдауне устройств.

**Вариант B: Wireless (без кабеля, Android 11+)**
1. Developer options → **Wireless debugging** → ON → **Pair device with pairing code**.
2. В Studio: **Device Manager** → **Pair Devices Using Wi-Fi** → отсканируй QR
   или вбей код с телефона.

### 1.3 Сборка и установка

- Выбери в дропдауне устройств свой телефон.
- Кнопка ▶ **Run 'app'** (Shift+F10).
- Studio соберёт debug APK, установит, запустит `MainActivity`.

---

## 2. Путь через CLI (без Studio)

Если Studio не хочешь ставить, а SDK и JDK уже есть.

### 2.1 Установи Android SDK (если ещё нет)

```bash
# macOS + Homebrew
brew install --cask android-commandlinetools

# или ручной путь: скачай command-line-tools с developer.android.com
mkdir -p "$HOME/android-sdk/cmdline-tools" && cd "$HOME/android-sdk/cmdline-tools"
unzip ~/Downloads/commandlinetools-*-*.zip
mv cmdline-tools latest

export ANDROID_HOME="$HOME/android-sdk"
export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools"

yes | sdkmanager --licenses
sdkmanager "platform-tools" "platforms;android-35" "build-tools;35.0.0"
```

Добавь `ANDROID_HOME` и `PATH` в `~/.zshrc` / `~/.bashrc` навсегда.

### 2.2 Собери wrapper и APK

```bash
cd claude_limit_widget

# Один раз — сгенерировать gradlew (нужен установленный gradle 8.11+ на PATH)
gradle wrapper --gradle-version 8.11.1

# Debug APK
./gradlew :app:assembleDebug

# APK будет здесь:
ls -lh app/build/outputs/apk/debug/app-debug.apk
```

Первый прогон 5–15 минут (качает зависимости), потом инкрементально 10–40 сек.

### 2.3 Установи на телефон

```bash
# USB подключен, "adb devices" видит телефон
adb devices

# Ставим
adb install -r app/build/outputs/apk/debug/app-debug.apk

# Или одной командой (собрать + поставить):
./gradlew :app:installDebug
```

### 2.4 Логи

```bash
# Всё от нашего приложения
adb logcat --pid=$(adb shell pidof -s dev.limitwatch)

# Только WorkManager (полезно при отладке периодического refresh)
adb logcat -s WM-WorkerWrapper:V WM-Processor:V
```

---

## 3. Первый запуск

1. Открой приложение — увидишь пустой Home tab и сообщение "No token — open Settings".
2. Перейди на **Settings**.
3. На **компьютере**, где ты залогинен в Claude Code:
   ```bash
   cat ~/.claude/.credentials.json
   ```
4. Скопируй **весь** JSON (проще всего) или только значение `accessToken`.
5. Перешли себе — Telegram Saved Messages / Signal Note to Self / любой пастебин.
6. В приложении: вставь в поле → **Save** → откинет на Home tab, автоматически
   дёрнет `/api/oauth/usage`.
7. Через 1–2 секунды увидишь три бара.

### Виджет на домашний экран

1. **Long-press** на пустое место → **Widgets** → найди **Claude Limits**.
2. Перетащи 2×2 виджет на нужную страницу. Первый раз может показать "Loading" —
   через 5–10 сек подтянет свежие данные.
3. Тап по виджету открывает приложение.

---

## 4. Что делать когда токен протух

Access token живёт часы. У нас в приложении две страховки:

1. **Автоматический refresh** — при ответе `401 Unauthorized` мы дёргаем
   `POST console.anthropic.com/v1/oauth/token` с сохранённым `refreshToken`.
2. **Если refresh не удался** (Anthropic ротирует client_id или ключ уже отозван) —
   приложение покажет "Token expired". Тогда:
   ```bash
   # На десктопе:
   claude   # любая команда — CLI сам обновит credentials.json
   cat ~/.claude/.credentials.json  # перепасти в приложение
   ```

---

## 5. Отладка

**Виджет всегда "Loading" / "Update failed"**

- Проверь **Settings → Apps → Claude Limits → App info → Battery → Unrestricted** —
  иначе Doze задушит WorkManager.
- Force-refresh вручную: тап по виджету → в приложении жми **Refresh**.

**"401 Unauthorized" в logcat**

- Токен реально отозван на стороне Anthropic. Перепастить (см. секцию 4).

**"Certificate pinning failure" / TLS-ошибки**

- У тебя корпоративный proxy? Ktor использует системный keystore, так что должен
  сработать — но если нет, добавь свой CA в `res/xml/network_security_config.xml`
  (пока такого файла нет, я его добавлю по запросу).

**"Widget preview shows old data"**

- Android кэширует preview. Удали и добавь виджет заново.

---

## 6. Release APK

Debug-подписанный APK нельзя обновить поверх release-подписанного и наоборот.

Для personal release:

```bash
# 1. Сгенерировать keystore (ОДИН РАЗ, храни в надёжном месте)
keytool -genkey -v -keystore ~/limitwatch.keystore \
  -alias limitwatch -keyalg RSA -keysize 2048 -validity 10000

# 2. Добавить signing config в app/build.gradle.kts:
#    signingConfigs { create("release") { ... storeFile = file("...") } }

# 3. Собрать
./gradlew :app:assembleRelease
ls -lh app/build/outputs/apk/release/app-release.apk
```

Или проще — оставаться на debug APK для личного использования.

---

## 7. Обновление после git pull

```bash
git pull
./gradlew :app:installDebug
```

WorkManager запомнит расписание, EncryptedSharedPreferences сохранит токен,
DataStore-кэш сохранит последний снапшот.

---

## 8. Deinstall (когда надоест)

```bash
adb uninstall dev.limitwatch
```

Или обычным путём через **Settings → Apps → Claude Limits → Uninstall**.
Всё локальное данные (токен, кэш) сотрутся вместе с приложением.

---

Если что-то не собирается — открой `logcat` и `./gradlew :app:assembleDebug --stacktrace`,
скинь мне ошибку.
