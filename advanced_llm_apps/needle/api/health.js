import { getKey, MODEL } from "../server/search.mjs";
export default function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  res.status(200).json({ configured: Boolean(getKey()), model: MODEL });
}
