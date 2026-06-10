# NexValue Financial Enterprise Search

A developer demo showing how **NexValue Financial**, a financial services company, turns complex internal documents into structured, searchable business knowledge using **IBM Docling** and **OpenSearch hybrid search**.

![Demo](docs/doclingdemo.gif)

## Overview

NexValue Financial manages thousands of internal documents, including KYC procedures, AML policies, customer onboarding guides, risk manuals, product documentation, and compliance FAQs. Employees often lose time searching through complex PDFs, long policy files, and tables. Traditional keyword search can miss useful information when employees ask natural-language questions or use different wording from the original policy.

This demo shows how NexValue builds a stronger enterprise search foundation with the following workflow:

**Internal documents → Docling ingestion → structured extraction → OpenSearch indexing → hybrid enterprise search**

**Docling** extracts structure from complex documents: headings, paragraphs, tables, reading order, page provenance, and layout-aware content (including OCR on scans). **OpenSearch** indexes the resulting structured chunks and supports keyword, semantic, and hybrid retrieval. **Hybrid search** is the default experience in the UI because it combines exact term matching with semantic understanding.

The result is a **search-ready knowledge layer** that can also work as a **RAG-ready foundation** for future pipelines and internal AI assistants.

## Business problem

| Challenge | Impact |
|-----------|--------|
| Policy knowledge trapped in PDFs | Slow answers, repeated manual lookups |
| Scanned forms and image-only pages | Invisible to plain text extraction |
| Tables, headings, and document structure lost during indexing | Wrong or incomplete search hits |
| Keyword-only search misses paraphrased questions | Employees cannot find policy by intent |
| No reusable knowledge layer for AI assistants | Hard to extend into grounded Q&A or RAG |

## What this demo does

- Parses documents through **Docling SaaS** (`docling-slim[service-client]`)
- Surfaces **structured extraction** in the UI: element types, markdown, JSON, chunks, and bounding-box overlays on the source PDF or image
- Builds **structure-aware chunks** with section titles, page numbers, and element metadata
- Generates **embeddings locally** and indexes chunks into **OpenSearch 3.5**
- Runs **hybrid search by default** (BM25 + vector similarity with score fusion)
- Includes **OCR** and **complex table** showcase samples for live presentations

## What this demo does not do

- It does **not** include an LLM chat or answer-generation layer
- It does **not** implement a full RAG assistant (retrieval only; chunks are ready to be passed to one)

## Why Docling matters

Naive PDF text extraction collapses layout, breaks tables, and fails on scans. Docling returns a typed **DoclingDocument** with classified elements (title, heading, paragraph, table, image), reading order, and provenance. In this repo you can see that value directly: click an element in the structured viewer and highlight its region on the original page.

That structure is what makes enterprise search and future RAG pipelines trustworthy. This matters a lot in regulated industries where you need to know where an answer came from.

## Why hybrid search matters

| Mode | Mechanism | Best for |
|------|-----------|----------|
| **Keyword** | BM25 on chunk text and titles | Exact policy terms, acronyms, product codes |
| **Semantic** | kNN vector similarity on pre-indexed embeddings | Natural-language questions, paraphrases |
| **Hybrid** | BM25 + kNN in one request; OpenSearch normalizes and fuses scores | General enterprise search (**default in this demo**) |

Keyword search alone misses rephrased questions. Semantic search alone can drift on rare acronyms. Hybrid search balances both, which is why the UI always sends `mode: "hybrid"`.

## What you will build

By running this demo locally you will:

1. Ingest NexValue policy documents with Docling and inspect layout-aware extraction
2. Preview OCR and complex-table showcases with bounding-box overlays
3. Index Docling chunks into OpenSearch with locally generated embeddings
4. Search indexed policy content with hybrid retrieval
5. Present a credible enterprise search story that can be extended into RAG

## Architecture

![Architecture](/docs/Nextvalue.png)

**Workflow:** Documents → **Docling** → structured elements + chunks → **OpenSearch** → hybrid search

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| **Docker** | OpenSearch 3.5 + Dashboards via `docker compose` |
| **Python 3.10+** | Backend, Docling client, local embeddings |
| **Node.js 18+** | Next.js frontend |
| **~4 GB RAM** | OpenSearch container + embedding model |
| **Docling SaaS credentials** | `DOCLING_SERVICE_URL` + `DOCLING_API_KEY` (required for parsing) |

