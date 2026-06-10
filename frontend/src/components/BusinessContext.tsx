const VALUE_TAGS = [
  "Structured PDF parsing",
  "Table & heading extraction",
  "Search-ready chunks",
  "AI-ready content",
];

export function BusinessContextBrief() {
  return (
    <div className="context-brief">
      <p className="context-brief-line">
        <span className="context-label">Challenge</span>
        Policy knowledge is locked in complex PDFs — tables, headings, and structure are hard to search.
      </p>
      <p className="context-brief-line">
        <span className="context-label">Demo</span>
        Parse a NexValue document with Docling, inspect the extracted structure, then search the indexed content.
      </p>
      <div className="context-value-tags" aria-label="Business outcomes">
        {VALUE_TAGS.map((tag) => (
          <span key={tag} className="context-value-tag">
            {tag}
          </span>
        ))}
      </div>
    </div>
  );
}
