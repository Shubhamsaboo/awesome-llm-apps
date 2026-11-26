import { search, SearchError } from "../server/search.mjs";
import { accessError, MAX_REQUEST_BYTES } from "../server/http.mjs";
export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "Use POST." });
  }
  const denied = accessError(req.headers);
  if (denied) return res.status(denied.status).json({ error: denied.error });
  try {
    const raw =
      typeof req.body === "string" ? req.body : JSON.stringify(req.body);
    if (typeof raw !== "string")
      throw new SearchError("Invalid search request.");
    if (Buffer.byteLength(raw, "utf8") > MAX_REQUEST_BYTES)
      throw new SearchError("Document is too large.", 413);
    return res.status(200).json(await search(JSON.parse(raw)));
  } catch (error) {
    return res.status(error instanceof SearchError ? error.status : 400).json({
      error:
        error instanceof SearchError
          ? error.message
          : "Invalid search request.",
    });
  }
}