Embeddings are generated locally with `sentence-transformers/all-MiniLM-L6-v2`, so no embedding API key is required.

> **SaaS-only parsing:**  

## Setup

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd docling_opensearch
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
```

Edit `.env` with your Docling SaaS credentials:

```env
DOCLING_SERVICE_URL=https://your-docling-service-url
DOCLING_API_KEY=your-api-key
```

Verify Docling connectivity (optional):

```bash
source .env
curl -H "X-Api-Key: $DOCLING_API_KEY" "$DOCLING_SERVICE_URL/health"
# Expected: {"status":"ok"}
```

Or, after starting the backend:

```bash
curl http://localhost:8000/api/docling/status
```

That status endpoint calls your local backend, which checks Docling SaaS health for you. A healthy response confirms credentials. It does not test file upload.

### 2. Install dependencies

```bash
npm run setup
```

This creates `.venv`, installs Python dependencies, and runs `npm install` in `frontend/`.

Three sample PDFs are already included in `data/`. To regenerate them:

```bash
npm run samples
```

### 3. Start OpenSearch

```bash
npm run opensearch:up
```

| Service | URL | Login |
|---------|-----|-------|
| OpenSearch 3.5 | `https://localhost:9200` | `admin` / `YourStrongPass123!` |
| OpenSearch Dashboards | `http://localhost:5601` | same |

Container names: `docling-demo-opensearch`, `docling-demo-dashboards`.

After ingesting documents, open Dashboards → **Query Workbench** to inspect the `docling_demo` index.


## Run the demo

Terminal 1 (backend):

```bash
npm run backend
```

Terminal 2 (frontend):

```bash
npm run frontend
```

Open **http://localhost:3000**

| Component | URL |
|-----------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| OpenSearch | https://localhost:9200 |
| Dashboards | http://localhost:5601 |

## How to use the UI

### Ingest & Parse (Docling focus)

1. Expand **Business context** for the NexValue narrative
2. Select a sample or upload your own file (PDF, DOCX, Markdown, text, PNG, JPG, TIFF, WebP)
3. Try the tagged showcases: **OCR** (`KYC Verification Form (Scanned)`) and **complex table** (`Regulatory Retention Matrix`)
4. Click **Parse & index** and watch the pipeline: upload → Docling parsing → structure extraction → OpenSearch indexing
5. In the **Structured** tab, read the **Reading order**, **Bounding boxes**, and **Chunks** callouts at the top
6. Click an element to see its **layout box** on the preview and which **search chunk** it maps to
7. Open **Markdown**, **JSON**, or **Chunks** for exports; the Chunks tab shows what OpenSearch indexes

### Enterprise Search (OpenSearch focus)

1. Switch to the **Enterprise Search** tab
2. Try a suggested query, e.g. *"What documents are required for customer due diligence?"*
3. Review ranked chunks with document name, section title, page number, and element types
4. All searches use **hybrid retrieval** automatically
5. Click **View index** to open **OpenSearch Dashboards Query Workbench** and inspect the `docling_demo` index (requires Dashboards on `http://localhost:5601`)

## Demo narrative

Use this flow for a live presentation (~10 minutes):

| Step | Action | Talking point |
|------|--------|---------------|
| 1 | Open **Business context** | NexValue policy knowledge is trapped in complex PDFs and scans |
| 2 | Parse **NexValue AML & KYC Procedures.pdf** | Docling extracts structure, not a flat text dump |
| 3 | Click a **table** element | Tables stay structured and become searchable chunks |
| 4 | Parse **KYC Verification Form (Scanned)** | Docling OCR recovers text plain extractors miss |
| 5 | Show **Chunks** tab | This is the search-ready knowledge layer OpenSearch indexes |
| 6 | Search *"enhanced due diligence"* | Hybrid search finds relevant policy without exact keywords |
| 7 | Close with business value | Faster policy access today; RAG-ready foundation tomorrow |

### Sample documents

| Document | Highlight |
|----------|-----------|
| NexValue AML & KYC Procedures.pdf | Core AML/KYC policy (default demo) |
| Regulatory Retention Matrix.pdf | **Complex table** (merged headers) |
| KYC Verification Form (Scanned).pdf | **OCR showcase** (image-only scanned page) |

Upload your own PDFs or images anytime. Run `npm run samples` to regenerate the bundled samples.

