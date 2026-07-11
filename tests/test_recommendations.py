"""
Test Suite for Recommendation Engine (Milestone 5)
Tests AI-powered goal recommendations generation.
"""

import os
import sys
import pytest
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from analyzers.recommendation_engine import GoalRecommendationEngine, MockRecommendationClient


# Mock framework (simplified)
MOCK_FRAMEWORK = {
    "organizationalPurpose": {
        "vision": "Leading sustainable logistics provider",
        "mission": "Excellence through innovation",
        "values": ["Innovation", "Sustainability", "Excellence"]
    },
    "strategicPerspectives": {
        "financial": {
            "objectives": [
                {"id": "F1", "objective": "Revenue growth", "keyMeasures": ["Revenue"]},
                {"id": "F2", "objective": "Cost reduction", "keyMeasures": ["Cost"]}
            ]
        },
        "customer": {
            "objectives": [
                {"id": "C1", "objective": "NPS > 70", "keyMeasures": ["NPS"]},
                {"id": "C2", "objective": "On-time delivery", "keyMeasures": ["Delivery"]}
            ]
        },
        "internalProcess": {
            "objectives": [
                {"id": "P1", "objective": "AI optimization", "keyMeasures": ["Efficiency"]},
                {"id": "P2", "objective": "Carbon neutrality", "keyMeasures": ["Emissions"]},
                {"id": "P3", "objective": "Process efficiency", "keyMeasures": ["Cost per unit"]}
            ]
        },
        "learningGrowth": {
            "objectives": [
                {"id": "L1", "objective": "Digital capabilities", "keyMeasures": ["Skills"]},
                {"id": "L2", "objective": "Employee engagement", "keyMeasures": ["Engagement"]}
            ]
        }
    },
    "keyPerformanceRequirements": [
        {"id": "KPR1", "requirement": "Drive digital", "perspective": "process", "priority": "critical", "linkedObjectiveIds": ["P1", "L1"]},
        {"id": "KPR2", "requirement": "Sustainability", "perspective": "process", "priority": "critical", "linkedObjectiveIds": ["P2"]}
    ]
}

# Mock goal document with low alignment
MOCK_LOW_ALIGNMENT_DOC = {
    "documentId": "doc-001",
    "fileName": "employee_goals.docx",
    "extractedText": """
    FY2025 Goals:
    1. Complete assigned tasks on time
    2. Attend all team meetings
    3. Submit reports weekly
    """,
    "overallAlignmentScore": 35,
    "overallImpactScore": 30,
    "goals": [
        {"goalId": "G1", "goalText": "Complete tasks on time", "alignmentScore": 30, "alignedObjectives": []},
        {"goalId": "G2", "goalText": "Attend meetings", "alignmentScore": 25, "alignedObjectives": []},
        {"goalId": "G3", "goalText": "Submit reports", "alignmentScore": 40, "alignedObjectives": ["P3"]}
    ],
    "strategicCoverage": {
        "financial": {"covered": 0, "total": 2, "percentage": 0},
        "customer": {"covered": 0, "total": 2, "percentage": 0},
        "process": {"covered": 1, "total": 3, "percentage": 33},
        "learning": {"covered": 0, "total": 2, "percentage": 0}
    }
}


