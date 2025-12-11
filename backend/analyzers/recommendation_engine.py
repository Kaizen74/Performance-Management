"""
Goal Recommendation Engine
Generates revised performance goals grounded in emerging practices.
"""

import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .claude_client import ClaudeClient


@dataclass
class RevisedGoal:
    """Structure for a revised goal recommendation."""
    objective: str
    keyResults: List[str]
    timeline: str
    metrics: List[str]


@dataclass
class Evidence:
    """Evidence supporting a recommendation."""
    source: str
    finding: str
    url: Optional[str] = None


@dataclass
class GoalRecommendation:
    """A single goal recommendation."""
    recommendationId: str
    revisedGoal: RevisedGoal
    strategicLinkages: List[str]
    predictedAlignmentGain: int
    evidence: Evidence
    implementationNotes: str


class GoalRecommendationEngine:
    """
    Generates improved performance goals based on strategic framework
    and alignment analysis. Uses Claude API with evidence-based reasoning.
    """

    RECOMMENDATIONS_COUNT = 5

    def __init__(
        self,
        claude_client: Optional[ClaudeClient] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the recommendation engine.

        Args:
            claude_client: Pre-configured Claude client (for testing)
            api_key: API key for Claude
        """
        if claude_client:
            self.client = claude_client
        elif api_key:
            self.client = ClaudeClient(api_key=api_key)
        else:
            self.client = ClaudeClient()

    def generate_recommendations(
        self,
        strategic_framework: Dict[str, Any],
        goal_document: Dict[str, Any],
        alignment_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate goal recommendations for a document.

        Args:
            strategic_framework: Strategic framework from StrategySynthesizer
            goal_document: Processed goal document with analysis
            alignment_analysis: Optional alignment analysis results

        Returns:
            Recommendations with projected improvements
        """
        document_text = goal_document.get('extractedText', '')
        current_score = goal_document.get('overallAlignmentScore', 50)

        if alignment_analysis is None:
            alignment_analysis = {
                'overallAlignmentScore': current_score,
                'overallImpactScore': goal_document.get('overallImpactScore', 50),
                'goals': goal_document.get('goals', []),
                'strategicCoverage': goal_document.get('strategicCoverage', {}),
                'recommendations': []
            }

        # Generate recommendations using Claude
        raw_recommendations = self.client.generate_recommendations(
            strategic_framework,
            document_text,
            alignment_analysis
        )

        # Validate and enhance recommendations
        recommendations = self._validate_recommendations(raw_recommendations)

        # Add metadata
        recommendations['documentId'] = goal_document.get('documentId', str(uuid.uuid4()))
        recommendations['metadata'] = {
            'generationTimestamp': datetime.utcnow().isoformat() + 'Z',
            'currentAlignmentScore': current_score,
            'recommendationCount': len(recommendations.get('recommendations', []))
        }

        return recommendations

    def _validate_recommendations(self, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and ensure recommendations have required structure.

        Args:
            recommendations: Raw recommendations from Claude

        Returns:
            Validated recommendations
        """
        # Ensure recommendations array
        if 'recommendations' not in recommendations:
            recommendations['recommendations'] = []

        for i, rec in enumerate(recommendations['recommendations']):
            if 'recommendationId' not in rec:
                rec['recommendationId'] = f"R{i+1}"

            # Ensure revised goal structure
            if 'revisedGoal' not in rec:
                rec['revisedGoal'] = {}

            goal = rec['revisedGoal']
            goal['objective'] = goal.get('objective', '')
            goal['keyResults'] = goal.get('keyResults', [])
            goal['timeline'] = goal.get('timeline', 'Q4 2025')
            goal['metrics'] = goal.get('metrics', [])

            # Ensure other fields
            rec['strategicLinkages'] = rec.get('strategicLinkages', [])
            rec['predictedAlignmentGain'] = self._clamp_gain(rec.get('predictedAlignmentGain', 10))

            # Ensure evidence
            if 'evidence' not in rec:
                rec['evidence'] = {}
            rec['evidence']['source'] = rec['evidence'].get('source', 'Best practices')
            rec['evidence']['finding'] = rec['evidence'].get('finding', '')

            rec['implementationNotes'] = rec.get('implementationNotes', '')

        # Ensure projected scores
        recommendations['projectedNewAlignmentScore'] = self._clamp_score(
            recommendations.get('projectedNewAlignmentScore', 75)
        )
        recommendations['projectedNewImpactScore'] = self._clamp_score(
            recommendations.get('projectedNewImpactScore', 70)
        )

        return recommendations

    def _clamp_score(self, score: int) -> int:
        """Clamp score to 0-100 range."""
        try:
            return max(0, min(100, int(score)))
        except (TypeError, ValueError):
            return 50

    def _clamp_gain(self, gain: int) -> int:
        """Clamp gain to reasonable range (0-50)."""
        try:
            return max(0, min(50, int(gain)))
        except (TypeError, ValueError):
            return 10

    def generate_batch_recommendations(
        self,
        strategic_framework: Dict[str, Any],
        analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for multiple documents.

        Args:
            strategic_framework: Strategic framework
            analyses: List of alignment analysis results

        Returns:
            List of recommendation sets
        """
        results = []
        for analysis in analyses:
            try:
                recommendations = self.generate_recommendations(
                    strategic_framework,
                    analysis,
                    analysis
                )
                results.append(recommendations)
            except Exception as e:
                results.append({
                    'documentId': analysis.get('documentId', str(uuid.uuid4())),
                    'error': str(e),
                    'recommendations': []
                })

        return results

    def prioritize_recommendations(
        self,
        recommendations: Dict[str, Any],
        framework: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Prioritize recommendations based on strategic importance.

        Args:
            recommendations: Generated recommendations
            framework: Strategic framework

        Returns:
            Sorted list of recommendations
        """
        recs = recommendations.get('recommendations', [])
        if not recs:
            return []

        # Get critical KPR objectives
        critical_objectives = set()
        for kpr in framework.get('keyPerformanceRequirements', []):
            if kpr.get('priority') == 'critical':
                critical_objectives.update(kpr.get('linkedObjectiveIds', []))

        # Score each recommendation
        def score_rec(rec):
            score = rec.get('predictedAlignmentGain', 0)
            # Bonus for linking to critical objectives
            for linkage in rec.get('strategicLinkages', []):
                if linkage in critical_objectives:
                    score += 10
            return score

        sorted_recs = sorted(recs, key=score_rec, reverse=True)
        return sorted_recs

    def get_coverage_improvement(
        self,
        current_coverage: Dict[str, Dict[str, Any]],
        recommendations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate expected coverage improvement from recommendations.

        Args:
            current_coverage: Current strategic coverage
            recommendations: Generated recommendations

        Returns:
            Coverage improvement analysis
        """
        # Collect new objective coverage from recommendations
        new_covered = set()
        for rec in recommendations.get('recommendations', []):
            new_covered.update(rec.get('strategicLinkages', []))

        # Map objectives to perspectives
        perspective_map = {
            'F': 'financial',
            'C': 'customer',
            'P': 'process',
            'I': 'process',
            'L': 'learning'
        }

        improvements = {}
        for perspective in ['financial', 'customer', 'process', 'learning']:
            current = current_coverage.get(perspective, {})
            current_pct = current.get('percentage', 0)
            total = current.get('total', 0)

            # Count new coverage for this perspective
            prefix = perspective[0].upper()
            if perspective == 'process':
                new_for_perspective = sum(
                    1 for obj_id in new_covered
                    if obj_id[0] in ['P', 'I']
                )
            else:
                new_for_perspective = sum(
                    1 for obj_id in new_covered
                    if obj_id[0] == prefix
                )

            # Calculate projected percentage
            if total > 0:
                projected_covered = min(total, current.get('covered', 0) + new_for_perspective)
                projected_pct = (projected_covered / total) * 100
            else:
                projected_pct = current_pct

            improvements[perspective] = {
                'current': round(current_pct, 1),
                'projected': round(projected_pct, 1),
                'improvement': round(projected_pct - current_pct, 1)
            }

        return improvements


class MockRecommendationClient:
    """
    Mock client for testing recommendation generation without API calls.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "mock-key"

    def generate_recommendations(
        self,
        strategic_framework: Dict[str, Any],
        current_goals: str,
        alignment_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Return mock recommendations."""
        current_score = alignment_analysis.get('overallAlignmentScore', 50)

        return {
            "recommendations": [
                {
                    "recommendationId": "R1",
                    "revisedGoal": {
                        "objective": "Lead digital transformation initiative for warehouse operations",
                        "keyResults": [
                            "Deploy AI-powered inventory forecasting by Q2",
                            "Achieve 25% reduction in stockouts",
                            "Train 100% of warehouse staff on new system"
                        ],
                        "timeline": "Q2 2025",
                        "metrics": ["System uptime", "Forecast accuracy", "Training completion rate"]
                    },
                    "strategicLinkages": ["P1", "L1", "C2"],
                    "predictedAlignmentGain": 15,
                    "evidence": {
                        "source": "McKinsey Digital Operations Report 2024",
                        "finding": "AI-driven forecasting reduces stockouts by 20-35%"
                    },
                    "implementationNotes": "Requires IT partnership and change management plan"
                },
                {
                    "recommendationId": "R2",
                    "revisedGoal": {
                        "objective": "Implement sustainability metrics in operations",
                        "keyResults": [
                            "Reduce carbon emissions per shipment by 15%",
                            "Achieve 90% waste diversion rate",
                            "Complete sustainability reporting framework"
                        ],
                        "timeline": "Q4 2025",
                        "metrics": ["Carbon per unit", "Waste diversion %", "Reporting compliance"]
                    },
                    "strategicLinkages": ["P2", "F2"],
                    "predictedAlignmentGain": 12,
                    "evidence": {
                        "source": "World Economic Forum Sustainability Report",
                        "finding": "Operational sustainability improves margin by 3-5%"
                    },
                    "implementationNotes": "Align with corporate sustainability team"
                },
                {
                    "recommendationId": "R3",
                    "revisedGoal": {
                        "objective": "Establish customer feedback loop for service improvement",
                        "keyResults": [
                            "Implement real-time delivery tracking with NPS survey",
                            "Achieve response rate of 30% on delivery feedback",
                            "Reduce customer complaints by 25%"
                        ],
                        "timeline": "Q3 2025",
                        "metrics": ["Survey response rate", "NPS score", "Complaint volume"]
                    },
                    "strategicLinkages": ["C1", "C2", "P3"],
                    "predictedAlignmentGain": 18,
                    "evidence": {
                        "source": "Harvard Business Review - Customer Feedback Systems",
                        "finding": "Real-time feedback improves NPS by 10-15 points"
                    },
                    "implementationNotes": "Requires CX team collaboration and IT support"
                },
                {
                    "recommendationId": "R4",
                    "revisedGoal": {
                        "objective": "Develop continuous improvement culture through Lean Six Sigma",
                        "keyResults": [
                            "Complete LSS Green Belt certification",
                            "Lead 3 improvement projects with measurable ROI",
                            "Train 5 team members in basic LSS tools"
                        ],
                        "timeline": "Q4 2025",
                        "metrics": ["Certifications", "Project ROI", "Team training hours"]
                    },
                    "strategicLinkages": ["L1", "L2", "P3"],
                    "predictedAlignmentGain": 10,
                    "evidence": {
                        "source": "ASQ Quality Progress Survey",
                        "finding": "LSS projects average 4:1 ROI"
                    },
                    "implementationNotes": "Budget needed for certification program"
                },
                {
                    "recommendationId": "R5",
                    "revisedGoal": {
                        "objective": "Drive cost optimization through process automation",
                        "keyResults": [
                            "Identify and automate 5 manual processes",
                            "Achieve $300K in annual cost savings",
                            "Improve process cycle time by 30%"
                        ],
                        "timeline": "Q4 2025",
                        "metrics": ["Processes automated", "Cost savings", "Cycle time"]
                    },
                    "strategicLinkages": ["F2", "P3", "P1"],
                    "predictedAlignmentGain": 14,
                    "evidence": {
                        "source": "Deloitte Automation Survey 2024",
                        "finding": "Process automation delivers 15-25% cost reduction"
                    },
                    "implementationNotes": "Cross-functional project requiring RPA tools"
                }
            ],
            "projectedNewAlignmentScore": min(100, current_score + 25),
            "projectedNewImpactScore": min(100, alignment_analysis.get('overallImpactScore', 50) + 20)
        }

    def test_connection(self) -> bool:
        return True
