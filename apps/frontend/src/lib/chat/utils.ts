import type { AttachmentPayload } from "./types";

export function createId(prefix = "id"): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `${prefix}-${crypto.randomUUID()}`;
  }

  const random = Math.random().toString(36).slice(2, 10);
  const timestamp = Date.now().toString(36);
  return `${prefix}-${timestamp}-${random}`;
}

export function nowIso(): string {
  return new Date().toISOString();
}

export function toBase64(buffer: ArrayBuffer): string {
  const maybeBuffer = typeof globalThis !== "undefined" ? (globalThis as Record<string, unknown>).Buffer : undefined;
  if (maybeBuffer && typeof (maybeBuffer as { from: (input: ArrayBuffer) => { toString(encoding: string): string } }).from === "function") {
    return (
      maybeBuffer as { from: (input: ArrayBuffer) => { toString(encoding: string): string } }
    )
      .from(buffer)
      .toString("base64");
  }

  let binary = "";
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    const chunk = bytes.subarray(i, i + chunkSize);
    binary += String.fromCharCode(...chunk);
  }
  if (typeof btoa === "function") {
    return btoa(binary);
  }
  throw new Error("Base64 encoding is not supported in this environment.");
}

export function buildAttachmentPayload(file: File, base64: string): AttachmentPayload {
  return {
    id: createId("file"),
    name: file.name,
    size: file.size,
    type: file.type,
    data: base64,
  };
}

export function formatFileSize(bytes?: number): string {
  if (bytes === undefined || bytes === null || Number.isNaN(bytes)) {
    return "";
  }

  const absolute = Math.abs(bytes);
  if (absolute < 1024) {
    return `${bytes} B`;
  }

  const units = ["KB", "MB", "GB", "TB"] as const;
  let value = absolute / 1024;
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }

  const formatted = `${value.toFixed(1)} ${units[unitIndex]}`;
  return bytes < 0 ? `-${formatted}` : formatted;
}

export function stripMarkdown(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/#+\s*/g, "")
    .replace(/>\s?/g, "")
    .trim();
}
