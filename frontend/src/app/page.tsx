"use client";

import { useState } from "react";
import { DemoContext } from "@/components/DemoContext";
import { IngestView } from "@/components/IngestView";
import { SearchView } from "@/components/SearchView";

type Tab = "ingest" | "search";

export default function Home() {
  const [tab, setTab] = useState<Tab>("ingest");

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-inner">
          <div className="app-header-row">
            <div className="app-header-brand">
              <div className="app-header-logo-mark">NV</div>
              <div>
                <h1>NexValue Enterprise Search</h1>
                <p className="app-header-subtitle">
                  Docling parsing · OpenSearch indexing
                </p>
              </div>
            </div>
            <div className="header-tags" aria-label="Technologies">
              <span>Docling</span>
              <span>OpenSearch 3.5</span>
            </div>
          </div>

          <nav className="tab-segmented" role="tablist" aria-label="Main navigation">
            <button
              role="tab"
              aria-selected={tab === "ingest"}
              className={`tab-segmented-btn ${tab === "ingest" ? "active" : ""}`}
              onClick={() => setTab("ingest")}
            >
              Ingest &amp; Parse
            </button>
            <button
              role="tab"
              aria-selected={tab === "search"}
              className={`tab-segmented-btn ${tab === "search" ? "active" : ""}`}
              onClick={() => setTab("search")}
            >
              Enterprise Search
            </button>
          </nav>
        </div>
      </header>

      <main className="app-main">
        <div className="demo-focus">
          {tab === "ingest" ? <IngestView /> : <SearchView />}
        </div>
        <DemoContext tab={tab} />
      </main>
    </div>
  );
}