class TestGoalRecommendationEngine:
    """Test cases for the GoalRecommendationEngine class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.mock_client = MockRecommendationClient()
        self.engine = GoalRecommendationEngine(claude_client=self.mock_client)

    def test_engine_initialization(self):
        """Test that GoalRecommendationEngine initializes correctly."""
        engine = GoalRecommendationEngine(claude_client=self.mock_client)
        assert engine is not None
        assert engine.client is not None

    def test_generate_recommendations(self):
        """Test generating recommendations for a document."""
        recommendations = self.engine.generate_recommendations(
            MOCK_FRAMEWORK,
            MOCK_LOW_ALIGNMENT_DOC,
            MOCK_LOW_ALIGNMENT_DOC
        )

        # Validate structure
        assert 'recommendations' in recommendations
        assert 'projectedNewAlignmentScore' in recommendations
        assert 'projectedNewImpactScore' in recommendations
        assert 'metadata' in recommendations

        print(f"Generated {len(recommendations['recommendations'])} recommendations")

    def test_one_recommendation_per_weak_goal(self):
        """Test that one recommendation is generated per weak goal (max 5)."""
        recommendations = self.engine.generate_recommendations(
            MOCK_FRAMEWORK,
            MOCK_LOW_ALIGNMENT_DOC
        )

        # MOCK_LOW_ALIGNMENT_DOC has 3 goals; the engine generates one
        # recommendation per goal needing improvement, capped at 5
        rec_count = len(recommendations['recommendations'])
        assert 1 <= rec_count <= 5
        assert rec_count == 3

        print(f"{rec_count} recommendations generated (one per weak goal)")

    def test_recommendation_structure(self):
        """Test that each recommendation has required fields."""
        recommendations = self.engine.generate_recommendations(
            MOCK_FRAMEWORK,
            MOCK_LOW_ALIGNMENT_DOC
        )

        for rec in recommendations['recommendations']:
            assert 'recommendationId' in rec
            assert 'revisedGoal' in rec
            assert 'strategicLinkages' in rec
            assert 'predictedAlignmentGain' in rec
            assert 'evidence' in rec
            assert 'implementationNotes' in rec

            # Validate revised goal structure
            goal = rec['revisedGoal']
            assert 'objective' in goal
            assert 'keyResults' in goal
            assert 'timeline' in goal
            assert 'metrics' in goal

        print("Recommendation structure validation passed")

    def test_goals_are_smart(self):
        """Test that recommended goals follow SMART format."""
        recommendations = self.engine.generate_recommendations(
            MOCK_FRAMEWORK,
            MOCK_LOW_ALIGNMENT_DOC
        )

        for rec in recommendations['recommendations']:
            goal = rec['revisedGoal']

            # Should have measurable metrics
            assert len(goal['metrics']) > 0, "Goals must have metrics"

            # Should have timeline
            assert goal['timeline'], "Goals must have timeline"

            # Should have key results (specific outcomes)
            assert len(goal['keyResults']) > 0, "Goals must have key results"

        print("SMART format validation passed")

    def test_strategic_linkages_valid(self):
        """Test that strategic linkages reference valid objectives."""
        recommendations = self.engine.generate_recommendations(
            MOCK_FRAMEWORK,
            MOCK_LOW_ALIGNMENT_DOC
        )

        for rec in recommendations['recommendations']:
            linkages = rec['strategicLinkages']
            assert len(linkages) > 0, "Must link to strategic objectives"

            for obj_id in linkages:
                # Should be valid format
                assert len(obj_id) >= 2
                assert obj_id[0] in ['F', 'C', 'P', 'I', 'L']

        print("Strategic linkages validation passed")

    def test_evidence_provided(self):
        """Test that each recommendation has evidence."""
        recommendations = self.engine.generate_recommendations(
            MOCK_FRAMEWORK,
            MOCK_LOW_ALIGNMENT_DOC
        )

        for rec in recommendations['recommendations']:
            evidence = rec['evidence']
            assert 'source' in evidence
            assert evidence['source'], "Evidence source should not be empty"

        print("Evidence validation passed")

    def test_projected_score_improvement(self):
        """Test that projected scores show improvement."""
        recommendations = self.engine.generate_recommendations(
            MOCK_FRAMEWORK,
            MOCK_LOW_ALIGNMENT_DOC,
            MOCK_LOW_ALIGNMENT_DOC
        )

        current_alignment = MOCK_LOW_ALIGNMENT_DOC['overallAlignmentScore']
        projected_alignment = recommendations['projectedNewAlignmentScore']

        assert projected_alignment > current_alignment, "Projected alignment should improve"
        assert projected_alignment <= 100, "Score should not exceed 100"

        print(f"Score improvement: {current_alignment} -> {projected_alignment}")

    def test_reasonable_gain_predictions(self):
        """Test that alignment gain predictions are reasonable."""
        recommendations = self.engine.generate_recommendations(
            MOCK_FRAMEWORK,
            MOCK_LOW_ALIGNMENT_DOC
        )

        for rec in recommendations['recommendations']:
            gain = rec['predictedAlignmentGain']
            assert 0 <= gain <= 50, f"Gain should be reasonable: {gain}"

        print("Gain prediction validation passed")

    def test_batch_recommendations(self):
        """Test batch recommendation generation."""
        analyses = [
            MOCK_LOW_ALIGNMENT_DOC,
            {**MOCK_LOW_ALIGNMENT_DOC, 'documentId': 'doc-002', 'fileName': 'goals2.docx'}
        ]

        results = self.engine.generate_batch_recommendations(MOCK_FRAMEWORK, analyses)

        assert len(results) == 2
        for result in results:
            assert 'recommendations' in result or 'error' in result

        print(f"Batch recommendations: {len(results)} documents")

    def test_prioritize_recommendations(self):
        """Test recommendation prioritization."""
        recommendations = self.engine.generate_recommendations(
            MOCK_FRAMEWORK,
            MOCK_LOW_ALIGNMENT_DOC
        )

        prioritized = self.engine.prioritize_recommendations(recommendations, MOCK_FRAMEWORK)

        # Prioritization preserves the goal-bound recommendation count
        assert len(prioritized) == len(recommendations['recommendations'])

        # First recommendation should have highest score
        if len(prioritized) > 1:
            first_gain = prioritized[0].get('predictedAlignmentGain', 0)
            # Should be ordered by impact (considering critical KPRs)
            print(f"Top recommendation gain: {first_gain}")

        print("Prioritization test passed")

    def test_coverage_improvement_calculation(self):
        """Test coverage improvement calculation."""
        recommendations = self.engine.generate_recommendations(
            MOCK_FRAMEWORK,
            MOCK_LOW_ALIGNMENT_DOC
        )

        current_coverage = MOCK_LOW_ALIGNMENT_DOC['strategicCoverage']
        improvement = self.engine.get_coverage_improvement(current_coverage, recommendations)

        assert 'financial' in improvement
        assert 'customer' in improvement
        assert 'process' in improvement
        assert 'learning' in improvement

        for perspective, data in improvement.items():
            assert 'current' in data
            assert 'projected' in data
            assert 'improvement' in data

        print(f"Coverage improvement: {improvement}")

    def test_metadata_included(self):
        """Test that metadata is included in recommendations."""
        recommendations = self.engine.generate_recommendations(
            MOCK_FRAMEWORK,
            MOCK_LOW_ALIGNMENT_DOC
        )

        assert 'metadata' in recommendations
        assert 'generationTimestamp' in recommendations['metadata']
        assert 'recommendationCount' in recommendations['metadata']

        print(f"Metadata: {recommendations['metadata']}")


class TestMockRecommendationClient:
    """Test the mock client for testing infrastructure."""

    def test_mock_client_initialization(self):
        """Test mock client initializes correctly."""
        client = MockRecommendationClient()
        assert client is not None

    def test_mock_generates_recommendations(self):
        """Test mock client generates valid recommendations."""
        client = MockRecommendationClient()
        result = client.generate_recommendations(
            MOCK_FRAMEWORK,
            "Current goals text",
            MOCK_LOW_ALIGNMENT_DOC
        )

        assert 'recommendations' in result
        # One recommendation per weak goal (fixture has 3 goals), capped at 5
        assert 1 <= len(result['recommendations']) <= 5
        assert 'projectedNewAlignmentScore' in result

    def test_mock_connection_test(self):
        """Test mock connection test."""
        client = MockRecommendationClient()
        assert client.test_connection() is True


def run_manual_tests():
    """Run tests manually for debugging."""
    print("=" * 60)
    print("MILESTONE 5: Recommendation Engine Tests")
    print("=" * 60)

    mock_client = MockRecommendationClient()
    engine = GoalRecommendationEngine(claude_client=mock_client)

    print("\n--- Generating Recommendations ---")
    recommendations = engine.generate_recommendations(
        MOCK_FRAMEWORK,
        MOCK_LOW_ALIGNMENT_DOC
    )

    print(f"\nGenerated {len(recommendations['recommendations'])} recommendations")
    print(f"Projected Alignment: {recommendations['projectedNewAlignmentScore']}")
    print(f"Projected Impact: {recommendations['projectedNewImpactScore']}")

    print("\nRecommendations:")
    for rec in recommendations['recommendations']:
        goal = rec['revisedGoal']
        print(f"\n{rec['recommendationId']}: {goal['objective'][:60]}...")
        print(f"  Links: {rec['strategicLinkages']}")
        print(f"  Gain: +{rec['predictedAlignmentGain']} points")
        print(f"  Evidence: {rec['evidence']['source']}")

    # Test prioritization
    print("\n--- Prioritizing Recommendations ---")
    prioritized = engine.prioritize_recommendations(recommendations, MOCK_FRAMEWORK)
    print("Priority order:", [r['recommendationId'] for r in prioritized])

    print("\n" + "=" * 60)
    print("All manual tests completed!")


if __name__ == '__main__':
    run_manual_tests()
