# Ripple - Change One Thing, Find What Else Needs to Change

**Change one thing and find everything else that needs to change, with suggested fixes.** Ripple catches related inconsistencies as you edit, right inside your Google Doc. Change a date, a plan, or a requirement, and see which other sentences need attention. Fast, near real-time checks highlight affected text, suggest a fix, and let you apply it without leaving the document. **Powered by TypeSafe Jev and Gemini 3.5 Flash-Lite.**

## Features

- **Follow the impact of an edit.** Change a fact and find statements elsewhere in the document that no longer agree with it.
- **See exactly what needs attention.** Numbered margin markers highlight affected sentences in the original document.
- **Review suggested fixes.** Compare the current wording with a proposed replacement, or remove a sentence that no longer belongs.
- **Stay in your writing flow.** Checks start automatically after a short pause in typing. Highlights appear first, followed by suggested fixes.
- **Keep control of your document.** Edit a suggestion, apply it, or keep the original. Nothing changes without your click.
- **Work through fixes without starting over.** Applying a correction keeps the next suggestion open and preserves the remaining review.

## How It Works

1. Enable Ripple in a Google Doc to capture its current wording as a starting point.
2. Edit a fact. After you pause, the extension sends the before-and-after wording and the active tab's sentences to the local Ripple backend.
3. TypeSafe Jev identifies sentences that conflict with the change. Ripple marks them in the document.
4. Gemini drafts a correction for each flagged sentence, using the changed fact and nearby context. It can suggest a replacement, a removal, keeping the original, or asking for missing information.
5. Review a suggestion and click **Apply change** or **Remove sentence**. Ripple confirms the edit in Google Docs and moves to the next finding.

