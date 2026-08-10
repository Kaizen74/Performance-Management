# Strategic Goal Alignment Analyzer (SGAA)

Analyze employee performance goals against organizational strategy. SGAA reads
your strategy documents, builds a Balanced Scorecard framework from them, scores
every employee goal for strategic alignment, and exports board-ready Excel and
PDF reports.

**Runs free and offline by default.** Without an API key the app uses a built-in
heuristic analyzer, so you can trial the full workflow at no cost. Supply an
Anthropic API key in the UI to switch to Claude-powered analysis.

---

## What it does

| Stage | What happens |
|---|---|
| **1. Upload strategy** | PDF, DOCX, PPTX or XLSX. Vision, mission, values, strategic themes and objectives are extracted into a Balanced Scorecard framework (Financial / Customer / Internal Process / Learning & Growth). |
| **2. Upload goals** | A CSV or Excel export of employee goals from your HR system (SAP SuccessFactors format supported out of the box), or individual goal documents. |
| **3. Analyze** | Each goal is scored for strategic alignment and impact, then classified on a **rigor × alignment** matrix. |
| **4. Review** | Portfolio dashboard, per-employee scorecards, and improvement recommendations for weak goals. |
| **5. Export** | Multi-sheet Excel workbook and a formatted PDF report. |

### The rigor × alignment matrix

Every goal lands in one of four quadrants, which drives the **Coherence Index**:

|  | **Strategically aligned** | **Not aligned** |
|---|---|---|
| **Outcome-based** | 🟢 Strategic Driver (100 pts) | 🟠 Rogue Project (25 pts) |
| **Activity-based** | 🟡 Busy Work Trap (50 pts) | 🔴 Distraction (0 pts) |

Coherence Index = mean points across all goals. It answers one question: *is this
person's effort actually pointed at the strategy?*

### Scope detection

SGAA detects whether an uploaded strategy is **organization-wide** or belongs to a
**specific department or team** (for example an HR or IT functional strategy) and
frames the entire analysis accordingly, rather than inventing a company vision for
a team-level document.

---

## Quick start

### Option A — Docker (recommended)

Requires Docker and Docker Compose.

```bash
git clone https://github.com/Kaizen74/Performance-Management.git
cd Performance-Management
cp .env.example .env          # optional; sensible defaults apply

docker compose -f deployment/docker/docker-compose.yml up --build
```

Then open **http://localhost** in your browser.

The backend API is on http://localhost:8000 (interactive docs at
http://localhost:8000/docs). The frontend container waits for the backend's
health check to pass before starting.

To stop:

```bash
docker compose -f deployment/docker/docker-compose.yml down
```

### Option B — Local development

Requires **Python 3.11+** and **Node.js 18+**.

**Terminal 1 — backend:**

