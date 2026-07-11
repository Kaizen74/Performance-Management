"""
API Route Smoke Tests
Exercises the real end-to-end path (upload -> synthesize -> analyze ->
recommend -> export) through the FastAPI app in mock mode, asserting the
response fields the frontend (AnalysisContext.tsx) depends on.
"""

import io
import os
import sys
from pathlib import Path

import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from fastapi.testclient import TestClient

from main import app
from api import routes


STRATEGY_TEXT = """
VISION: To be the leading sustainable logistics provider in Asia-Pacific by 2030.

MISSION: We deliver excellence through innovation, connecting businesses to opportunities.

STRATEGIC PRIORITIES:
1. Digital Transformation - Implement AI-driven route optimization
2. Customer Excellence - NPS > 70 across all segments
3. Operational Efficiency - 15% reduction in unit costs
4. Talent Development - Build future-ready workforce with digital skills

CORE VALUES:
- Innovation: We embrace change and continuously seek better solutions
- Integrity: We act with honesty and transparency
"""

GOALS_CSV = (
    "Employee Name,Job Title,Department,Goal 1,Goal 1 Weight,Goal 2,Goal 2 Weight\n"
    "Alice Tan,Operations Manager,Operations,"
    "\"Reduce unit processing costs by 15% by Q4 through automation\",50,"
    "\"Achieve NPS of 72 for internal service delivery\",50\n"
    "Ben Lim,Analyst,Finance,"
    "\"Attend weekly finance meetings\",40,"
    "\"Complete monthly reports on time\",60\n"
)


def _make_strategy_docx() -> bytes:
    """Build a minimal strategy DOCX in memory."""
    from docx import Document

    doc = Document()
    for line in STRATEGY_TEXT.strip().split('\n'):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@pytest.fixture()
