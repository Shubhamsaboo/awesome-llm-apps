/**
 * Save a Blob as a file using the browser download path (no pop-up).
 * Works after async fetch when the response is same-origin (e.g. /api/workspace/download?stream).
 */
export function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