```bash
cd Performance-Management
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 — frontend:**

```bash
cd Performance-Management/frontend
npm install
npm run dev
```

Open **http://localhost:3000**. Vite proxies `/api` to the backend on port 8000,
so no CORS configuration is needed in development.

---

## Configuration

All settings are optional — the app runs with no `.env` file at all. See
[`.env.example`](.env.example) for the full list.

| Variable | Default | Purpose |
|---|---|---|
| `USE_MOCK` | `true` | When `true`, requests without an API key use the offline heuristic analyzer. When `false`, requests without a key are rejected. |
| `ANTHROPIC_API_KEY` | unset | Optional server-wide default. Normally each user supplies their own key in the UI, and it is never persisted server-side. |

**API keys are never stored.** A key entered in the UI is held in browser memory
for the session, sent per request, and discarded.

### Limits

| Limit | Value |
|---|---|
| Strategy documents per analysis | 5 |
| Goal documents per analysis | 500 |
| Parallel analysis workers | 5 |
| Supported strategy formats | PDF, DOCX, PPTX, XLSX |
| Supported goals-table formats | CSV, XLSX, XLS |

---

## Verifying the build

One command runs everything — backend tests, frontend type check, production build:

```bash
./run_checks.sh            # full gate
./run_checks.sh backend    # backend tests only (no Node required)
```

You want to see `ALL CHECKS PASSED ✅`. The suite is fully mocked, so it runs
free, offline, and makes no API calls.

```
tests/test_alignment_analyzer.py       alignment scoring, coherence, quadrants
tests/test_api_routes.py               end-to-end API contract (upload → export)
tests/test_document_processor.py       PDF / DOCX / PPTX / XLSX extraction
tests/test_excel_export.py             Excel + PDF export, seniority reconciliation
tests/test_goals_table_processor.py    HR table parsing, seniority inference
tests/test_recommendations.py          goal improvement recommendations
tests/test_strategy_synthesizer.py     framework synthesis, scope detection
```

---

## API reference

Base URL `/api`. Interactive documentation is served at `/docs`.

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/test-connection` | Validate an Anthropic API key |
| `POST` | `/upload/goals-table` | Upload a CSV/Excel goals export |
| `POST` | `/upload/{document_type}` | Upload a `strategy` or `goals` document |
| `GET` | `/documents` | List uploaded documents |
| `GET` | `/documents/{id}` | Fetch one document |
| `DELETE` | `/documents/{id}` | Remove a document |
| `POST` | `/analyze/strategy` | Synthesize the strategic framework |
| `POST` | `/analyze/goals` | Score goals against the framework |
| `GET` | `/framework` | Fetch the current framework |
| `GET` | `/analyses` · `/analyses/{id}` | Fetch analysis results |
| `POST` | `/recommendations/{document_id}` | Recommendations for one employee |
| `POST` · `GET` | `/recommendations/portfolio` | Portfolio-wide recommendations |
| `POST` | `/export/excel` · `/export/pdf` | Generate reports |
| `GET` | `/export/status` | Whether an export is available yet |
| `POST` | `/reset` | Clear all server-side state |

---

## Project structure

```
backend/
  main.py                  FastAPI app and CORS
  api/routes.py            all HTTP endpoints
  processors/              PDF / DOCX / PPTX / XLSX / goals-table extraction
  analyzers/               strategy synthesis, alignment scoring, recommendations
  exports/                 Excel and PDF report engines
frontend/
  src/components/          UI panels, dashboard, scorecards, charts
  src/contexts/            shared analysis state
  src/lib/seniority.ts     canonical seniority buckets (shared contract)
deployment/
  docker/                  Dockerfiles and compose file
  nginx/                   production frontend server config
tests/                     full mocked test suite
run_checks.sh              one-command quality gate
```

---

## Deployment notes

**Production checklist**

1. Set `USE_MOCK=false` if every request must carry a real API key.
2. Put the app behind HTTPS — API keys travel in request bodies.
3. Update the CORS `allow_origins` list in `backend/main.py` to your real
   frontend origin (it currently allows only localhost dev ports).
4. Give the backend container enough memory for large goal tables — analysis of
   500 employees runs 5 documents at a time in memory.

**Known limitation — single-tenant state.** Uploaded documents and analysis
results are held in module-level dictionaries in `backend/api/routes.py`. This is
fine for one analyst at a time, which is the intended use, but concurrent users
share and overwrite the same state. Multi-tenant use needs a per-session store
(Redis or a database) behind the same endpoints — the API surface would not
change.

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `500` on PDF upload | The `cffi` package is missing, which makes `cryptography` (a `pdfplumber` dependency) crash on import. Fix: `pip install -r backend/requirements.txt`. |
| `500` on PPTX upload | `python-pptx` not installed. Same fix as above. |
| Frontend container never starts | The backend health check is failing. Check `docker compose logs backend`. |
| Dashboard shows "Sample data" | No goal analyses exist yet. Upload a goals table and run the analysis; the banner disappears once real results load. |
| Coherence sections missing | Older analyses lacked coherence data. Re-run the analysis — both the offline and Claude-powered paths now produce it. |
| Scores differ between runs | Expected when switching between the offline heuristic analyzer and Claude. Compare like with like. |

---

## License

Internal project. All rights reserved.
