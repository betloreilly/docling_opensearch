import type { DocumentChunk, DocumentElement } from "@/lib/api";

/** Best-effort link from a structured element to OpenSearch-ready chunks. */
export function findChunksForElement(
  element: DocumentElement,
  chunks: DocumentChunk[]
): DocumentChunk[] {
  const needle = element.text.trim().slice(0, 48);
  if (needle.length >= 12) {
    const byText = chunks.filter((c) => c.text.includes(needle));
    if (byText.length > 0) return byText;
  }

  if (element.type === "table") {
    return chunks.filter(
      (c) => c.element_types.includes("table") && c.page_number === element.page
    );
  }

  return chunks.filter(
    (c) =>
      c.page_number === element.page &&
      c.element_types.includes(element.type) &&
      (needle.length < 8 || c.text.toLowerCase().includes(needle.slice(0, 24).toLowerCase()))
  );
}