def client():
    """TestClient with clean server-side stores per test."""
    routes.document_store.clear()
    routes.framework_store.clear()
    routes.analysis_store.clear()
    routes.recommendation_store.clear()
    routes.portfolio_recommendations_store.clear()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def analyzed_client(client):
    """Client with strategy uploaded+synthesized and goals uploaded+analyzed."""
    resp = client.post(
        "/api/upload/strategy",
        files={"file": ("strategy.docx", _make_strategy_docx(),
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert resp.status_code == 200, resp.text

    resp = client.post("/api/analyze/strategy", json={"api_key": ""})
    assert resp.status_code == 200, resp.text

    resp = client.post(
        "/api/upload/goals-table",
        files={"file": ("goals.csv", GOALS_CSV.encode(), "text/csv")},
    )
    assert resp.status_code == 200, resp.text

    resp = client.post("/api/analyze/goals", json={"api_key": "", "framework_id": None})
    assert resp.status_code == 200, resp.text
    client.goals_response = resp.json()
    return client


class TestHealthAndConnection:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_connection_mock_mode(self, client):
        resp = client.post("/api/test-connection", json={"apiKey": ""})
        assert resp.status_code == 200
        assert resp.json()["connected"] is True


class TestUploadEndpoints:
    def test_upload_goals_table_csv(self, client):
        resp = client.post(
            "/api/upload/goals-table",
            files={"file": ("goals.csv", GOALS_CSV.encode(), "text/csv")},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["employeeCount"] == 2
        names = {e["employeeName"] for e in data["employees"]}
        assert names == {"Alice Tan", "Ben Lim"}

    def test_upload_goals_table_rejects_bad_extension(self, client):
        resp = client.post(
            "/api/upload/goals-table",
            files={"file": ("goals.txt", b"not a table", "text/plain")},
        )
        assert resp.status_code == 400

    def test_upload_strategy_docx(self, client):
        resp = client.post(
            "/api/upload/strategy",
            files={"file": ("strategy.docx", _make_strategy_docx(),
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["documentType"] == "strategy"
        assert data["wordCount"] > 0

    def test_upload_invalid_document_type(self, client):
        resp = client.post(
            "/api/upload/nonsense",
            files={"file": ("strategy.docx", _make_strategy_docx(),
                            "application/octet-stream")},
        )
        assert resp.status_code == 400


class TestAnalysisContract:
    """Assert the response schema the frontend AnalysisContext depends on."""

    def test_strategy_framework_contract(self, analyzed_client):
        framework = list(routes.framework_store.values())[0]
        # Fields consumed by StrategicFrameworkView / AnalysisContext
        assert 'organizationalPurpose' in framework
        assert 'strategicPerspectives' in framework
        assert 'strategicThemes' in framework
        assert 'keyPerformanceRequirements' in framework
        assert framework.get('strategyScope') in ('organization', 'department', 'team')
        for p in ('financial', 'customer', 'internalProcess', 'learningGrowth'):
            assert framework['strategicPerspectives'][p]['objectives']

    def test_goals_analysis_contract(self, analyzed_client):
        data = analyzed_client.goals_response
        assert 'analyses' in data and 'summary' in data and 'gapAnalysis' in data
        assert len(data['analyses']) == 2

        for analysis in data['analyses']:
            # Core scores
            assert 0 <= analysis['overallAlignmentScore'] <= 100
            assert 0 <= analysis['overallImpactScore'] <= 100
            # Headline coherence features (DocumentScorecard / dashboard / PDF)
            assert 'coherenceIndex' in analysis
            assert 'quadrantDistribution' in analysis['coherenceIndex']
            assert 'strategicNarrative' in analysis
            # Per-goal quadrant classification
            for goal in analysis['goals']:
                qc = goal['quadrantClassification']
                assert qc['quadrant'] in (
                    'Strategic Driver', 'Busy Work Trap', 'Rogue Project', 'Distraction'
                )
            # Employee context from the goals table flows through
            assert analysis['employeeContext']['employeeName'] in ('Alice Tan', 'Ben Lim')

    def test_recommendations_contract(self, analyzed_client):
        analysis = list(routes.analysis_store.values())[0]
        resp = analyzed_client.post(
            f"/api/recommendations/{analysis['documentId']}",
            json={"api_key": ""},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        recs = data['recommendations']
        assert len(recs) >= 1
        for rec in recs:
            assert rec['originalClassification'] in (
                'Strategic Driver', 'Busy Work Trap', 'Rogue Project', 'Distraction'
            )
            assert 'revisedGoal' in rec
            assert 'evidence' in rec


class TestExportEndpoints:
    def test_export_status(self, analyzed_client):
        resp = analyzed_client.get("/api/export/status")
        assert resp.status_code == 200
        assert resp.json()["canExport"] is True

    def test_export_excel_and_cleanup(self, analyzed_client):
        resp = analyzed_client.post("/api/export/excel")
        assert resp.status_code == 200, resp.text
        assert len(resp.content) > 1000
        assert resp.content[:2] == b'PK'  # xlsx is a zip

    def test_export_pdf_and_cleanup(self, analyzed_client):
        resp = analyzed_client.post("/api/export/pdf")
        assert resp.status_code == 200, resp.text
        assert resp.content[:4] == b'%PDF'

    def test_export_temp_files_removed(self, analyzed_client):
        import glob
        before = set(glob.glob(os.path.join(tempfile_dir(), 'sgaa_*')))
        analyzed_client.post("/api/export/pdf")
        analyzed_client.post("/api/export/excel")
        after = set(glob.glob(os.path.join(tempfile_dir(), 'sgaa_*')))
        assert after - before == set(), "export temp files were not cleaned up"


def tempfile_dir() -> str:
    import tempfile
    return tempfile.gettempdir()


class TestResetEndpoint:
    def test_reset_clears_stores(self, analyzed_client):
        assert routes.document_store and routes.framework_store
        resp = analyzed_client.post("/api/reset")
        assert resp.status_code == 200
        assert not routes.document_store
        assert not routes.framework_store
        assert not routes.analysis_store
