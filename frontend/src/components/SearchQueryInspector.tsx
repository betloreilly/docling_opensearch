"use client";

import { useState } from "react";
import type { SearchQueryDebug } from "@/lib/api";

function JsonBlock({ data }: { data: unknown }) {
  return <pre className="query-json-block">{JSON.stringify(data, null, 2)}</pre>;
}

function Expandable({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="query-expandable">
      <button
        type="button"
        className="query-expandable-trigger"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className={`query-chevron ${open ? "open" : ""}`} aria-hidden>›</span>
        {title}
      </button>
      {open && <div className="query-expandable-body">{children}</div>}
    </div>
  );
}

export function SearchQueryInspector({
  debug,
  mode,
}: {
  debug: SearchQueryDebug | null | undefined;
  mode: string;
}) {
  if (!debug) {
    return (
      <p className="query-inspector-empty">
        Run a search to see a short explanation of what OpenSearch does.
      </p>
    );
  }

  const kw = Math.round(debug.fusion_weights.keyword * 100);
  const vec = Math.round(debug.fusion_weights.vector * 100);

  return (
    <div className="query-inspector">
      <p className="query-summary">
        {mode === "hybrid"
          ? `OpenSearch runs a keyword search and a meaning-based search, then blends the results (${kw}% exact words, ${vec}% meaning).`
          : mode === "keyword"
            ? "OpenSearch looks for exact words in policy text and titles."
            : "OpenSearch looks for chunks that mean the same thing as the question."}
      </p>

      <Expandable title="What happens in 3 steps">
        <ol className="query-steps">
          {debug.steps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </Expandable>

      {mode === "hybrid" && (
        <Expandable title="Technical: search pipeline">
          <p className="query-hint">
            Sets how keyword and vector scores are combined.{" "}
            <a href={debug.documentation_url} target="_blank" rel="noopener noreferrer">
              OpenSearch docs
            </a>
          </p>
          {debug.create_search_pipeline && (
            <>
              <code className="query-endpoint">
                {debug.create_search_pipeline.method} {debug.create_search_pipeline.path}
              </code>
              <JsonBlock data={debug.create_search_pipeline.body} />
            </>
          )}
        </Expandable>
      )}

      <Expandable title="Technical: search request">
        <p className="query-hint">
          The actual query sent to index <strong>{debug.index}</strong>
          {debug.search_pipeline ? ` with pipeline ${debug.search_pipeline}` : ""}.
        </p>
        <code className="query-endpoint">
          {debug.search_request.method} {debug.search_request.endpoint}
        </code>
        <JsonBlock data={debug.search_request.body} />
      </Expandable>
    </div>
  );
}
