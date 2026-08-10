# Decisions

Every non-obvious choice, with the reason, newest first. The point is that a
future session (or a future you) can tell what was deliberate from what was
accidental.

---

## 2026-08-10

**Seniority is bucketed in one place, and "not stated" is its own group.**
The dashboard was treating missing seniority as "individual contributor" while
the Excel export dropped those people entirely — the same upload reported
different headcounts in different views. `frontend/src/lib/seniority.ts` is now
the single contract, and unknown seniority is reported honestly rather than
guessed. Rejected the alternative of defaulting unknowns to IC: it silently
overstates one group and hides missing HR data.

**The frontend trusts the backend's seniority values instead of re-deriving.**
The backend already emits exactly three canonical values. The frontend was
re-classifying them with 25+ fuzzy substring patterns (`gm`, `lead`, `head`),
which is fragile and duplicates logic. Fuzzy matching is kept only as a fallback
for free-text values from other sources.

**Python packaging patterns in `.gitignore` are anchored to the repo root.**
Unanchored `lib/` matches at any depth and was silently excluding
`frontend/src/lib/` — real source code would never have been committed.

**Docker health checks use stdlib `urllib`, not `requests`.**
`requests` was never in `requirements.txt`, so the health check could never
pass; because compose gates the frontend on `service_healthy`, the whole stack
failed to come up. Using the standard library removes the dependency entirely.

**`uuid` removed from `requirements.txt`.**
It is a Python standard-library module. The PyPI package of the same name is a
Python 2 backport that can shadow it and break installs.

**One font family, and tokens that describe reality.**
A "Clash Display" family was configured but never loaded or referenced, so every
`font-display` class silently fell back to the system stack. Removed rather than
loaded: a second webfont costs load time and the app is data-dense, where a
display face adds little. Brand colour tokens were rewritten to match the blue
the app actually uses.

**Status docs consolidated into `PROJECT_STATE.md`.**
`RESUME.md` claimed work was at "Milestone 2" long after everything shipped, and
`SESSION_NOTES.md` described a Node/Express backend that was never built. Three
overlapping, contradictory files is worse than one accurate one.

**Coherence and quadrant analysis is computed server-side for both paths.**
The Claude-powered path never returned `coherenceIndex` or per-goal quadrant
classification, so the app's headline features silently vanished whenever a real
API key was used. `AlignmentAnalyzer` now derives them when the client does not
supply them, keeping both paths schema-identical.

**Recommendation evidence cites frameworks, not invented statistics.**
The offline engine attributed specific made-up percentages to Harvard Business
Review and MIT Sloan. Replaced with principle-level grounding in real published
work (Locke & Latham, Doerr, Kaplan & Norton). A fabricated citation in an HR
deliverable is a credibility risk with no upside.

**Recommendations are treated as drafts the employee adapts.**
Goal-commitment research finds that goals written *for* someone undermine
ownership unless they adapt them. Every recommendation now says so explicitly.

---

## Earlier

**Goal document cap raised from 15 to 500.**
The tool is used for portfolio-level reviews across a whole department, not a
handful of files. Analysis runs 5 documents at a time to respect API rate limits.

**Mock/offline analyzer kept as a first-class path, not test scaffolding.**
It lets someone trial the entire workflow at zero cost and with no API key,
which is how most evaluations start.

**Model tier is chosen by employee seniority.**
Senior employees' goals get the stronger model; everyone else gets the faster,
cheaper one. Keeps portfolio-scale runs affordable without flattening quality
where it matters most.

**API keys are never persisted server-side.**
Entered in the UI, held in browser memory, sent per request, discarded. Avoids
becoming a credential store.