### Suggested search queries

- "What documents are required for customer due diligence?"
- "When is enhanced due diligence needed?"
- "How long should customer data be retained?"
- "What is the process for high-risk customers?"

## How Docling ingestion works

1. A document is uploaded or selected from `data/`
2. The backend calls **Docling SaaS** via `DoclingServiceClient` using `DOCLING_SERVICE_URL` and `DOCLING_API_KEY` (also accepts `DOCLING_SERVICE_API_KEY`)
3. Docling returns a layout-aware document with reading order, tables, and provenance
4. Elements are classified: title, heading, paragraph, table, image, caption, and more
5. Structure-aware chunks are built (`CHUNK_SIZE_WORDS` / `CHUNK_OVERLAP_WORDS` in `.env`)
6. Chunks are embedded locally and bulk-indexed into OpenSearch

```python
from pathlib import Path
from docling.service_client import DoclingServiceClient

with DoclingServiceClient(url=SERVICE_URL, api_key=API_KEY) as client:
    result = client.convert(source=Path("policy.pdf"))
```

Parsed output is cached under `parsed/`. Uploads are stored under `uploads/`.

## How OpenSearch hybrid search works

This demo pre-generates embeddings in the backend (`sentence-transformers`) and stores vectors in the `chunk_text_vector` field. OpenSearch does not generate embeddings at query time (no ML Commons `neural` query in this repo).

Hybrid search follows the [OpenSearch hybrid search guide](https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/index/):

1. **Search pipeline:** `PUT /_search/pipeline/docling-hybrid-pipeline` with a `normalization-processor` (`min_max` + `arithmetic_mean`)
2. **Hybrid query:** `GET /docling_demo/_search?search_pipeline=docling-hybrid-pipeline` with `query.hybrid.queries` containing both BM25 and kNN sub-queries
3. **Score fusion:** default weights from `.env` are **40% keyword / 60% semantic** (`KEYWORD_WEIGHT`, `VECTOR_WEIGHT`)

The backend API accepts `mode: "keyword" | "semantic" | "hybrid"` on `POST /api/search`. The frontend always sends `hybrid`.

## Business value

- **Faster access** to internal policy knowledge across PDFs, tables, and long compliance documents
- **Better retrieval** for natural-language questions and policy lookups
- **Trustworthy provenance** with page numbers and layout context from Docling
- **Search-ready knowledge layer** that can be extended into a RAG pipeline or internal AI assistant

## Project layout

```
docling_opensearch/
├── backend/              # FastAPI, Docling SaaS, chunking, embeddings, OpenSearch
│   ├── main.py
│   ├── config.py
│   ├── models/
│   └── services/
├── frontend/             # Next.js UI, ingest preview, hybrid search
│   └── src/
├── data/                 # NexValue sample documents (+ .samples_manifest.json)
├── docs/                 # README assets (architecture PNG, demo GIF)
├── scripts/              # Sample PDF generator
├── parsed/               # Cached Docling JSON (gitignored at runtime)
├── uploads/              # Uploaded files (gitignored at runtime)
├── docker-compose.yml    # OpenSearch 3.5 + Dashboards
├── package.json          # npm scripts for setup and dev servers
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Missing sample PDFs

```bash
npm run samples
```

Requires the Python venv from `npm run setup` (ReportLab + Pillow).

### Python version mismatch

Use **Python 3.10 or newer**. Recreate the venv if packages fail to install:

```bash
rm -rf .venv && npm run setup
```

### PDF preview is blank

Leave `NEXT_PUBLIC_API_URL` unset so Next.js proxies `/api` to the backend (`BACKEND_URL` in `frontend/.env.local`). Direct cross-origin PDF URLs break the preview iframe.

### `http://localhost:8000` in curl commands

`/api/*` routes are served by the local FastAPI backend. The frontend reaches the same backend through Next.js rewrites to `http://127.0.0.1:8000`.

## Next steps

- Ingest all three NexValue samples and compare OCR vs native PDF extraction quality
- Tune hybrid weights in `.env` (`KEYWORD_WEIGHT`, `VECTOR_WEIGHT`)
- Connect your own policy corpus and validate chunks before indexing
- Extend indexed chunks into a RAG pipeline. 


## Learn more

- [Docling documentation](https://docling-project.github.io/docling/)
- [OpenSearch hybrid search](https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/index/)
