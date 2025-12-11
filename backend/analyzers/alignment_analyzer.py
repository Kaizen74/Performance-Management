"""
Alignment Analyzer
Deep semantic analysis of employee goals against strategic framework.
"""

import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime

from .claude_client import ClaudeClient


@dataclass
class GoalAnalysis:
    """Analysis result for a single goal."""
    goalId: str
    goalText: str
    alignmentScore: int
    impactScore: int
    alignedObjectives: List[str]
    alignmentRationale: str
    impactRationale: str
    gaps: List[str]


@dataclass
class StrategicCoverage:
    """Coverage metrics for a strategic perspective."""
    covered: int
    total: int
    percentage: float


@dataclass
class DocumentAnalysis:
    """Complete analysis result for a goal document."""
    documentId: str
    fileName: str
    overallAlignmentScore: int
    overallImpactScore: int
    goals: List[GoalAnalysis]
    strategicCoverage: Dict[str, StrategicCoverage]
    recommendations: List[str]
    metadata: Dict[str, Any]


class AlignmentAnalyzer:
    """
    Analyzes alignment between employee goals and strategic framework.
    Uses Claude API for semantic analysis (not keyword matching).
    """

    MAX_GOAL_DOCUMENTS = 15
    PERSPECTIVES = ['financial', 'customer', 'process', 'learning']

    def __init__(
        self,
        strategic_framework: Dict[str, Any],
        claude_client: Optional[ClaudeClient] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the alignment analyzer.

        Args:
            strategic_framework: Strategic framework from StrategySynthesizer
            claude_client: Pre-configured Claude client (for testing)
            api_key: API key for Claude
        """
        self.framework = strategic_framework
        if claude_client:
            self.client = claude_client
        elif api_key:
            self.client = ClaudeClient(api_key=api_key)
        else:
            self.client = ClaudeClient()

    def analyze(self, goal_document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single goal document against the strategic framework.

        Args:
            goal_document: Processed goal document with 'extractedText'

        Returns:
            Analysis result with alignment and impact scores
        """
        document_text = goal_document.get('extractedText', '')
        file_name = goal_document.get('fileName', 'Unknown')

        if not document_text:
            raise ValueError("Goal document must contain extractedText")

        # Use Claude to analyze alignment
        raw_analysis = self.client.analyze_goal_alignment(
            self.framework,
            document_text
        )

        # Validate and enhance analysis
        analysis = self._validate_analysis(raw_analysis)

        # Calculate strategic coverage
        coverage = self._calculate_coverage(analysis)
        analysis['strategicCoverage'] = coverage

        # Add metadata
        analysis['documentId'] = str(uuid.uuid4())
        analysis['fileName'] = file_name
        analysis['metadata'] = {
            'analysisTimestamp': datetime.utcnow().isoformat() + 'Z',
            'goalCount': len(analysis.get('goals', [])),
            'frameworkId': self.framework.get('metadata', {}).get('frameworkId', 'unknown')
        }

        return analysis

    def analyze_batch(self, goal_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple goal documents.

        Args:
            goal_documents: List of processed goal documents

        Returns:
            List of analysis results
        """
        if len(goal_documents) > self.MAX_GOAL_DOCUMENTS:
            raise ValueError(f"Maximum {self.MAX_GOAL_DOCUMENTS} documents allowed")

        results = []
        for doc in goal_documents:
            try:
                result = self.analyze(doc)
                results.append(result)
            except Exception as e:
                results.append({
                    'documentId': str(uuid.uuid4()),
                    'fileName': doc.get('fileName', 'Unknown'),
                    'error': str(e),
                    'overallAlignmentScore': 0,
                    'overallImpactScore': 0,
                    'goals': [],
                    'strategicCoverage': {},
                    'recommendations': []
                })

        return results

    def _validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and ensure analysis has required structure.

        Args:
            analysis: Raw analysis from Claude

        Returns:
            Validated analysis
        """
        # Ensure overall scores
        analysis['overallAlignmentScore'] = self._clamp_score(
            analysis.get('overallAlignmentScore', 50)
        )
        analysis['overallImpactScore'] = self._clamp_score(
            analysis.get('overallImpactScore', 50)
        )

        # Ensure goals array
        if 'goals' not in analysis:
            analysis['goals'] = []

        for i, goal in enumerate(analysis['goals']):
            if 'goalId' not in goal:
                goal['goalId'] = f"G{i+1}"
            goal['goalText'] = goal.get('goalText', '')
            goal['alignmentScore'] = self._clamp_score(goal.get('alignmentScore', 50))
            goal['impactScore'] = self._clamp_score(goal.get('impactScore', 50))
            goal['alignedObjectives'] = goal.get('alignedObjectives', [])
            goal['alignmentRationale'] = goal.get('alignmentRationale', '')
            goal['impactRationale'] = goal.get('impactRationale', '')
            goal['gaps'] = goal.get('gaps', [])

        # Ensure recommendations
        if 'recommendations' not in analysis:
            analysis['recommendations'] = []

        return analysis

    def _clamp_score(self, score: int) -> int:
        """Clamp score to 0-100 range."""
        try:
            score = int(score)
            return max(0, min(100, score))
        except (TypeError, ValueError):
            return 50

    def _calculate_coverage(self, analysis: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate strategic coverage from goal alignments.

        Args:
            analysis: Goal analysis with aligned objectives

        Returns:
            Coverage metrics per perspective
        """
        # Get all objective IDs from framework
        objective_ids_by_perspective = self._get_objectives_by_perspective()

        # Collect all aligned objectives from goals
        aligned_ids = set()
        for goal in analysis.get('goals', []):
            aligned_ids.update(goal.get('alignedObjectives', []))

        # Calculate coverage per perspective
        coverage = {}
        perspective_map = {
            'financial': 'F',
            'customer': 'C',
            'process': ['P', 'I'],  # Process or Internal
            'learning': 'L'
        }

        for perspective, prefix in perspective_map.items():
            if isinstance(prefix, list):
                total_ids = [
                    oid for oid in objective_ids_by_perspective.get('internalProcess', [])
                ]
            else:
                total_ids = [
                    oid for oid in objective_ids_by_perspective.get(
                        self._perspective_key(perspective), []
                    )
                ]

            if not total_ids:
                coverage[perspective] = {
                    'covered': 0,
                    'total': 0,
                    'percentage': 0
                }
                continue

            covered_count = sum(1 for oid in total_ids if oid in aligned_ids)
            total_count = len(total_ids)
            percentage = (covered_count / total_count * 100) if total_count > 0 else 0

            coverage[perspective] = {
                'covered': covered_count,
                'total': total_count,
                'percentage': round(percentage, 1)
            }

        return coverage

    def _perspective_key(self, short_name: str) -> str:
        """Map short perspective names to framework keys."""
        mapping = {
            'financial': 'financial',
            'customer': 'customer',
            'process': 'internalProcess',
            'learning': 'learningGrowth'
        }
        return mapping.get(short_name, short_name)

    def _get_objectives_by_perspective(self) -> Dict[str, List[str]]:
        """Get objective IDs grouped by perspective."""
        objectives = {}
        perspectives = self.framework.get('strategicPerspectives', {})

        for p_name, p_data in perspectives.items():
            obj_ids = [obj['id'] for obj in p_data.get('objectives', []) if 'id' in obj]
            objectives[p_name] = obj_ids

        return objectives

    def calculate_tier(self, alignment_score: int, impact_score: int) -> Dict[str, str]:
        """
        Calculate tier based on alignment and impact scores.

        Args:
            alignment_score: Alignment score (0-100)
            impact_score: Impact score (0-100)

        Returns:
            Tier information with tier name, color, and label
        """
        composite = (alignment_score * 0.6) + (impact_score * 0.4)

        if composite >= 80:
            return {
                'tier': 'high',
                'color': 'teal',
                'label': 'Strong Strategic Fit',
                'composite': round(composite, 1)
            }
        elif composite >= 50:
            return {
                'tier': 'moderate',
                'color': 'amber',
                'label': 'Partial Alignment',
                'composite': round(composite, 1)
            }
        else:
            return {
                'tier': 'low',
                'color': 'rose',
                'label': 'Requires Revision',
                'composite': round(composite, 1)
            }

    def get_gap_analysis(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate gap analysis across all analyzed documents.

        Args:
            analyses: List of document analysis results

        Returns:
            Comprehensive gap analysis
        """
        all_objectives = self._get_objectives_by_perspective()

        # Collect all aligned objectives
        covered_objectives = set()
        for analysis in analyses:
            for goal in analysis.get('goals', []):
                covered_objectives.update(goal.get('alignedObjectives', []))

        # Find uncovered objectives
        uncovered = {}
        for p_name, obj_ids in all_objectives.items():
            uncovered_ids = [oid for oid in obj_ids if oid not in covered_objectives]
            if uncovered_ids:
                uncovered[p_name] = uncovered_ids

        # Find orphaned goals (low alignment)
        orphaned_goals = []
        for analysis in analyses:
            for goal in analysis.get('goals', []):
                if goal.get('alignmentScore', 0) < 30:
                    orphaned_goals.append({
                        'document': analysis.get('fileName'),
                        'goalId': goal.get('goalId'),
                        'goalText': goal.get('goalText', '')[:100]
                    })

        # Calculate overall coverage
        total_objectives = sum(len(ids) for ids in all_objectives.values())
        covered_count = len(covered_objectives)
        coverage_pct = (covered_count / total_objectives * 100) if total_objectives > 0 else 0

        return {
            'totalObjectives': total_objectives,
            'coveredObjectives': covered_count,
            'coveragePercentage': round(coverage_pct, 1),
            'uncoveredByPerspective': uncovered,
            'orphanedGoals': orphaned_goals,
            'criticalGaps': self._identify_critical_gaps(uncovered)
        }

    def _identify_critical_gaps(self, uncovered: Dict[str, List[str]]) -> List[str]:
        """Identify critical gaps in strategic coverage."""
        critical = []

        # Get KPRs from framework
        kprs = self.framework.get('keyPerformanceRequirements', [])
        critical_kprs = [k for k in kprs if k.get('priority') == 'critical']

        for kpr in critical_kprs:
            linked = kpr.get('linkedObjectiveIds', [])
            for obj_id in linked:
                for p_name, uncovered_ids in uncovered.items():
                    if obj_id in uncovered_ids:
                        critical.append(
                            f"Critical KPR '{kpr.get('requirement', '')[:50]}...' "
                            f"lacks goal coverage for objective {obj_id}"
                        )

        return critical

    def get_portfolio_summary(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate portfolio summary across all documents.

        Args:
            analyses: List of document analysis results

        Returns:
            Portfolio summary with rankings and statistics
        """
        valid_analyses = [a for a in analyses if 'error' not in a]

        if not valid_analyses:
            return {
                'totalDocuments': len(analyses),
                'validDocuments': 0,
                'averageAlignmentScore': 0,
                'averageImpactScore': 0,
                'tierDistribution': {},
                'topPerformers': [],
                'needsAttention': []
            }

        # Calculate averages
        avg_alignment = sum(a['overallAlignmentScore'] for a in valid_analyses) / len(valid_analyses)
        avg_impact = sum(a['overallImpactScore'] for a in valid_analyses) / len(valid_analyses)

        # Calculate tier distribution
        tier_dist = {'high': 0, 'moderate': 0, 'low': 0}
        for a in valid_analyses:
            tier = self.calculate_tier(a['overallAlignmentScore'], a['overallImpactScore'])
            tier_dist[tier['tier']] += 1

        # Identify top performers and needs attention
        sorted_by_alignment = sorted(valid_analyses, key=lambda x: x['overallAlignmentScore'], reverse=True)
        top_performers = [
            {'fileName': a['fileName'], 'alignmentScore': a['overallAlignmentScore']}
            for a in sorted_by_alignment[:3]
        ]
        needs_attention = [
            {'fileName': a['fileName'], 'alignmentScore': a['overallAlignmentScore']}
            for a in sorted_by_alignment[-3:] if a['overallAlignmentScore'] < 50
        ]

        return {
            'totalDocuments': len(analyses),
            'validDocuments': len(valid_analyses),
            'averageAlignmentScore': round(avg_alignment, 1),
            'averageImpactScore': round(avg_impact, 1),
            'tierDistribution': tier_dist,
            'topPerformers': top_performers,
            'needsAttention': needs_attention
        }


class MockAlignmentClient:
    """
    Mock client for testing alignment analysis without API calls.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "mock-key"

    def analyze_goal_alignment(
        self,
        strategic_framework: Dict[str, Any],
        goal_document_text: str
    ) -> Dict[str, Any]:
        """Return mock alignment analysis."""
        # Detect goals from text (simple parsing)
        goals = self._parse_goals(goal_document_text)

        return {
            "overallAlignmentScore": 72,
            "overallImpactScore": 68,
            "goals": goals,
            "recommendations": [
                "Add goals addressing customer perspective objectives",
                "Strengthen linkage to sustainability initiatives",
                "Include more measurable targets for learning objectives"
            ]
        }

    def _parse_goals(self, text: str) -> List[Dict[str, Any]]:
        """Simple goal detection from text."""
        goals = []
        lines = text.split('\n')

        goal_num = 0
        for line in lines:
            line_lower = line.lower().strip()
            # Look for lines that might be goals
            if (line_lower.startswith('goal') or
                line_lower.startswith('objective') or
                'reduce' in line_lower or
                'improve' in line_lower or
                'implement' in line_lower or
                'achieve' in line_lower or
                'complete' in line_lower):

                if len(line) > 20:  # Substantial text
                    goal_num += 1
                    goals.append({
                        "goalId": f"G{goal_num}",
                        "goalText": line.strip()[:200],
                        "alignmentScore": 70 + (goal_num % 20),
                        "impactScore": 65 + (goal_num % 25),
                        "alignedObjectives": self._assign_mock_objectives(goal_num),
                        "alignmentRationale": "Goal supports operational efficiency and process improvement",
                        "impactRationale": "Direct contribution to cost reduction targets",
                        "gaps": ["No direct link to customer satisfaction metrics"] if goal_num % 2 == 0 else []
                    })

        # Ensure at least some goals
        if not goals:
            goals = [
                {
                    "goalId": "G1",
                    "goalText": "Process improvement goal",
                    "alignmentScore": 75,
                    "impactScore": 70,
                    "alignedObjectives": ["P1", "P3"],
                    "alignmentRationale": "Supports operational efficiency",
                    "impactRationale": "Direct contribution to cost targets",
                    "gaps": []
                }
            ]

        return goals

    def _assign_mock_objectives(self, goal_num: int) -> List[str]:
        """Assign mock objective alignments."""
        objectives_pool = [
            ["P1", "P3"],
            ["P2", "L1"],
            ["C1", "C2"],
            ["F1", "P3"],
            ["L1", "L2"]
        ]
        return objectives_pool[goal_num % len(objectives_pool)]

    def test_connection(self) -> bool:
        return True
