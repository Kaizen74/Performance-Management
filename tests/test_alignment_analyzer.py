"""
Test Suite for Alignment Analyzer (Milestone 3)
Tests goal alignment analysis against strategic framework.
"""

import os
import sys
import pytest
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from analyzers.alignment_analyzer import AlignmentAnalyzer, MockAlignmentClient
from analyzers.strategy_synthesizer import MockClaudeClient


# Mock goal document
MOCK_GOAL_DOCUMENT = """
Employee: Jane Smith, Operations Manager

FY2025 Goals:
1. Reduce warehouse processing time by 20% through lean methodology
2. Implement new inventory management system by Q2
3. Achieve team engagement score of 4.2/5.0
4. Complete Six Sigma Green Belt certification
5. Identify and implement cost savings of $250,000
"""

# Mock strategic framework (simplified)
MOCK_FRAMEWORK = {
    "organizationalPurpose": {
        "vision": "Leading sustainable logistics provider",
        "mission": "Excellence through innovation",
        "values": ["Innovation", "Sustainability", "Excellence"]
    },
    "strategicPerspectives": {
        "financial": {
            "objectives": [
                {"id": "F1", "objective": "Revenue growth 12%", "keyMeasures": ["Revenue"], "strategicThemes": ["Growth"]},
                {"id": "F2", "objective": "Cost reduction 15%", "keyMeasures": ["Cost"], "strategicThemes": ["Efficiency"]}
            ]
        },
        "customer": {
            "objectives": [
                {"id": "C1", "objective": "NPS > 70", "keyMeasures": ["NPS"], "strategicThemes": ["Customer"]},
                {"id": "C2", "objective": "On-time delivery 95%", "keyMeasures": ["Delivery"], "strategicThemes": ["Quality"]}
            ]
        },
        "internalProcess": {
            "objectives": [
                {"id": "P1", "objective": "AI route optimization", "keyMeasures": ["Efficiency"], "strategicThemes": ["Digital"]},
                {"id": "P2", "objective": "Carbon neutrality 2028", "keyMeasures": ["Emissions"], "strategicThemes": ["Sustainability"]},
                {"id": "P3", "objective": "Operational efficiency", "keyMeasures": ["Cost per unit"], "strategicThemes": ["Efficiency"]}
            ]
        },
        "learningGrowth": {
            "objectives": [
                {"id": "L1", "objective": "Digital capabilities", "keyMeasures": ["Skills"], "strategicThemes": ["Digital"]},
                {"id": "L2", "objective": "Employee engagement 80%", "keyMeasures": ["Engagement"], "strategicThemes": ["Culture"]}
            ]
        }
    },
    "strategicThemes": [
        {"themeId": "T1", "name": "Digital Transformation", "linkedObjectives": ["P1", "L1"]},
        {"themeId": "T2", "name": "Sustainability", "linkedObjectives": ["P2"]},
        {"themeId": "T3", "name": "Operational Excellence", "linkedObjectives": ["F2", "P3"]}
    ],
    "keyPerformanceRequirements": [
        {"id": "KPR1", "requirement": "Drive digital transformation", "perspective": "process", "priority": "critical", "linkedObjectiveIds": ["P1", "L1"]},
        {"id": "KPR2", "requirement": "Achieve sustainability targets", "perspective": "process", "priority": "critical", "linkedObjectiveIds": ["P2"]}
    ],
    "metadata": {
        "frameworkId": "test-framework-001"
    }
}


