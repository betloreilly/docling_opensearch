export const DASHBOARDS_URL =
  process.env.NEXT_PUBLIC_OPENSEARCH_DASHBOARDS_URL || "http://localhost:5601";

export const OPENSEARCH_INDEX =
  process.env.NEXT_PUBLIC_OPENSEARCH_INDEX || "docling_demo";

/** Query Workbench — browse indexes and run SQL/PPL queries */
export const DASHBOARDS_INDEX_URL = `${DASHBOARDS_URL}/app/opensearch-query-workbench#/`;
