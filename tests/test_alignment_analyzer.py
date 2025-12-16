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


class TestTranslationQualityAssessment:
    """Test the translation quality assessment for strategy translation."""

    def test_strategic_contribution_test_poor(self):
        """Test that copy-paste goals are detected for senior management."""
        client = MockAlignmentClient()
        client.vision = "To be the industry leader"
        client.mission = "Delivering value"
        client.theme_names = ["Operational Excellence", "Customer Focus"]

        # Poor translation - generic BSC language without functional context
        poor_goal = "Achieve company-wide revenue growth and ensure overall organizational success"

        result = client._strategic_contribution_test(poor_goal, "VP Sales", "Sales")

        assert result['testName'] == 'Strategic Contribution Test'
        assert result['translationQuality'] == 'poor' or result['score'] < 50
        assert result['genericPatternsFound'] >= 1
        print(f"Copy-paste detection: {result['assessment'][:100]}...")

    def test_strategic_contribution_test_excellent(self):
        """Test that functionally contextualized goals pass for senior management."""
        client = MockAlignmentClient()
        client.vision = "To be the industry leader"
        client.mission = "Delivering value"
        client.theme_names = ["Operational Excellence", "Customer Focus"]

        # Good translation - specific functional language
        good_goal = "Increase pipeline conversion rate from 15% to 25% through improved deal qualification"

        result = client._strategic_contribution_test(good_goal, "VP Sales", "Sales")

        assert result['testName'] == 'Strategic Contribution Test'
        assert result['translationQuality'] in ['excellent', 'moderate'] or result['score'] >= 60
        print(f"Functional context detection: {result['assessment'][:100]}...")

    def test_operational_driver_test_poor(self):
        """Test that pass-through goals are detected for team leaders."""
        client = MockAlignmentClient()

        # Poor translation - just passing down pressure
        poor_goal = "Hit 20% growth target and achieve sales quota for the team"

        result = client._operational_driver_test(poor_goal, "Sales Manager", "Sales")

        assert result['testName'] == 'Operational Driver Test'
        assert result['passThruPatternsFound'] >= 1
        print(f"Pass-through detection: {result['assessment'][:100]}...")

    def test_operational_driver_test_excellent(self):
        """Test that coachable goals pass for team leaders."""
        client = MockAlignmentClient()

        # Good translation - specific activities that can be coached
        good_goal = "Secure 3 Premium Tier demos per rep per week with 40% conversion rate"

        result = client._operational_driver_test(good_goal, "Sales Manager", "Sales")

        assert result['testName'] == 'Operational Driver Test'
        assert result['litmusTestPassed'] == True
        assert result['translationQuality'] in ['excellent', 'good', 'moderate']
        print(f"Coachable goal detection: {result['assessment'][:100]}...")

    def test_shared_goal_trap_detected(self):
        """Test that shared goals are flagged for handshake breakdown."""
        client = MockAlignmentClient()

        # Shared goal trap - too generic, applies to multiple departments
        shared_goal = "Launch new product successfully and ensure project success"

        result = client._shared_goal_trap_test(shared_goal, "Product")

        assert result['testName'] == 'Shared Goal Trap Test'
        assert result['isSharedGoalTrap'] == True
        assert result['sharedPatternsFound'] >= 1
        print(f"Shared goal trap: {result['assessment'][:100]}...")

    def test_shared_goal_with_handshake(self):
        """Test that shared goals with handshakes are accepted."""
        client = MockAlignmentClient()

        # Good handshake - specific deliverable for function
        handshake_goal = "Deliver Gold Master code for new product by Q3 with all acceptance criteria met"

        result = client._shared_goal_trap_test(handshake_goal, "Product")

        assert result['testName'] == 'Shared Goal Trap Test'
        assert result['isSharedGoalTrap'] == False
        print(f"Handshake accepted: {result['assessment'][:100]}...")

    def test_translation_quality_in_analysis(self):
        """Test that translation quality is included in full analysis."""
        client = MockAlignmentClient()
        result = client.analyze_goal_alignment(
            MOCK_FRAMEWORK,
            "• Reduce customer churn by 15% through improved onboarding process",
            employee_context={
                'employeeName': 'Test User',
                'jobTitle': 'VP Customer Success',
                'seniorityLevel': 'senior management',
                'department': 'Customer Success'
            }
        )

        # Check that translation quality is in coherence index
        assert 'coherenceIndex' in result
        assert 'translationQualityAnalysis' in result['coherenceIndex']

        translation_analysis = result['coherenceIndex']['translationQualityAnalysis']
        assert 'averageScore' in translation_analysis
        assert 'verdict' in translation_analysis

        print(f"Translation quality in analysis: {translation_analysis['verdict']}")

    def test_translation_quality_per_goal(self):
        """Test that each goal has translation quality assessment."""
        client = MockAlignmentClient()
        result = client.analyze_goal_alignment(
            MOCK_FRAMEWORK,
            "• Increase pipeline conversion through better qualification",
            employee_context={
                'employeeName': 'Test User',
                'jobTitle': 'Sales Manager',
                'seniorityLevel': 'team leader',
                'department': 'Sales'
            }
        )

        assert len(result['goals']) >= 1
        for goal in result['goals']:
            assert 'translationQualityAssessment' in goal
            tqa = goal['translationQualityAssessment']
            assert 'seniorityTestResult' in tqa
            assert 'sharedGoalTrapCheck' in tqa
            assert 'overallTranslationQuality' in tqa

        print(f"Per-goal translation quality included for {len(result['goals'])} goals")

    def test_alignment_score_quadrant_synchronization(self):
        """Test that alignment score and quadrant classification are synchronized."""
        client = MockAlignmentClient()

        # High alignment goal should be classified as aligned
        result = client.analyze_goal_alignment(
            MOCK_FRAMEWORK,
            "• Reduce customer churn by 15% through improved onboarding experience",
            employee_context={
                'employeeName': 'Test User',
                'jobTitle': 'VP Customer Success',
                'seniorityLevel': 'senior management',
                'department': 'Customer Success'
            }
        )

        assert len(result['goals']) >= 1
        for goal in result['goals']:
            alignment_score = goal.get('alignmentScore', 0)
            quadrant = goal.get('quadrantClassification', {})

            # If alignment score is high, quadrant should reflect alignment
            if alignment_score >= 65:
                assert quadrant.get('alignmentCheck', {}).get('isAligned') == True, \
                    f"High alignment score ({alignment_score}) should result in aligned quadrant"

            # If alignment score is low, should not be Strategic Driver
            if alignment_score < 35:
                assert quadrant.get('quadrant') != 'Strategic Driver', \
                    f"Low alignment score ({alignment_score}) should not be Strategic Driver"

        print(f"Alignment-quadrant synchronization verified")

    def test_original_rationale_preserved(self):
        """Test that original alignment rationale is not overwritten."""
        client = MockAlignmentClient()
        result = client.analyze_goal_alignment(
            MOCK_FRAMEWORK,
            "• Increase pipeline conversion through better qualification",
            employee_context={
                'employeeName': 'Test User',
                'jobTitle': 'Sales Manager',
                'seniorityLevel': 'team leader',
                'department': 'Sales'
            }
        )

        for goal in result['goals']:
            # Original rationale should exist
            assert 'alignmentRationale' in goal
            assert len(goal['alignmentRationale']) > 0

            # Quadrant rationale should be separate
            assert 'quadrantRationale' in goal
            assert len(goal['quadrantRationale']) > 0

            # They should be different (quadrant uses different format)
            # Original rationale should not start with quadrant keywords
            original = goal['alignmentRationale']
            quadrant_r = goal['quadrantRationale']
            assert original != quadrant_r or (original == quadrant_r and 'ALIGNMENT' in original)

        print("Original rationale preserved, quadrant rationale added separately")

    def test_translation_penalty_applied(self):
        """Test that poor translation quality applies penalty to quadrant points."""
        client = MockAlignmentClient()

        # A goal with poor translation should have penalty applied
        poor_goal = "Achieve company-wide organizational transformation and ensure overall success"

        # Simulate the goal going through the full analysis
        result = client.analyze_goal_alignment(
            MOCK_FRAMEWORK,
            f"• {poor_goal}",
            employee_context={
                'employeeName': 'Test User',
                'jobTitle': 'VP Operations',
                'seniorityLevel': 'senior management',
                'department': 'Operations'
            }
        )

        for goal in result['goals']:
            quadrant = goal.get('quadrantClassification', {})
            # If translation penalty was applied, it should be tracked
            if 'translationPenalty' in quadrant:
                base_points = quadrant.get('basePoints', 0)
                actual_points = quadrant.get('points', 0)
                penalty = quadrant.get('translationPenalty', 0)

                if penalty > 0:
                    assert actual_points <= base_points, "Penalty should reduce points"
                    print(f"Translation penalty applied: -{penalty} points")

        print("Translation penalty integration verified")


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