class TestAlignmentAnalyzer:
    """Test cases for the AlignmentAnalyzer class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.mock_client = MockAlignmentClient()
        self.analyzer = AlignmentAnalyzer(
            strategic_framework=MOCK_FRAMEWORK,
            claude_client=self.mock_client
        )

    def test_analyzer_initialization(self):
        """Test that AlignmentAnalyzer initializes correctly."""
        analyzer = AlignmentAnalyzer(MOCK_FRAMEWORK, claude_client=self.mock_client)
        assert analyzer is not None
        assert analyzer.framework is not None
        assert analyzer.client is not None

    def test_analyze_single_document(self):
        """Test analysis of a single goal document."""
        document = {
            'fileName': 'jane_goals.docx',
            'extractedText': MOCK_GOAL_DOCUMENT,
            'structuredSections': []
        }

        result = self.analyzer.analyze(document)

        # Validate basic structure
        assert 'documentId' in result
        assert 'fileName' in result
        assert 'overallAlignmentScore' in result
        assert 'overallImpactScore' in result
        assert 'goals' in result
        assert 'strategicCoverage' in result
        assert 'recommendations' in result
        assert 'metadata' in result

        print(f"Single document analysis passed: {result['overallAlignmentScore']} alignment")

    def test_score_ranges(self):
        """Test that scores are within valid ranges."""
        document = {
            'fileName': 'goals.docx',
            'extractedText': MOCK_GOAL_DOCUMENT
        }

        result = self.analyzer.analyze(document)

        # Check overall scores
        assert 0 <= result['overallAlignmentScore'] <= 100
        assert 0 <= result['overallImpactScore'] <= 100

        # Check individual goal scores
        for goal in result['goals']:
            assert 0 <= goal['alignmentScore'] <= 100
            assert 0 <= goal['impactScore'] <= 100

        print("Score range validation passed")

    def test_goal_structure(self):
        """Test that goals have required fields."""
        document = {
            'fileName': 'goals.docx',
            'extractedText': MOCK_GOAL_DOCUMENT
        }

        result = self.analyzer.analyze(document)

        assert len(result['goals']) > 0, "Should identify at least one goal"

        for goal in result['goals']:
            assert 'goalId' in goal
            assert 'goalText' in goal
            assert 'alignmentScore' in goal
            assert 'impactScore' in goal
            assert 'alignedObjectives' in goal
            assert 'alignmentRationale' in goal
            assert 'impactRationale' in goal
            assert 'gaps' in goal

        print(f"Goal structure validation passed: {len(result['goals'])} goals")

    def test_aligned_objectives_format(self):
        """Test that aligned objectives reference valid IDs."""
        document = {
            'fileName': 'goals.docx',
            'extractedText': MOCK_GOAL_DOCUMENT
        }

        result = self.analyzer.analyze(document)

        for goal in result['goals']:
            for obj_id in goal['alignedObjectives']:
                # Should be valid format (F1, C1, P1, L1, etc.)
                assert len(obj_id) >= 2
                assert obj_id[0] in ['F', 'C', 'P', 'I', 'L']

        print("Aligned objectives format validation passed")

    def test_strategic_coverage_calculation(self):
        """Test strategic coverage is calculated correctly."""
        document = {
            'fileName': 'goals.docx',
            'extractedText': MOCK_GOAL_DOCUMENT
        }

        result = self.analyzer.analyze(document)
        coverage = result['strategicCoverage']

        required_perspectives = ['financial', 'customer', 'process', 'learning']
        for perspective in required_perspectives:
            assert perspective in coverage, f"Missing perspective: {perspective}"
            assert 'covered' in coverage[perspective]
            assert 'total' in coverage[perspective]
            assert 'percentage' in coverage[perspective]
            assert 0 <= coverage[perspective]['percentage'] <= 100

        print(f"Strategic coverage: {coverage}")

    def test_tier_calculation(self):
        """Test tier calculation based on scores."""
        # High tier
        tier = self.analyzer.calculate_tier(85, 80)
        assert tier['tier'] == 'high'
        assert tier['color'] == 'teal'

        # Moderate tier
        tier = self.analyzer.calculate_tier(60, 55)
        assert tier['tier'] == 'moderate'
        assert tier['color'] == 'amber'

        # Low tier
        tier = self.analyzer.calculate_tier(30, 25)
        assert tier['tier'] == 'low'
        assert tier['color'] == 'rose'

        print("Tier calculation passed")

    def test_batch_analysis(self):
        """Test batch analysis of multiple documents."""
        documents = [
            {'fileName': 'goals1.docx', 'extractedText': MOCK_GOAL_DOCUMENT},
            {'fileName': 'goals2.docx', 'extractedText': 'Improve customer satisfaction by 10%'},
            {'fileName': 'goals3.docx', 'extractedText': 'Complete leadership training'}
        ]

        results = self.analyzer.analyze_batch(documents)

        assert len(results) == 3
        for result in results:
            assert 'fileName' in result
            assert 'overallAlignmentScore' in result or 'error' in result

        print(f"Batch analysis passed: {len(results)} documents")

    def test_max_documents_limit(self):
        """Test that document limit is enforced."""
        documents = [
            {'fileName': f'goals{i}.docx', 'extractedText': 'Goal text'}
            for i in range(16)
        ]

        with pytest.raises(ValueError) as exc_info:
            self.analyzer.analyze_batch(documents)

        assert 'Maximum' in str(exc_info.value)

        print("Document limit enforcement passed")

    def test_empty_document_rejected(self):
        """Test that empty documents are rejected."""
        document = {
            'fileName': 'empty.docx',
            'extractedText': ''
        }

        with pytest.raises(ValueError):
            self.analyzer.analyze(document)

        print("Empty document rejection passed")

    def test_recommendations_generated(self):
        """Test that recommendations are generated."""
        document = {
            'fileName': 'goals.docx',
            'extractedText': MOCK_GOAL_DOCUMENT
        }

        result = self.analyzer.analyze(document)

        assert 'recommendations' in result
        assert isinstance(result['recommendations'], list)

        print(f"Recommendations: {len(result['recommendations'])} items")

    def test_gap_analysis(self):
        """Test gap analysis across multiple documents."""
        documents = [
            {'fileName': 'goals1.docx', 'extractedText': MOCK_GOAL_DOCUMENT}
        ]

        results = self.analyzer.analyze_batch(documents)
        gaps = self.analyzer.get_gap_analysis(results)

        assert 'totalObjectives' in gaps
        assert 'coveredObjectives' in gaps
        assert 'coveragePercentage' in gaps
        assert 'uncoveredByPerspective' in gaps
        assert 'orphanedGoals' in gaps

        print(f"Gap analysis: {gaps['coveragePercentage']}% coverage")

    def test_portfolio_summary(self):
        """Test portfolio summary generation."""
        documents = [
            {'fileName': 'goals1.docx', 'extractedText': MOCK_GOAL_DOCUMENT},
            {'fileName': 'goals2.docx', 'extractedText': 'Reduce costs by 20%'}
        ]

        results = self.analyzer.analyze_batch(documents)
        summary = self.analyzer.get_portfolio_summary(results)

        assert 'totalDocuments' in summary
        assert 'validDocuments' in summary
        assert 'averageAlignmentScore' in summary
        assert 'averageImpactScore' in summary
        assert 'tierDistribution' in summary
        assert 'topPerformers' in summary
        assert 'needsAttention' in summary

        print(f"Portfolio summary: avg alignment {summary['averageAlignmentScore']}")

    def test_metadata_included(self):
        """Test that analysis metadata is included."""
        document = {
            'fileName': 'goals.docx',
            'extractedText': MOCK_GOAL_DOCUMENT
        }

        result = self.analyzer.analyze(document)

        assert 'metadata' in result
        assert 'analysisTimestamp' in result['metadata']
        assert 'goalCount' in result['metadata']

        print(f"Metadata: {result['metadata']}")


class TestMockAlignmentClient:
    """Test the mock client for testing infrastructure."""

    def test_mock_client_initialization(self):
        """Test mock client initializes correctly."""
        client = MockAlignmentClient()
        assert client is not None

    def test_mock_analyze_alignment(self):
        """Test mock alignment analysis returns valid structure."""
        client = MockAlignmentClient()
        result = client.analyze_goal_alignment(MOCK_FRAMEWORK, MOCK_GOAL_DOCUMENT)

        assert 'overallAlignmentScore' in result
        assert 'overallImpactScore' in result
        assert 'goals' in result
        assert 'recommendations' in result

    def test_mock_goal_parsing(self):
        """Test mock client parses goals from text."""
        client = MockAlignmentClient()
        result = client.analyze_goal_alignment(MOCK_FRAMEWORK, MOCK_GOAL_DOCUMENT)

        assert len(result['goals']) >= 1
        for goal in result['goals']:
            assert 'goalId' in goal
            assert 'goalText' in goal

        print(f"Mock parsed {len(result['goals'])} goals")


def run_manual_tests():
    """Run tests manually for debugging."""
    print("=" * 60)
    print("MILESTONE 3: Alignment Analyzer Tests")
    print("=" * 60)

    mock_client = MockAlignmentClient()
    analyzer = AlignmentAnalyzer(MOCK_FRAMEWORK, claude_client=mock_client)

    document = {
        'fileName': 'jane_goals.docx',
        'extractedText': MOCK_GOAL_DOCUMENT
    }

    print("\n--- Analyzing Goal Document ---")
    result = analyzer.analyze(document)

    print(f"\nOverall Alignment Score: {result['overallAlignmentScore']}")
    print(f"Overall Impact Score: {result['overallImpactScore']}")
    print(f"Goals Analyzed: {len(result['goals'])}")

    tier = analyzer.calculate_tier(result['overallAlignmentScore'], result['overallImpactScore'])
    print(f"Tier: {tier['tier']} ({tier['label']})")

    print("\nStrategic Coverage:")
    for perspective, coverage in result['strategicCoverage'].items():
        print(f"  {perspective}: {coverage['covered']}/{coverage['total']} ({coverage['percentage']}%)")

    print("\nRecommendations:")
    for rec in result['recommendations'][:3]:
        print(f"  - {rec[:80]}...")

    print("\n" + "=" * 60)
    print("All manual tests completed!")


if __name__ == '__main__':
    run_manual_tests()
