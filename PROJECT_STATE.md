# Project State

**The single source of truth for where this project stands.** If this file and
anyone's memory disagree, this file wins.

- **Last updated:** 2026-08-10
- **Branch:** `claude/build-sgaa-app-01D4Ve5ACzbQiBeJk4yqcvfZ`
- **Status:** All milestones complete. Build is green and deployable.
- **Checks:** 132 of 132 backend tests passing · frontend type check clean ·
  production build succeeds.

---

## What the app does today

A working end-to-end tool. You upload your strategy documents, upload a
spreadsheet of employee goals from your HR system, and it tells you how well
each person's goals actually support the strategy — then exports the whole
analysis to Excel and PDF.

It runs free and offline out of the box using a built-in analyzer. Adding an
Anthropic API key in the app switches it to Claude-powered analysis.

See [README.md](README.md) for what it does in detail and how to run it.

---

## How to resume

```bash
git checkout claude/build-sgaa-app-01D4Ve5ACzbQiBeJk4yqcvfZ
./run_checks.sh
```

You want `ALL CHECKS PASSED ✅`. If anything is red, fix that before starting
new work — never build on a broken base.

---

## Done in the most recent session

| Area | What changed |
|---|---|
| **Seniority filter** | Dashboard and Excel export bucketed employees differently, so the same upload showed different headcounts in each view. Now share one contract, with an explicit "Seniority not stated" group. |
| **Docker deployment** | Backend health check called a package that was never installed, so the container never became healthy and the frontend never started. Fixed. |
| **README** | Did not exist. Now covers deployment, configuration, API, and troubleshooting. |
| **Design system** | Colour and font tokens were declared but unused; the favicon was a 404. Tokens now match what the app uses; accessibility floor added (focus rings, skip link, reduced-motion, screen-reader labels). |
| **Status docs** | `RESUME.md` and `SESSION_NOTES.md` contradicted the actual build and each other; folded into this file. |

Earlier in the same session: coherence/quadrant analysis restored for the
Claude-powered path (it previously only worked in offline mode), recommendation
engine field mismatches fixed, fabricated research citations replaced, temp-file
leaks closed, and the test suite grown from 83 passing / 16 failing to 132 / 0.

---

## Known limitations (deliberate, not bugs)

1. **Single analyst at a time.** Uploads and results live in memory in
   `backend/api/routes.py`. Two people using the same server at once will
   overwrite each other. Multi-user support needs a per-session store behind the
   same API — no endpoint changes required.
2. **No frontend unit tests.** The frontend is covered by type checking and a
   production build; behaviour is verified through the backend API contract
   tests. Adding Vitest is the natural next step.
3. **Offline analyzer is heuristic.** Without an API key, scoring uses keyword
   and pattern rules. It is consistent and free, but Claude-powered analysis is
   meaningfully better at judging whether a goal truly supports an objective.

---

## Suggested next session

Pick one:

- **Add frontend tests** (Vitest + Testing Library) — closes the last coverage
  gap; the seniority bucketing logic in `frontend/src/lib/seniority.ts` is a
  good first target.
- **Per-session state** — removes the single-user limitation above.
- **Sharpen the offline analyzer** — replace keyword matching for
  objective mapping with text similarity, so scores hold up on unusual wording.
