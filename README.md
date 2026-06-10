# NexValue Financial Enterprise Search

A developer demo showing how **NexValue Financial**, a financial services company, turns complex internal documents into structured, searchable business knowledge using **IBM Docling** and **OpenSearch hybrid search**.

![Demo](docs/doclingdemo.gif)

## Overview

NexValue Financial manages thousands of internal documents, including KYC procedures, AML policies, customer onboarding guides, risk manuals, product documentation, and compliance FAQs. Employees often lose time searching through complex PDFs, long policy files, and tables. Traditional keyword search can miss useful information when employees ask natural-language questions or use different wording from the original policy.

This demo shows how NexValue builds a stronger enterprise search foundation with the following workflow:

**Internal documents → Docling ingestion → structured extraction → OpenSearch indexing → hybrid enterprise search**

**Docling** extracts structure from complex documents: headings, paragraphs, tables, reading order, page provenance, and layout-aware content (including OCR on scans). **OpenSearch** indexes the resulting structured chunks and supports keyword, semantic, and hybrid retrieval. **Hybrid search** is the default experience in the UI because it combines exact term matching with semantic understanding.

The result is a **search-ready knowledge layer** that can also work as a **RAG-ready foundation** for future pipelines and internal AI assistants.

## Why use Docling SaaS

Most organizations have valuable information locked inside PDFs, scans, forms, tables, presentations, spreadsheets, and long policy documents. Basic text extraction can remove the context that makes those documents useful: headings, layout, table structure, reading order, page location, and relationships between sections.

Docling SaaS helps turn those raw files into structured, AI-ready content that downstream search, analytics, and automation systems can use more reliably.

Use Docling SaaS when you need to:

- Preserve document meaning by keeping layout, reading order, tables, and page context
- Extract content from scanned files and image-heavy documents with OCR
- Convert complex files into AI-ready outputs such as Markdown, JSON, and HTML
- Process multiple formats through one service instead of maintaining separate parsers
- Keep provenance such as page numbers and bounding boxes for traceability
- Move from one-off document conversion to repeatable API-based processing

You can start with the [IBM Docling for IBM watsonx free trial](https://www.ibm.com/account/reg/us-en/signup?formid=urx-54322). The trial page describes free pages, AI-ready outputs, preserved document meaning, multi-format processing, and API access.

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

This repo uses Docling SaaS for parsing. Do not install local Docling parsing models for this demo.

## Setup

### Start from scratch checklist

For a new machine, the order is:

1. Create a Docling SaaS trial and copy your API key + service URL
2. Clone this repo
3. Run `./setup.sh`
4. Edit `.env` with your Docling values
5. Verify Docling connectivity
6. Start OpenSearch with `npm run opensearch:up`
7. Start the backend with `npm run backend`
8. Start the frontend with `npm run frontend`
9. Open `http://localhost:3000`

### 1. Create a Docling SaaS trial and get credentials

Create a free trial from the [IBM Docling for IBM watsonx trial page](https://www.ibm.com/account/reg/us-en/signup?formid=urx-54322). After registration, open the IBM SaaS Console and confirm that **Docling for IBM watsonx** is active.

The screenshots below show the flow in the Docling SaaS console. Use the values from your own trial account when you configure `.env`.

![Docling trial subscription](docs/screenshots/trial1.png)

Open the subscription, go to the **Instances** tab, and open your running instance.

![Docling instance list](docs/screenshots/trial2.png)

In the Docling workbench:

1. Open **API keys**
2. Create an API key
3. Copy it immediately and save it somewhere safe. You will use it as `DOCLING_API_KEY`

![Docling workbench](docs/screenshots/trial3.png)

Then open **Integrate** and copy the **Service URL**. You will use it as `DOCLING_SERVICE_URL`.

![Docling API integration](docs/screenshots/trial4.png)

You need two values for this repo:

```env
DOCLING_SERVICE_URL=https://your-docling-service-url
DOCLING_API_KEY=your-api-key
```

Keep the real values only in your local `.env`. Do not commit them.

### 2. Clone and configure

```bash
git clone <your-repo-url>
cd docling_opensearch
```

Run the setup script:

```bash
./setup.sh
```

The script:

- Creates `.env` from `.env.example` if it does not exist
- Creates `frontend/.env.local` from `frontend/.env.local.example` if it does not exist
- Creates the Python virtual environment at `.venv`
- Installs Python dependencies from `requirements.txt`
- Installs frontend dependencies in `frontend/`
- Regenerates the sample PDFs in `data/`

You can also run the same setup through npm:

```bash
npm run setup
```

Edit `.env` with your Docling SaaS credentials after setup:

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

### 3. Manage the Python virtual environment

The backend is a Python FastAPI app. It uses Docling SaaS, local embeddings, OpenSearch client libraries, and the sample PDF generator. This repo keeps those Python packages inside `.venv` so they do not affect your system Python or other projects.

Useful commands:

```bash
.venv/bin/python --version
.venv/bin/python -m pip show docling-slim
.venv/bin/uvicorn --version
npm run venv:reset
```

Use `npm run venv:reset` if the Python environment gets into a bad state.

Three sample PDFs are already included in `data/`. To regenerate them:

```bash
npm run samples
```

This uses `.venv/bin/python`, so run `./setup.sh` or `npm run setup` first.

### 4. Start OpenSearch

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
├── docs/                 # README assets (architecture PNG, demo GIF, setup screenshots)
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
