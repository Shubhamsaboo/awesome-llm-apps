# 🪡 Needle - A New Way to Find

**A new way to find.** Find what you mean, not just what matches. Describe what you are looking for in your own words, without knowing the words the page uses. Needle finds relevant passages and highlights the sentence that matters, right in the original text. Use it on webpages with the Chrome extension or explore your own text in the React app. **Powered by TypeSafe Jev.**

<img width="1379" height="685" alt="Screenshot 2026-09-20 at 12 28 10 AM" src="https://github.com/user-attachments/assets/1058589f-d686-4b3d-8873-5eb800ba35b3" />


## Features

- **Search by meaning.** Ask a question, describe an idea, or type a half-remembered detail.
- **Find the sentence that matters.** Bright green highlights the strongest sentence; pale green keeps the surrounding context visible.
- **Stay on the page.** Open the Chrome extension on a webpage and jump between matching passages.
- **Explore your own text.** Paste an article, policy, or document into the React app, or start with one of the included examples.
- **Read the original source.** Results point to existing text, with a relevance ranking and a copy button in the React app.

## How It Works

1. The extension extracts readable passages from the current webpage. The React app uses the selected document or pasted text.
2. Your query and those passages go to the local Needle backend.
3. TypeSafe Jev scores each passage for relevance and selects its strongest sentence in one evaluation request.
4. Needle maps the result back to the original text so you can read it in context.

