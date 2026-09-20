export const MAX_REQUEST_BYTES = 512_000;
export function accessError(headers, env = process.env) {
  const token = env.NEEDLE_ACCESS_TOKEN?.trim();
  if (env.VERCEL && !token)
    return {
      status: 503,
      error:
        "Set NEEDLE_ACCESS_TOKEN on the server before sharing this deployment.",
    };
  if (token && headers["x-needle-token"] !== token)
    return { status: 401, error: "Set the Needle access token in settings." };
  return null;
}
