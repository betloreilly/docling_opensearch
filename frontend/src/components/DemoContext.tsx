"use client";

import { useState } from "react";
import { BusinessContextBrief } from "./BusinessContext";
import { WorkflowStrip } from "./WorkflowStrip";

export function DemoContext({ tab }: { tab: "ingest" | "search" }) {
  const [open, setOpen] = useState(false);

  return (
    <section className="context-section" aria-label="Business context">
      <button
        type="button"
        className="context-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="context-toggle-label">Business context</span>
        <span className="context-toggle-chevron" aria-hidden>
          {open ? "−" : "+"}
        </span>
      </button>

      {open && (
        <div className="context-body">
          <BusinessContextBrief />
          <WorkflowStrip highlight={tab === "ingest" ? 1 : 4} />
        </div>
      )}
    </section>
  );
}
