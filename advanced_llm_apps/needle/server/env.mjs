import { loadEnvFile } from "node:process";
// Runtime-only configuration; existing environment variables take precedence.
try {
  loadEnvFile(".env");
} catch (error) {
  if (error.code !== "ENOENT") throw error;
}
