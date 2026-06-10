const STEPS = [
  "Documents",
  "Docling",
  "Structured content",
  "OpenSearch",
  "Search",
];

export function WorkflowStrip({ highlight }: { highlight?: number }) {
  return (
    <p className="workflow-line" aria-label="Enterprise search workflow">
      {STEPS.map((step, i) => (
        <span key={step}>
          <span className={`workflow-line-step ${highlight === i ? "highlight" : ""}`}>
            {step}
          </span>
          {i < STEPS.length - 1 && (
            <span className="workflow-line-sep" aria-hidden>
              {" "}
              →{" "}
            </span>
          )}
        </span>
      ))}
    </p>
  );
}
