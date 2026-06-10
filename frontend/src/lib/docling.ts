export function getPictureDataUri(
  jsonExport: Record<string, unknown>,
  ref: string | null | undefined
): string | null {
  if (!ref) return null;
  const pictures = jsonExport.pictures;
  if (!Array.isArray(pictures)) return null;

  const picture = pictures.find(
    (entry) =>
      typeof entry === "object" &&
      entry !== null &&
      (entry as Record<string, unknown>).self_ref === ref
  ) as Record<string, unknown> | undefined;

  if (!picture) return null;

  const image = picture.image;
  if (!image || typeof image !== "object") return null;

  const uri = (image as Record<string, unknown>).uri;
  if (typeof uri !== "string" || !uri.startsWith("data:")) return null;
  return uri;
}
