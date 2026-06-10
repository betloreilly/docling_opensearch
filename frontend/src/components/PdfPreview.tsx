"use client";

import { useEffect, useRef, useState } from "react";
import { apiClient, type DoclingBbox } from "@/lib/api";

const IMAGE_EXT = /\.(png|jpe?g|tiff?|webp|bmp)$/i;

type PdfPreviewProps = {
  documentId: string;
  filename?: string;
  page?: number;
  highlight?: DoclingBbox | null;
  highlightLabel?: string;
};

function bboxOverlay(
  highlight: DoclingBbox,
  pageSize: { width: number; height: number },
  renderScale: number
) {
  return {
    left: highlight.l * renderScale,
    top: (pageSize.height - highlight.t) * renderScale,
    width: (highlight.r - highlight.l) * renderScale,
    height: (highlight.t - highlight.b) * renderScale,
  };
}

export function PdfPreview({
  documentId,
  filename = "",
  page = 1,
  highlight,
  highlightLabel,
}: PdfPreviewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pageSize, setPageSize] = useState<{ width: number; height: number } | null>(null);
  const [renderScale, setRenderScale] = useState(1);
  const [imageUrl, setImageUrl] = useState<string | null>(null);

  const isImage = IMAGE_EXT.test(filename);

  useEffect(() => {
    let cancelled = false;
    let objectUrl: string | null = null;

    async function renderPdf() {
      const container = containerRef.current;
      const canvas = canvasRef.current;
      if (!container || !canvas) return;

      setLoading(true);
      setError(null);
      setPageSize(null);
      setImageUrl(null);

      try {
        const res = await fetch(apiClient.documentFileUrl(documentId));
        if (!res.ok) throw new Error(`Could not load document (${res.status})`);
        const buffer = await res.arrayBuffer();
        if (!buffer.byteLength) throw new Error("File is empty");
        if (cancelled) return;

        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

        const pdf = await pdfjs.getDocument({ data: buffer }).promise;
        if (cancelled) return;

        const pageIndex = Math.min(Math.max(page, 1), pdf.numPages);
        const pdfPage = await pdf.getPage(pageIndex);
        if (cancelled) return;

        const baseViewport = pdfPage.getViewport({ scale: 1 });
        const containerWidth = container.clientWidth || 640;
        const scale = containerWidth / baseViewport.width;
        const viewport = pdfPage.getViewport({ scale });

        canvas.width = Math.floor(viewport.width);
        canvas.height = Math.floor(viewport.height);
        const ctx = canvas.getContext("2d");
        if (!ctx) throw new Error("Canvas unavailable");

        await pdfPage.render({ canvasContext: ctx, viewport }).promise;
        if (cancelled) return;

        setPageSize({ width: baseViewport.width, height: baseViewport.height });
        setRenderScale(scale);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load document");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    async function renderImage() {
      const container = containerRef.current;
      if (!container) return;

      setLoading(true);
      setError(null);
      setPageSize(null);
      setImageUrl(null);

      try {
        const res = await fetch(apiClient.documentFileUrl(documentId));
        if (!res.ok) throw new Error(`Could not load image (${res.status})`);
        const blob = await res.blob();
        if (!blob.size) throw new Error("Image file is empty");
        if (cancelled) return;

        objectUrl = URL.createObjectURL(blob);
        const dims = await new Promise<{ width: number; height: number }>((resolve, reject) => {
          const img = new Image();
          img.onload = () => resolve({ width: img.naturalWidth, height: img.naturalHeight });
          img.onerror = () => reject(new Error("Failed to decode image"));
          img.src = objectUrl!;
        });
        if (cancelled) return;

        const containerWidth = container.clientWidth || 640;
        const scale = containerWidth / dims.width;
        setPageSize(dims);
        setRenderScale(scale);
        setImageUrl(objectUrl);
        objectUrl = null;
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load image");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    if (isImage) {
      renderImage();
    } else {
      renderPdf();
    }

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [documentId, page, isImage]);

  useEffect(() => {
    return () => {
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    };
  }, [imageUrl]);

  const downloadUrl = apiClient.documentFileUrl(documentId);
  const overlay =
    highlight && pageSize ? bboxOverlay(highlight, pageSize, renderScale) : null;

  return (
    <div className="pdf-preview-wrap" ref={containerRef}>
      {loading && (
        <div className="pdf-preview-state pdf-preview-overlay">
          <span className="spinner" />
          <span>Loading document preview…</span>
        </div>
      )}

      {error && !loading && (
        <div className="pdf-preview-state pdf-preview-error">
          <p>{error}</p>
          <a href={downloadUrl} target="_blank" rel="noopener noreferrer" className="btn btn-sm">
            Open file in new tab
          </a>
        </div>
      )}

      {!error && (
        <div className={`pdf-preview-canvas-wrap ${loading ? "is-loading" : ""}`}>
          {isImage ? (
            imageUrl && (
              <img src={imageUrl} alt="Document preview" className="pdf-preview-image" />
            )
          ) : (
            <canvas ref={canvasRef} className="pdf-preview-canvas" />
          )}
          {!loading && overlay && (
            <div
              className="pdf-bbox-highlight"
              style={{
                left: overlay.left,
                top: overlay.top,
                width: overlay.width,
                height: overlay.height,
              }}
              aria-hidden
            >
              {highlightLabel && <span className="pdf-bbox-label">{highlightLabel}</span>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
