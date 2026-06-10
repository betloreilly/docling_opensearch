type Step = { num: number; label: string; active?: boolean; done?: boolean };

const INGEST_STEPS: Step[] = [
  { num: 1, label: "Choose a NexValue document" },
  { num: 2, label: "Inspect Docling extraction" },
  { num: 3, label: "Search policy knowledge" },
];

export function DemoSteps({
  current = 1,
  variant = "ingest",
}: {
  current?: number;
  variant?: "ingest" | "search";
}) {
  const activeStep = variant === "search" ? Math.max(3, current) : current;

  return (
    <div className="demo-steps" role="list" aria-label="Demo walkthrough">
      {INGEST_STEPS.map((step) => {
        const done = step.num < activeStep;
        const active = step.num === activeStep;
        return (
          <div
            key={step.num}
            role="listitem"
            className={`demo-step ${done ? "done" : ""} ${active ? "active" : ""}`}
          >
            <span className="demo-step-num">{done ? "✓" : step.num}</span>
            <span className="demo-step-label">{step.label}</span>
          </div>
        );
      })}
    </div>
  );
}
