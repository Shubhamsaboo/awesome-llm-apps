# Build & install — Claude Limits browser extension

Расширение написано на vanilla JS без сборщика. Никакой `npm install`,
никакого bundler'а — папку можно загрузить в браузер как есть.

---

## Chrome / Edge / Brave / Arc (unpacked)

1. Открой `chrome://extensions` (в Edge — `edge://extensions`).
2. Включи тумблер **Developer mode** справа сверху.
3. Нажми **Load unpacked** → выбери папку `claude_limit_extension/`
   (ту, где лежит `manifest.json`).
4. Разреши доступ к claude.ai если попросит.
5. Закрепи иконку в тулбаре: паззл справа от адресной строки → пин у "Claude Limits".

Обновление кода: жми **Reload** на карточке расширения — при этом
service worker и popup перезагрузятся, storage сохранится.

---

## Firefox (temporary)

Быстрый способ, но живёт до перезапуска Firefox.

1. Открой `about:debugging#/runtime/this-firefox`.
2. **Load Temporary Add-on…** → выбери `claude_limit_extension/manifest.json`.
3. Расширение подгружено. Иконка появится в тулбаре — перетащи через
   `Customize Toolbar` если её не видно.

Требуется **Firefox ≥ 128** — MV3 service_worker поддержан с этой версии.

Обновление: **Reload** в about:debugging.

---

## Firefox (permanent, self-signed)

Firefox требует подписи для постоянной установки. Есть два пути.

### A. Через `web-ext sign` (нужен AMO account)

```bash
# Один раз
npm install --global web-ext

cd claude_limit_extension
web-ext lint
web-ext sign \
  --api-key=$(cat ~/.amo-jwt-issuer) \
  --api-secret=$(cat ~/.amo-jwt-secret) \
  --channel=unlisted
```

AMO выдаст подписанный `.xpi` — двойной клик → **Install**.

Ключи получаются на https://addons.mozilla.org/developers/addon/api/key/.

### B. Firefox Developer Edition / Nightly / ESR-unbranded

В этих сборках можно установить неподписанное расширение навсегда:

1. `about:config` → `xpinstall.signatures.required` → `false`.
2. `web-ext build` → получишь `.zip`.
3. Переименуй в `.xpi`, открой в Firefox → **Install**.

Обычный релизный Firefox это не позволяет.

---

## Опциональный dev-loop через `web-ext`

`web-ext` даёт удобный watch-режим — правишь код, браузер сам подхватывает.

```bash
npm install --global web-ext

cd claude_limit_extension

# Firefox: запускает Firefox с уже загруженным расширением, hot-reload
web-ext run

# Chrome: генерирует ZIP для загрузки
web-ext build --overwrite-dest
```

---

## Regenerate icons

Если хочешь другой дизайн иконки:

```bash
cd claude_limit_extension
python3 -m pip install pillow  # один раз
python3 tools/make-icons.py --out src/icons
```

Скрипт рисует rounded gradient orange → dark orange + белая C + три
tick-мет "gauge" снизу. Правь `tools/make-icons.py` — цвета вверху файла.

---

## Как убедиться что работает

1. Открой claude.ai в текущем браузере, залогинься.
2. Кликни на иконку расширения в тулбаре.
3. Должен показаться popup с барами. На иконке появится badge с процентом.

Если увидишь **"Not signed in to claude.ai"** — залогинься заново. Кнопка
внутри popup откроет `claude.ai/login`.

---

## Debug

**Popup**
- Chrome: правый клик по иконке расширения → **Inspect popup**.
- Firefox: правый клик → **Inspect** → откроется DevTools popup'а.

**Service worker (background)**
- Chrome: `chrome://extensions` → карточка расширения → **service worker (Inspect views)**.
- Firefox: `about:debugging#/runtime/this-firefox` → **Inspect** возле расширения.

**Смотреть сетевые запросы**
- Из DevTools service worker'а, вкладка Network — увидишь запросы на claude.ai.
- Полезно чтобы диагностировать 401 (сессия истекла) vs 5xx (что-то сломалось на claude.ai).

**Storage**
- Chrome DevTools → **Application** → **Storage** → **Extension** → `browser.storage.local`.
- Ключи `snapshot` (последний снапшот) и `settings` (настройки).

---

## Удалить

- Chrome: `chrome://extensions` → **Remove**.
- Firefox: `about:addons` → **Remove**, или в about:debugging → **Remove**.

Storage удалится вместе с расширением.

---

## Совместимые браузеры

| Браузер | Работает? |
|---|---|
| Chrome ≥ 121 | ✅ |
| Edge ≥ 121 | ✅ |
| Brave ≥ 1.60 | ✅ |
| Arc / Opera | ✅ (Chromium-based) |
| Firefox ≥ 128 | ✅ |
| Firefox ESR 115 | ❌ (нет MV3 service_worker) |
| Safari | ❌ (нужен Xcode-конвертер, не поддерживается) |

---

Если что-то не работает — открой DevTools service worker'а, смотри
консольные ошибки, шли мне.
