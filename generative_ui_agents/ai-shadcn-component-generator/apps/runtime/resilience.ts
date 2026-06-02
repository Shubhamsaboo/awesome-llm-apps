/**
 * Process-level error resilience and memory monitoring.
 *
 * The Node.js runtime proxies streaming responses from the Python agent.
 * When the agent or client disconnects mid-stream, socket/fetch errors
 * surface as unhandled rejections or uncaught exceptions that would
 * otherwise crash the process.
 *
 * This module:
 * - Suppresses known network/stream errors in unhandledRejection so the
 *   process stays up for other connections.
 * - Always exits on uncaughtException (per Node.js guidance) but logs
 *   whether the error was a known network issue or a genuine bug.
 * - Periodically logs memory usage, triggers GC when RSS climbs toward
 *   the container limit, and initiates a **graceful shutdown** when heap
 *   is dangerously close to the V8 hard limit — preventing the abrupt
 *   exit-134 OOM crash that kills in-flight requests.
 */

const IGNORABLE_ERRORS = [
  "terminated",
  "other side closed",
  "ECONNRESET",
  "ECONNREFUSED",
  "EPIPE",
  "network error",
  "aborted",
  "AbortError",
  "socket hang up",
  "UND_ERR_SOCKET",
];

function isIgnorable(err: unknown): boolean {
  const msg =
    err instanceof Error ? `${err.name}: ${err.message}` : String(err);
  if (IGNORABLE_ERRORS.some((token) => msg.includes(token))) return true;
  // Check cause chain (Node.js fetch wraps network errors)
  if (err instanceof Error && err.cause) {
    return isIgnorable(err.cause);
  }
  return false;
}

process.on("unhandledRejection", (err: unknown) => {
  if (isIgnorable(err)) {
    console.warn(
      "[unhandledRejection] Suppressed:",
      err instanceof Error ? err.message : String(err),
    );
    return;
  }
  console.error("[unhandledRejection]", err);
});

process.on("uncaughtException", (err: Error) => {
  if (isIgnorable(err)) {
    console.error("[uncaughtException] Ignorable but fatal (unsafe to continue):", err.message);
  } else {
    console.error("[uncaughtException] Fatal:", err);
  }
  process.exit(1);
});

// --- Memory monitoring with graceful OOM shutdown ---

const MEMORY_LOG_INTERVAL_MS = 60_000;
const MEMORY_WARN_THRESHOLD_MB = 200;
// Trigger graceful shutdown before V8's hard OOM (--max-old-space-size=256).
// At 235MB heap we're ~20MB from the cliff — enough headroom to drain but
// not so much that we restart unnecessarily.
const GRACEFUL_SHUTDOWN_HEAP_MB = 235;
const GRACEFUL_DRAIN_MS = 5_000;

let shuttingDown = false;
const shutdownCallbacks: Array<() => void> = [];

/**
 * Exported so server.ts can read it in middleware to reject new requests
 * while the process is draining before a graceful restart.
 */
export function isShuttingDown(): boolean {
  return shuttingDown;
}

/**
 * Register a callback to run when graceful shutdown begins (e.g. server.close()).
 */
export function onShutdown(cb: () => void): void {
  shutdownCallbacks.push(cb);
}

function gracefulShutdown() {
  if (shuttingDown) return;
  shuttingDown = true;
  for (const cb of shutdownCallbacks) {
    try { cb(); } catch (e) { console.error("[shutdown] callback error", e); }
  }

  const mem = process.memoryUsage();
  const heapMb = Math.round(mem.heapUsed / 1024 / 1024);
  console.warn(
    `[memory] Heap at ${heapMb}MB — initiating graceful shutdown to avoid OOM crash`,
  );
  console.warn(
    `[memory] Draining in-flight requests for ${GRACEFUL_DRAIN_MS}ms before exit…`,
  );

  // Give in-flight requests a few seconds to complete, then exit cleanly.
  // Render will restart the instance automatically.
  setTimeout(() => {
    console.warn("[memory] Drain period complete — exiting (code 0)");
    process.exit(0);
  }, GRACEFUL_DRAIN_MS);
}

setInterval(() => {
  const mem = process.memoryUsage();
  const rssMb = Math.round(mem.rss / 1024 / 1024);
  const heapMb = Math.round(mem.heapUsed / 1024 / 1024);

  if (heapMb >= GRACEFUL_SHUTDOWN_HEAP_MB) {
    gracefulShutdown();
    return;
  }

  if (rssMb > MEMORY_WARN_THRESHOLD_MB) {
    console.warn(
      `[memory] WARNING RSS=${rssMb}MB heap=${heapMb}MB — approaching limit`,
    );
    if (global.gc) {
      console.warn("[memory] Forcing garbage collection");
      global.gc();
    }
  }
}, MEMORY_LOG_INTERVAL_MS).unref();
