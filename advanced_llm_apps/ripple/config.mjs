import { readFileSync, existsSync } from "node:fs";
import { parseEnv } from "node:util";

const localEnv = new URL(".env", import.meta.url);

// Read on each request so saving the local key does not require a restart.
export function getApiKey() {
  const fromEnvironment = process.env.TYPESAFE_API_KEY?.trim();
  if (fromEnvironment) return fromEnvironment;
  if (!existsSync(localEnv)) return "";
  return (
    parseEnv(readFileSync(localEnv, "utf8")).TYPESAFE_API_KEY?.trim() || ""
  );
}

export function getGeminiKey() {
  const env = existsSync(localEnv)
    ? parseEnv(readFileSync(localEnv, "utf8"))
    : {};
  const key =
    process.env.GEMINI_API_KEY ||
    process.env.GOOGLE_API_KEY ||
    env.GEMINI_API_KEY ||
    env.GOOGLE_API_KEY;
  if (key?.trim()) return key.trim();
  return "";
}
