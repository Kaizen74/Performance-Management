"""
API Routes for SGAA Backend
FastAPI routes for document processing and analysis.
"""

import os
import uuid
import tempfile
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel

from processors import DocumentProcessor, GoalsTableProcessor
from analyzers import (
    StrategySynthesizer,
    AlignmentAnalyzer,
    GoalRecommendationEngine,
    ClaudeClient,
    MockClaudeClient,
    MockAlignmentClient,
    MockRecommendationClient,
)
from exports import ExcelExportEngine, PDFExportEngine


router = APIRouter()

# USE_MOCK controls behavior when NO API key is provided
# When an API key IS provided, always use the real Claude client
USE_MOCK = os.environ.get('USE_MOCK', 'true').lower() == 'true'


class APIKeyRequest(BaseModel):
    apiKey: str


class AnalyzeRequest(BaseModel):
    apiKey: str
    strategyDocumentIds: List[str]
    goalDocumentIds: List[str]


class DocumentResponse(BaseModel):
    documentId: str
    fileName: str
    documentType: str
    wordCount: int
    pageCount: int


# In-memory storage for demo (use database in production)
document_store = {}
framework_store = {}
analysis_store = {}
recommendation_store = {}


@router.post("/test-connection")
async def test_connection(request: APIKeyRequest):
    """Test API key connection."""
    # Use real Claude client if API key is provided, otherwise use mock
    if request.apiKey and request.apiKey.strip():
        try:
            client = ClaudeClient(api_key=request.apiKey)
            connected = client.test_connection()
            return {"connected": connected, "message": "Connection successful" if connected else "Connection failed"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif USE_MOCK:
        # Mock always succeeds for demo when no API key provided
        return {"connected": True, "message": "Connection successful (mock mode)"}
    else:
        raise HTTPException(status_code=400, detail="API key required")


@router.post("/upload/goals-table")
async def upload_goals_table(
    file: UploadFile = File(...)
):
    """
    Upload a CSV or Excel file containing employee goals from HR systems.
    The file should contain columns for employee name, goals, and optionally
    job title, department, and seniority level.
    """
    # Validate file extension
    allowed_extensions = ['.csv', '.xlsx', '.xls']
    file_ext = os.path.splitext(file.filename or '')[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Please upload CSV or Excel (.xlsx, .xls)"
        )

    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Process goals table
        processor = GoalsTableProcessor()
        processed_data = processor.process(tmp_path)

        # Convert to goal documents
        goal_documents = processor.to_goal_documents(processed_data)

        # Clear previous goal documents before adding new ones
        # This prevents accumulation across multiple uploads
        old_goal_ids = [
            doc_id for doc_id, doc in document_store.items()
            if doc.get('documentType') == 'goals'
        ]
        for doc_id in old_goal_ids:
            del document_store[doc_id]

        # Also clear previous analyses since we're uploading new goals
        analysis_store.clear()

        # Store all employee goal documents
        for doc in goal_documents:
            document_store[doc['documentId']] = doc

        # Clean up temp file (with retry for Windows file locking)
        try:
            os.unlink(tmp_path)
        except PermissionError:
            # On Windows, file may still be locked - schedule for cleanup later
            import gc
            gc.collect()  # Force garbage collection to release file handles
            try:
                os.unlink(tmp_path)
            except PermissionError:
                pass  # File will be cleaned up by OS temp cleanup

        return {
            "success": True,
            "fileName": file.filename,
            "employeeCount": processed_data['employeeCount'],
            "totalGoals": sum(emp.get('goalCount', 0) for emp in processed_data['employees']),
            "columnMapping": processed_data['columnMapping'],
            "employees": [
                {
                    "documentId": doc['documentId'],
                    "employeeName": doc['employeeMetadata'].get('employeeName'),
                    "jobTitle": doc['employeeMetadata'].get('jobTitle'),
                    "department": doc['employeeMetadata'].get('department'),
                    "seniorityLevel": doc['employeeMetadata'].get('seniorityLevel'),
                    "goalCount": doc['metadata'].get('goalCount', 0)
                }
                for doc in goal_documents
            ]
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/{document_type}")
async def upload_document(
    document_type: str,
    file: UploadFile = File(...)
):
    """Upload and process a document."""
    if document_type not in ['strategy', 'goals']:
        raise HTTPException(status_code=400, detail="Invalid document type")

    # Validate file extension
    allowed_extensions = ['.pdf', '.docx', '.pptx', '.xlsx']
    file_ext = os.path.splitext(file.filename or '')[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")

    try:
        # Clear previous documents of same type to prevent stale data
        if document_type == 'strategy':
            # Clear old strategy documents and framework
            old_strategy_ids = [
                doc_id for doc_id, doc in document_store.items()
                if doc.get('documentType') == 'strategy'
            ]
            for doc_id in old_strategy_ids:
                del document_store[doc_id]
            # Clear old framework since we're uploading new strategy
            framework_store.clear()

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Process document
        processor = DocumentProcessor()
        result = processor.extract(tmp_path, document_type=document_type)

        # Update filename
        result['fileName'] = file.filename

        # Store in memory
        document_store[result['documentId']] = result

        # Clean up temp file
        os.unlink(tmp_path)

        return {
            "documentId": result['documentId'],
            "fileName": result['fileName'],
            "documentType": result['documentType'],
            "wordCount": result['metadata']['wordCount'],
            "pageCount": result['metadata'].get('pageCount', 1),
            "sections": len(result['structuredSections']),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents():
    """List all uploaded documents."""
    return {
        "documents": [
            {
                "documentId": doc['documentId'],
                "fileName": doc['fileName'],
                "documentType": doc['documentType'],
                "wordCount": doc['metadata']['wordCount'],
                "employeeName": doc.get('employeeMetadata', {}).get('employeeName'),
            }
            for doc in document_store.values()
        ]
    }


@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Get document details."""
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    return document_store[document_id]


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document."""
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    del document_store[document_id]
    return {"deleted": True}


@router.post("/analyze/strategy")
async def analyze_strategy(api_key: str = Body(..., embed=True)):
    """Synthesize strategic framework from strategy documents."""
    strategy_docs = [
        doc for doc in document_store.values()
        if doc['documentType'] == 'strategy'
    ]

    if not strategy_docs:
        raise HTTPException(status_code=400, detail="No strategy documents uploaded")

    try:
        # Clear old framework data to prevent stale results
        framework_store.clear()

        # Use real Claude client if API key is provided, otherwise use mock
        if api_key and api_key.strip():
            client = ClaudeClient(api_key=api_key)
        elif USE_MOCK:
            client = MockClaudeClient()
        else:
            raise HTTPException(status_code=400, detail="API key required")

        synthesizer = StrategySynthesizer(claude_client=client)
        framework = synthesizer.analyze(strategy_docs)

        # Store framework
        framework_id = framework['metadata']['frameworkId']
        framework_store[framework_id] = framework

        return framework

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/goals")
async def analyze_goals(
    api_key: str = Body(...),
    framework_id: Optional[str] = Body(None)
):
    """Analyze goal documents against strategic framework."""
    goal_docs = [
        doc for doc in document_store.values()
        if doc['documentType'] == 'goals'
    ]

    if not goal_docs:
        raise HTTPException(status_code=400, detail="No goal documents uploaded")

    # Get framework
    if framework_id and framework_id in framework_store:
        framework = framework_store[framework_id]
    elif framework_store:
        framework = list(framework_store.values())[0]
    else:
        raise HTTPException(status_code=400, detail="No strategic framework available")

    try:
        # Use real Claude client if API key is provided, otherwise use mock
        if api_key and api_key.strip():
            client = ClaudeClient(api_key=api_key)
        elif USE_MOCK:
            client = MockAlignmentClient()
        else:
            raise HTTPException(status_code=400, detail="API key required")

        analyzer = AlignmentAnalyzer(framework, claude_client=client)
        analyses = analyzer.analyze_batch(goal_docs)

        # Store analyses
        for analysis in analyses:
            analysis_store[analysis['documentId']] = analysis

        # Calculate portfolio summary
        summary = analyzer.get_portfolio_summary(analyses)

        return {
            "analyses": analyses,
            "summary": summary,
            "gapAnalysis": analyzer.get_gap_analysis(analyses),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Store for portfolio recommendations
portfolio_recommendations_store = {}


# IMPORTANT: Portfolio routes must come BEFORE the {document_id} route
# to prevent FastAPI from matching "portfolio" as a document_id
@router.post("/recommendations/portfolio")
async def generate_portfolio_recommendations(
    api_key: str = Body(..., embed=True)
):
    """Generate portfolio-wide recommendations across all employees."""
    if not analysis_store:
        raise HTTPException(status_code=400, detail="No goal analyses available. Run goal analysis first.")

    if not framework_store:
        raise HTTPException(status_code=400, detail="No strategic framework available")

    framework = list(framework_store.values())[0]
    all_analyses = list(analysis_store.values())

    try:
        # Use real Claude client if API key is provided, otherwise use mock
        if api_key and api_key.strip():
            client = ClaudeClient(api_key=api_key)
        elif USE_MOCK:
            client = MockRecommendationClient()
        else:
            raise HTTPException(status_code=400, detail="API key required")

        # Generate portfolio recommendations
        recommendations = client.generate_portfolio_recommendations(framework, all_analyses)

        # Store for export
        portfolio_recommendations_store['latest'] = recommendations

        return recommendations

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/portfolio")
async def get_portfolio_recommendations():
    """Get the latest portfolio recommendations."""
    if 'latest' not in portfolio_recommendations_store:
        raise HTTPException(status_code=404, detail="No portfolio recommendations generated yet")
    return portfolio_recommendations_store['latest']


@router.post("/recommendations/{document_id}")
async def generate_recommendations(
    document_id: str,
    api_key: str = Body(..., embed=True)
):
    """Generate recommendations for a specific document."""
    if document_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found for document")

    analysis = analysis_store[document_id]

    # Get framework
    if not framework_store:
        raise HTTPException(status_code=400, detail="No strategic framework available")
    framework = list(framework_store.values())[0]

    try:
        # Use real Claude client if API key is provided, otherwise use mock
        if api_key and api_key.strip():
            client = ClaudeClient(api_key=api_key)
        elif USE_MOCK:
            client = MockRecommendationClient()
        else:
            raise HTTPException(status_code=400, detail="API key required")

        engine = GoalRecommendationEngine(claude_client=client)
        recommendations = engine.generate_recommendations(framework, analysis, analysis)

        # Store recommendations for export
        recommendation_store[document_id] = recommendations

        return recommendations

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/framework")
async def get_framework():
    """Get the current strategic framework."""
    if not framework_store:
        raise HTTPException(status_code=404, detail="No framework available")
    return list(framework_store.values())[0]


@router.get("/analyses")
async def list_analyses():
    """List all goal analyses."""
    return {"analyses": list(analysis_store.values())}


@router.get("/analyses/{document_id}")
async def get_analysis(document_id: str):
    """Get analysis for a specific document."""
    if document_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis_store[document_id]


@router.post("/reset")
async def reset_all():
    """Reset all stored data."""
    document_store.clear()
    framework_store.clear()
    analysis_store.clear()
    recommendation_store.clear()
    portfolio_recommendations_store.clear()
    return {"reset": True}


class ExportRequest(BaseModel):
    """Request body for export endpoints."""
    framework: Optional[dict] = None
    analyses: Optional[List[dict]] = None
    recommendations: Optional[dict] = None


@router.post("/export/excel")
async def export_excel(request: Optional[ExportRequest] = None):
    """Export all analyses to Excel workbook."""
    # Use request body data if provided, otherwise fall back to stores
    if request and request.framework and request.analyses:
        framework = request.framework
        analyses = request.analyses
        recs = request.recommendations or {}
    else:
        # Fall back to stored data
        if not framework_store:
            raise HTTPException(status_code=400, detail="No strategic framework available. Please provide data in request body or complete analysis first.")
        if not analysis_store:
            raise HTTPException(status_code=400, detail="No analyses available to export. Please provide data in request body or complete analysis first.")
        framework = list(framework_store.values())[0]
        analyses = list(analysis_store.values())
        recs = recommendation_store

    try:
        # Create temp file for export
        with tempfile.NamedTemporaryFile(
            suffix='.xlsx',
            prefix='sgaa_export_',
            delete=False
        ) as tmp:
            output_path = tmp.name

        # Generate Excel workbook
        engine = ExcelExportEngine(framework, analyses, recs)
        engine.generate_workbook(output_path)

        return FileResponse(
            path=output_path,
            filename="strategic_goal_alignment_analysis.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            background=None  # Don't delete file immediately
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/pdf")
async def export_pdf(request: Optional[ExportRequest] = None):
    """Export analysis summary to PDF report."""
    # Use request body data if provided, otherwise fall back to stores
    if request and request.framework and request.analyses:
        framework = request.framework
        analyses = request.analyses
        recs = request.recommendations or {}
    else:
        # Fall back to stored data
        if not framework_store:
            raise HTTPException(status_code=400, detail="No strategic framework available. Please provide data in request body or complete analysis first.")
        if not analysis_store:
            raise HTTPException(status_code=400, detail="No analyses available to export. Please provide data in request body or complete analysis first.")
        framework = list(framework_store.values())[0]
        analyses = list(analysis_store.values())
        recs = recommendation_store

    try:
        # Create temp file for export
        with tempfile.NamedTemporaryFile(
            suffix='.pdf',
            prefix='sgaa_report_',
            delete=False
        ) as tmp:
            output_path = tmp.name

        # Generate PDF report
        engine = PDFExportEngine(framework, analyses, recs)
        engine.generate_report(output_path)

        return FileResponse(
            path=output_path,
            filename="strategic_goal_alignment_report.pdf",
            media_type="application/pdf",
            background=None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/status")
async def export_status():
    """Get current export status and availability."""
    has_framework = len(framework_store) > 0
    has_analyses = len(analysis_store) > 0
    has_recommendations = len(recommendation_store) > 0

    return {
        "canExport": has_framework and has_analyses,
        "frameworkAvailable": has_framework,
        "analysesCount": len(analysis_store),
        "recommendationsCount": len(recommendation_store),
        "message": "Ready to export" if (has_framework and has_analyses) else "Complete analysis before exporting"
    }