The backend accesses `typesafe-ai/jev` through [Vercel AI Gateway's evaluation API](https://vercel.com/docs/ai-gateway/modalities/evaluation). Jev selects source sentences rather than generating an answer. Results with relevance scores of at least `0.58` are included; this is a ranking threshold, not a guarantee that every relevant passage was found.

## How to Get Started

Requires **Node.js 22.12+**, npm, and a Vercel AI Gateway account with access to `typesafe-ai/jev` and sufficient credits. Obtain an **AI Gateway API key** from the [Vercel AI Gateway dashboard](https://vercel.com/dashboard/ai-gateway). An OpenAI key or a direct TypeSafe key is not a substitute for this endpoint.

```sh
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/needle
npm ci
cp .env.example .env
```

On Windows PowerShell, use `Copy-Item .env.example .env` instead of `cp`.

Open `.env` in your editor and fill in:

```dotenv
AI_GATEWAY_API_KEY=your_vercel_ai_gateway_key
```

## Run the App

Start the React app and its backend:

```sh
npm run dev
```

Open **http://127.0.0.1:4199** in your browser. This starts the UI and backend together and creates a downloadable extension ZIP. Keep the terminal running while using the extension. `.env` is loaded at server startup; restart after changing it. The local server binds only to your computer’s loopback interface.

Never put the Gateway key in the extension, a `VITE_` environment variable, a screenshot, or a committed file. `.env` is ignored by Git. The optional `AI_GATEWAY_KEY_FILE` setting can read an existing local key file instead; ordinary users only need `.env`.

## Install the Chrome Extension

The extension is included in this repository. Install it directly in Chrome using Developer mode.

No separate extension build is needed to load the source:

1. Open `chrome://extensions` in Chrome and enable **Developer mode**.
2. Choose **Load unpacked** and select **`awesome-llm-apps/advanced_llm_apps/needle/extension/`** folder. This is the folder containing `manifest.json`. Do not select the repository root or a ZIP file.
3. Pin Needle from Chrome’s puzzle-piece menu. The settings page opens on first installation; you can also right-click the icon and choose **Options**.
4. Set **Needle server URL** to `http://127.0.0.1:4199`. Leave **Server access token** blank for the default local setup. Click **Save connection**.
5. Open a normal webpage and click the Needle icon, or press **Cmd+F** on macOS / **Ctrl+F** elsewhere. Type what you want to find.

If the shortcut is already in use, assign one at `chrome://extensions/shortcuts`.

**ZIP installation:** use **Get the extension** in the running playground, or run `npm run package:extension`. Unzip the package into a permanent folder and choose that folder in **Load unpacked**. Downloading or double-clicking a ZIP does not install it automatically. This follows Chrome’s [unpacked extension installation flow](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world#load-unpacked).

**Updates:** pull the new source (or replace the extracted ZIP files), click **Reload** on Needle’s card in `chrome://extensions`, then refresh the webpage before reopening Needle. Keep the same extension folder to retain settings.

## How to Use Needle

### On a webpage

Keep `npm run dev` running, open the webpage you want to search, and click the pinned Needle icon. Type what you mean, such as “costs beyond the advertised price” or “what happens if I cancel?” Needle searches after a short pause and highlights relevant source sentences. 

### In the React app

Open **http://127.0.0.1:4199**, choose a document from the library, and type your query. To search your own content, open the library with the top-left toggle if it is hidden, choose **Bring your own text**, enter a title and the text, then select **Start exploring**. Click a result to jump to its source.

### PDFs

Needle currently searches webpage text. Chrome's built-in PDF viewer renders PDFs inside a separate browser viewer, so Needle's page script cannot read and highlight the PDF text as ordinary webpage elements. Enabling file access does not add PDF support.

For a PDF with selectable text, copy the relevant text and use **Bring your own text** in the React app. Scanned PDFs need text extraction with OCR first. Direct PDF upload and highlights inside the PDF viewer are not implemented.

### Troubleshooting

| What you see                    | What to do                                                                                                      |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Cannot reach Needle             | Start `npm run dev` and use `http://127.0.0.1:4199` as the extension's server URL. Keep that terminal running.  |
| API key or credits error        | Check `AI_GATEWAY_API_KEY` in `.env`, your Gateway account's model access and credits, then restart the server. |
| Chrome cannot find the manifest | Choose the `extension/` folder containing `manifest.json`. If using the download, unzip it first.               |
| Changes do not appear           | Reload Needle at `chrome://extensions`, then refresh the webpage.                                               |
| No searchable text              | Try a regular webpage. Built-in PDF viewers, browser settings pages, images and scanned text are unsupported.   |

## API Key and Connection Settings

| Setting               | Where to put it                                                | Purpose                                                                 |
| --------------------- | -------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `AI_GATEWAY_API_KEY`  | Backend `.env`, or Vercel project environment variables        | Pays for and authenticates Jev inference; never goes into the extension |
| `NEEDLE_ACCESS_TOKEN` | Backend environment, then the same value in extension settings | Protects access to your backend; required on Vercel, optional locally   |
| Needle server URL     | Extension settings                                             | Your local backend or your own HTTPS deployment                         |

For the web playground on a protected backend, enter the access token in **How it works → Server access token**. This is a separate app-specific token, not the Gateway key. Whoever owns the backend’s Gateway key pays for its searches.

## Optional: Deploy to Vercel

1. Import your fork into Vercel. Set **Root Directory** to `advanced_llm_apps/needle` and Framework Preset to **Vite**. The included `vercel.json` specifies the build output and API function duration.
2. Add `AI_GATEWAY_API_KEY` and a randomly generated `NEEDLE_ACCESS_TOKEN` to the project’s environment variables. For example, generate the access token with:

   ```sh
   node -e "console.log(require('node:crypto').randomBytes(32).toString('hex'))"
   ```

3. Deploy. In extension settings, use your deployment’s HTTPS origin and the access token. Allow access to that server when Chrome prompts you.
4. Test a real search. `/api/health` confirms whether a key is configured; it does not validate the key or account credits.

The backend refuses search requests on Vercel if `NEEDLE_ACCESS_TOKEN` is missing. Use the token only for your own installation or a small trusted group. A general public service needs individual user authentication, rate limits, quotas and a billing decision; this template does not implement those. If Vercel Deployment Protection is enabled, the extension cannot complete its browser-login challenge. Use a backend reachable by the extension and retain Needle’s token check.

## Project Structure

```text
needle/
|-- src/                  React app, components, styles and example documents
|-- extension/            Chrome extension, settings, manifest and icons
|-- server/               Local server, Jev requests and sentence mapping
|-- api/                  Vercel API functions
|-- public/               App assets and generated extension download
|-- scripts/              Extension ZIP packaging
|-- tests/                Search, sentence, access and packaging checks
|-- .env.example          API key and optional settings
`-- README.md
```

## Data Handling and Limits

- Search sends **all captured passages plus your query**, not just the highlighted result, to the configured backend and AI Gateway. Use it only on pages you are comfortable sending to those services.
- The extension runs when you invoke it, rather than monitoring every page. It selects rendered paragraph/list/heading-style elements. It does not collect password/input values, browsing history, cookies, or screenshots. Text embedded within selected page elements is part of the capture.
- The backend does not intentionally persist or log page text. Hosting and model-provider policies still apply. The playground keeps up to 25 results in tab memory, and a protected-backend token in session storage. The extension stores its server URL and app access token in Chrome local storage.
- Up to **160 passages / 60,000 characters**, with at most **2,200 characters per passage**. The extension skips oversized passages and reports omissions. Very long pages may only be partially searched. Pasted text is split into bounded passages.
- Chrome system pages, the Chrome Web Store, built-in PDF viewers, scanned text, cross-origin frames and shadow-root content are unsupported. Dynamic page changes may invalidate results; search again.
- Jev access/credit errors appear explicitly. There are no fabricated fallback matches.

## Development

```sh
npm test
npm run format:check
npm run build
npm run preview
```

Stop the dev server before running preview on the same port, or choose another `PORT` in `.env`. Preview serves the production build and the real local backend.

`npm run package:extension` produces:

- `artifacts/needle-extension-v1.1.1.zip` for release attachment.
- `public/needle-extension.zip` for the app’s download link; production builds copy it to `dist/`.

ZIP packaging uses an explicit file allowlist and does not include the backend, `.env`, dependencies or development output. Build artifacts are not committed.

Before sharing a package, load it in Chrome and check the connection, search, highlights and navigation. Automated tests do not cover Chrome’s installation and permission prompts.

Licensed under the repository’s [Apache-2.0 license](../../LICENSE).
