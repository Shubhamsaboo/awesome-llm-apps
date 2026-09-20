# Sharing Needle from the Repository

Needle ships as source in `advanced_llm_apps/needle/`, including the React app, backend and Chrome extension. Users follow the [README](../README.md) to add their own Gateway key, start the app and load the extension in Chrome Developer mode. Distribution does not depend on a Chrome Web Store listing or review.

## What Users Install

| Download                           | Contents                                        | Installation                                                                       |
| ---------------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------- |
| Repository clone or source ZIP     | React app, backend, extension and documentation | Run the README setup, then load `extension/` in Chrome                             |
| Extension ZIP from the running app | Manifest, scripts, settings and icons           | Unzip into a permanent folder and select it with Chrome's **Load unpacked** button |

The extension ZIP needs a running Needle backend. Downloading it does not install Node.js, configure an API key or start a server. Users who start from the repo have everything they need to run that backend locally.

## Credentials

Users put their Vercel AI Gateway key in their own backend's `.env` file. The extension stores the backend URL and an optional Needle access token. Local setup uses `http://127.0.0.1:4199` with a blank access token. Each user pays for searches through their own Gateway account.

For an optional Vercel deployment, set `AI_GATEWAY_API_KEY` and `NEEDLE_ACCESS_TOKEN` in the project's environment variables. Only the Needle token goes into extension settings. Follow the README deployment steps.

## Package and Verify

1. Run `npm ci`, `npm test`, `npm run format:check`, and `npm run build` from the Needle directory.
2. The build creates `artifacts/needle-extension-v1.1.1.zip` and `public/needle-extension.zip`. The latter is the React app's download.
3. Check that the ZIP has `manifest.json` at its root and includes the icons and scripts. Packaging uses an explicit allowlist to exclude keys, the backend and dependencies.
4. Before sharing an updated package, load the extracted folder in a fresh Chrome installation and check settings, backend connection, semantic search, highlights, navigation and closing. Browser fixtures and unit tests do not replace this installation check.
5. Commit source and documentation. Keep `.env`, `node_modules`, `dist`, and generated ZIPs out of Git. Users can generate the ZIP themselves or load `extension/` directly.

The CI workflow runs tests, formatting and a build, then retains the extension ZIP as a workflow artifact. It does not publish the extension or deploy a backend.

## Update an Existing Installation

Pull the latest repository changes, run `npm ci`, and restart the server. At `chrome://extensions`, click **Reload** on Needle, then refresh the webpage. If using the ZIP, replace the files in the same extracted folder before reloading. Keep that folder in place because Chrome loads the extension from it.