The backend calls `jev-latest` through the [TypeSafe API](https://docs.typesafe.ai/introduction/quickstart) and `gemini-3.5-flash-lite` through the Google Gemini API. Checks begin roughly two seconds after you stop typing; completion time depends on the document and model responses. Jev finds likely inconsistencies, so review the suggestions rather than treating them as a guarantee that every dependency was found.

## How to Get Started

Requires **Node.js 22+**, npm, a **TypeSafe API key** with access to Jev, and a **Gemini API key** with access to `gemini-3.5-flash-lite`.

```sh
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/ripple
cp .env.example .env
```

On Windows PowerShell, use `Copy-Item .env.example .env` instead of `cp`. Ripple has no npm dependencies, so no install command is needed.

Open `.env` in your editor and fill in:

```dotenv
TYPESAFE_API_KEY=your_typesafe_api_key
GEMINI_API_KEY=your_gemini_api_key
```

## Run the App

Start Ripple's local backend:

```sh
npm start
```

The backend listens at **http://127.0.0.1:4212**. Keep the terminal running while using the extension. Your workspace is the Google Doc itself; there is no separate editor to open.

Keep both API keys in the backend's `.env` file. They do not go into the extension. `.env` is ignored by Git and excluded from the extension package. The backend reads it on each request, so saving an updated key takes effect without restarting.

## Install the Chrome Extension

The extension is included in this project. Install it directly in Chrome or Brave using Developer mode.

No separate extension build is needed to load the source:

1. Open `chrome://extensions` in Chrome or `brave://extensions` in Brave and enable **Developer mode**.
2. Choose **Load unpacked** and select **`awesome-llm-apps/advanced_llm_apps/ripple/extension/`**. This is the folder containing `manifest.json`. Do not select the project root or a ZIP file.
3. Pin Ripple from the browser's puzzle-piece menu.
4. Open a Google Doc you can edit and refresh it once so Ripple loads alongside the editor.
5. Click Ripple's status chip, then **Enable for this Doc**. You can also enable it from the pinned extension icon.

**ZIP installation:** run `npm run package`, then unzip `dist/ripple-extension.zip` into a permanent folder. Choose the extracted `ripple-extension` folder in **Load unpacked**. Downloading or double-clicking the ZIP does not install it automatically. Packaging uses the `zip` command; loading `extension/` directly does not require it.

**Updates:** update the source or replace the extracted ZIP files, click the circular **Reload** icon on Ripple's card in the browser's extensions page, then refresh the Google Doc. Both steps are required: refreshing only the Doc can leave old editor scripts running alongside a newer UI. Keep the same extension folder; no reinstall is needed.

## How to Use Ripple

### In a Google Doc

Keep `npm start` running and enable Ripple **before** making the edit you want it to track. Change a fact, then continue writing. When you pause, Ripple checks related sentences in the active document tab.

Click a numbered margin marker or **Review changes** to inspect a finding. The card shows the current wording and suggested fix. Expand **Why this sentence?** to see the edit that triggered it.

- **Apply change** replaces the sentence. You can edit the suggested wording first.
- **Remove sentence** deletes an obsolete sentence without adding a replacement.
- **Keep original** dismisses the finding without changing the document.
- **Next suggestion** lets you move through the review without applying anything.

After an applied correction, the next suggestion stays open. Once all visible findings are resolved, the card closes. Use Google Docs' normal **Undo** to reverse an edit. Manual edits and Undo trigger a fresh check; confirmed Ripple corrections preserve the current review.

Open the settings button beside the status chip to pause Ripple or restore kept findings. Pause and resume when you want to capture a fresh starting point.

### Try an example

Put these sentences in a Google Doc before enabling Ripple:

> Attendance is online.
>
> Participants can attend from anywhere in the world.
>
> We will email the Zoom link one day before the workshop.
>
> Bring a laptop for the exercises.
>
> Last year's workshop was online.

Enable Ripple, then change **Attendance is online.** to **Attendance is in person only.**

The remote-attendance and Zoom-link sentences should be flagged for review. Ripple can suggest removing obsolete joining instructions or rewriting them for in-person attendance. The laptop requirement and historical description should remain unaffected. Model results can vary.

### Troubleshooting

| What you see                                      | What to do                                                                                                                                                                 |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cannot connect to Ripple                          | Start `npm start` and keep the terminal running. The extension uses `http://127.0.0.1:4212`.                                                                               |
| API key or model-access error                     | Check the corresponding key in `.env` and your provider account's model access and credits.                                                                                |
| Chrome cannot find the manifest                   | Select `extension/`, the folder containing `manifest.json`. Unzip downloaded packages first.                                                                               |
| Updates do not appear, or Apply uses the old flow | Reload Ripple on the browser's extensions page, then refresh the Doc. A page refresh alone is not enough.                                                                  |
| No findings after enabling                        | Enable Ripple before changing the source fact. It cannot recover the wording from before it was enabled.                                                                   |
| An edit could not be confirmed                    | Check the actual Doc before retrying. Docs can occasionally ignore the first input after navigation. For replacements, use **Copy suggestion** to edit manually if needed. |
| Doc access unavailable                            | Refresh the Doc. If the error persists, the current Google Docs editor may not support Ripple's adapter.                                                                   |

## API Key and Connection Settings

| Setting            | Where to put it                                                             | Purpose                                                     |
| ------------------ | --------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `TYPESAFE_API_KEY` | Backend `.env` or server environment                                        | Authenticates Jev checks through the direct TypeSafe API    |
| `GEMINI_API_KEY`   | Backend `.env` or server environment                                        | Authenticates suggested fixes through the direct Gemini API |
| `GOOGLE_API_KEY`   | Backend `.env` or server environment, as an alternative to `GEMINI_API_KEY` | Uses an existing Google API key for suggestions             |
| Backend address    | Fixed at `http://127.0.0.1:4212`                                            | Connects the extension to the backend on your computer      |

Ordinary setup only needs the two keys in `.env`. Whoever owns those keys pays for model usage. The extension has no API-key field and does not receive either key. This version runs locally and does not include a hosted deployment or a configurable remote backend.

## Project Structure

```text
ripple/
|-- extension/            Chrome extension, Docs adapter, review UI and icons
|-- server.mjs            Local backend and request handling
|-- jev.mjs               TypeSafe Jev checks and response validation
|-- suggestions.mjs       Gemini suggested fixes and response validation
|-- config.mjs            Server-side API key loading
|-- scripts/              Live suggestion evaluation with synthetic examples
|-- tests/                Change tracking, editing, review and API checks
|-- package.mjs           Extension ZIP packaging
|-- package.json          Run, test and packaging commands
|-- .env.example          API key settings
`-- README.md
```

## Data Handling and Limits

- Checks send the **source edit and captured sentences from the active document tab** to TypeSafe. Suggested fixes send flagged sentences, the source edit, and nearby context to Google. Enable Ripple only on documents you are comfortable sending to those services.
- Both API keys stay in the local backend. The backend does not intentionally save or log document text. Model-provider policies still apply.
- Starting text, findings, and drafts are held in tab memory and reset on refresh. Only the per-document enabled preference is stored locally.
- Up to **120 sentences / 30,000 characters** in the active tab, with a maximum of **2,500 characters per sentence**. Request metadata can reduce the usable limit. Oversized checks report an error.
- Up to **four source edits** can be tracked in one session. Pure insertions or deletions without both previous and replacement wording are not checked. Pause and resume after a large rewrite to capture a fresh starting point.
- Images, drawings, footnotes, comments, and other document tabs are not checked. Collaborative edits may be detected without reliable attribution to an author.
- Ripple uses extension-facing Google Docs interfaces that Google can change. Plain-text fixes can affect inline formatting; complex formatting, tables, and Suggesting mode need broader validation. Sentence removal preserves paragraph breaks and can leave an empty paragraph.

## Development

```sh
npm test
npm run package
```

`npm run package` produces:

- `dist/ripple-extension/` for unpacked installation.
- `dist/ripple-extension.zip` for sharing.

Packaging copies only `extension/`, excluding the backend, `.env`, and development files. Generated packages are ignored by Git.

To evaluate suggestion quality against synthetic examples using the real Gemini API:

```sh
node scripts/evaluate-suggestions.mjs
```

This command uses the configured Gemini key and incurs normal API usage. Before sharing an updated package, load it in the browser and check detection, suggestions, Apply, navigation, and Undo in a disposable Doc.

Licensed under the repository's [Apache-2.0 license](../../LICENSE).
