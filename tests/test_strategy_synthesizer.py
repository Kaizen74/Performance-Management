"""
Test Suite for Strategy Synthesizer (Milestone 2)
Tests strategy document analysis and BSC framework generation.
"""

import os
import sys
import pytest
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from analyzers.strategy_synthesizer import StrategySynthesizer, MockClaudeClient


# Mock strategy document content
MOCK_STRATEGY_CONTENT = """
VISION: To be the leading sustainable logistics provider in Asia-Pacific by 2030.

MISSION: We deliver excellence through innovation, connecting businesses to opportunities while minimizing environmental impact.

STRATEGIC PRIORITIES:
1. Digital Transformation - Implement AI-driven route optimization
2. Sustainability Leadership - Achieve carbon neutrality by 2028
3. Customer Excellence - NPS > 70 across all segments
4. Operational Efficiency - 15% reduction in unit costs
5. Talent Development - Build future-ready workforce with digital skills

CORE VALUES:
- Innovation: We embrace change and continuously seek better solutions
- Integrity: We act with honesty and transparency
- Sustainability: We protect our planet
- Excellence: We strive for the highest quality
- Collaboration: We achieve more together
"""


class TestStrategySynthesizer:
    """Test cases for the StrategySynthesizer class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        # Use mock client for testing
        self.mock_client = MockClaudeClient()
        self.synthesizer = StrategySynthesizer(claude_client=self.mock_client)

    def test_synthesizer_initialization(self):
        """Test that StrategySynthesizer initializes correctly."""
        synthesizer = StrategySynthesizer(claude_client=self.mock_client)
        assert synthesizer is not None
        assert synthesizer.client is not None

    def test_analyze_single_document(self):
        """Test analysis of a single strategy document."""
        documents = [{
            'fileName': 'strategy.pdf',
            'extractedText': MOCK_STRATEGY_CONTENT,
            'structuredSections': []
        }]

        result = self.synthesizer.analyze(documents)

        # Validate basic structure
        assert 'organizationalPurpose' in result
        assert 'strategicPerspectives' in result
        assert 'strategicThemes' in result
        assert 'keyPerformanceRequirements' in result
        assert 'metadata' in result

        print("Single document analysis passed")

    def test_organizational_purpose_extraction(self):
        """Test that vision, mission, values are correctly extracted."""
        documents = [{
            'extractedText': MOCK_STRATEGY_CONTENT,
            'structuredSections': []
        }]

        result = self.synthesizer.analyze(documents)
        purpose = result['organizationalPurpose']

        # Check vision contains key terms
        assert 'vision' in purpose
        assert purpose['vision'], "Vision should not be empty"
        assert 'sustainable' in purpose['vision'].lower() or 'logistics' in purpose['vision'].lower()

        # Check mission exists
        assert 'mission' in purpose
        assert purpose['mission'], "Mission should not be empty"

        # Check values
        assert 'values' in purpose
        assert isinstance(purpose['values'], list)
        assert len(purpose['values']) > 0

        print(f"Purpose extraction passed: {len(purpose['values'])} values")

    def test_bsc_perspectives_populated(self):
        """Test that all BSC perspectives have objectives."""
        documents = [{
            'extractedText': MOCK_STRATEGY_CONTENT,
            'structuredSections': []
        }]

        result = self.synthesizer.analyze(documents)
        perspectives = result['strategicPerspectives']

        required_perspectives = ['financial', 'customer', 'internalProcess', 'learningGrowth']

        for perspective in required_perspectives:
            assert perspective in perspectives, f"Missing perspective: {perspective}"
            assert 'objectives' in perspectives[perspective]
            objectives = perspectives[perspective]['objectives']
            assert len(objectives) > 0, f"No objectives in {perspective} perspective"

        # Count total objectives
        total_objectives = sum(
            len(perspectives[p]['objectives'])
            for p in required_perspectives
        )
        assert total_objectives >= 8, f"Expected at least 8 objectives, got {total_objectives}"

        print(f"BSC perspectives populated: {total_objectives} total objectives")

    def test_objective_structure(self):
        """Test that objectives have required fields."""
        documents = [{
            'extractedText': MOCK_STRATEGY_CONTENT,
            'structuredSections': []
        }]

        result = self.synthesizer.analyze(documents)
        perspectives = result['strategicPerspectives']

        for p_name, perspective in perspectives.items():
            for obj in perspective['objectives']:
                assert 'id' in obj, f"Objective missing id in {p_name}"
                assert 'objective' in obj, f"Objective missing objective text in {p_name}"
                assert 'keyMeasures' in obj, f"Objective missing keyMeasures in {p_name}"
                assert 'strategicThemes' in obj, f"Objective missing strategicThemes in {p_name}"

                # Validate ID format (F1, C1, P1, L1, etc.)
                assert len(obj['id']) >= 2, f"Invalid objective ID: {obj['id']}"

        print("Objective structure validation passed")

    def test_strategic_themes_created(self):
        """Test that strategic themes are created with cross-perspective linkages."""
        documents = [{
            'extractedText': MOCK_STRATEGY_CONTENT,
            'structuredSections': []
        }]

        result = self.synthesizer.analyze(documents)
        themes = result['strategicThemes']

        assert len(themes) >= 3, f"Expected at least 3 strategic themes, got {len(themes)}"

        for theme in themes:
            assert 'themeId' in theme
            assert 'name' in theme
            assert 'description' in theme
            assert 'linkedObjectives' in theme

        # Check cross-perspective linkages
        linked_objectives = []
        for theme in themes:
            linked_objectives.extend(theme['linkedObjectives'])

        unique_linked = set(linked_objectives)
        assert len(unique_linked) >= 3, "Strategic themes should link multiple objectives"

        print(f"Strategic themes created: {len(themes)} themes linking {len(unique_linked)} objectives")

    def test_key_performance_requirements(self):
        """Test that KPRs are generated with proper structure."""
        documents = [{
            'extractedText': MOCK_STRATEGY_CONTENT,
            'structuredSections': []
        }]

        result = self.synthesizer.analyze(documents)
        kprs = result['keyPerformanceRequirements']

        assert len(kprs) >= 4, f"Expected at least 4 KPRs, got {len(kprs)}"

        valid_perspectives = ['financial', 'customer', 'process', 'learning']
        valid_priorities = ['critical', 'high', 'medium']

        for kpr in kprs:
            assert 'id' in kpr
            assert 'requirement' in kpr
            assert 'perspective' in kpr
            assert 'priority' in kpr
            assert 'linkedObjectiveIds' in kpr

            assert kpr['perspective'] in valid_perspectives, f"Invalid perspective: {kpr['perspective']}"
            assert kpr['priority'] in valid_priorities, f"Invalid priority: {kpr['priority']}"

        print(f"KPRs generated: {len(kprs)} requirements")

    def test_metadata_included(self):
        """Test that analysis metadata is included."""
        documents = [{
            'fileName': 'test_strategy.pdf',
            'extractedText': MOCK_STRATEGY_CONTENT,
            'structuredSections': []
        }]

        result = self.synthesizer.analyze(documents)

        assert 'metadata' in result
        metadata = result['metadata']

        assert 'frameworkId' in metadata
        assert 'sourceDocuments' in metadata
        assert 'analysisTimestamp' in metadata

        # Validate timestamp format (ISO8601)
        assert 'T' in metadata['analysisTimestamp']

        print(f"Metadata included: {list(metadata.keys())}")

    def test_multiple_documents(self):
        """Test analysis of multiple strategy documents."""
        documents = [
            {
                'fileName': 'vision_doc.pdf',
                'extractedText': 'VISION: Leading sustainable logistics provider',
                'structuredSections': []
            },
            {
                'fileName': 'strategy_doc.pdf',
                'extractedText': MOCK_STRATEGY_CONTENT,
                'structuredSections': []
            }
        ]

        result = self.synthesizer.analyze(documents)

        assert result['metadata']['sourceDocuments'] == 2

        print("Multiple document analysis passed")

    def test_max_documents_limit(self):
        """Test that document limit is enforced."""
        documents = [{'extractedText': 'Test', 'structuredSections': []} for _ in range(6)]

        with pytest.raises(ValueError) as exc_info:
            self.synthesizer.analyze(documents)

        assert 'Maximum' in str(exc_info.value)

        print("Document limit enforcement passed")

    def test_empty_documents_rejected(self):
        """Test that empty document list is rejected."""
        with pytest.raises(ValueError):
            self.synthesizer.analyze([])

        print("Empty documents rejection passed")

    def test_cross_perspective_validation(self):
        """Test the cross-perspective linkage validation."""
        documents = [{
            'extractedText': MOCK_STRATEGY_CONTENT,
            'structuredSections': []
        }]

        result = self.synthesizer.analyze(documents)
        validation = self.synthesizer.validate_cross_perspective_linkages(result)

        assert 'valid' in validation
        assert 'themes' in validation
        assert 'warnings' in validation

        # Check that at least some themes link across perspectives
        cross_linked = [t for t in validation['themes'] if t['crossPerspective']]
        assert len(cross_linked) >= 1, "Expected at least one cross-perspective theme"

        print(f"Cross-perspective validation: {len(cross_linked)} themes with cross-linkage")

    def test_objective_count(self):
        """Test objective counting functionality."""
        documents = [{
            'extractedText': MOCK_STRATEGY_CONTENT,
            'structuredSections': []
        }]

        result = self.synthesizer.analyze(documents)
        counts = self.synthesizer.get_objective_count(result)

        assert 'financial' in counts
        assert 'customer' in counts
        assert 'internalProcess' in counts
        assert 'learningGrowth' in counts
        assert 'total' in counts

        assert counts['total'] >= 8

        print(f"Objective counts: {counts}")

    def test_get_all_objective_ids(self):
        """Test retrieval of all objective IDs."""
        documents = [{
            'extractedText': MOCK_STRATEGY_CONTENT,
            'structuredSections': []
        }]

        result = self.synthesizer.analyze(documents)
        ids = self.synthesizer.get_all_objective_ids(result)

        assert len(ids) >= 8
        # Check ID format
        for obj_id in ids:
            assert obj_id[0] in ['F', 'C', 'P', 'I', 'L'], f"Invalid ID prefix: {obj_id}"

        print(f"Retrieved {len(ids)} objective IDs")


class TestMockClaudeClient:
    """Test the mock client for testing infrastructure."""

    def test_mock_client_initialization(self):
        """Test mock client initializes correctly."""
        client = MockClaudeClient()
        assert client is not None
        assert client.api_key == "mock-key"

    def test_mock_analyze_strategy(self):
        """Test mock strategy analysis returns valid structure."""
        client = MockClaudeClient()
        result = client.analyze_strategy("test content")

        assert 'organizationalPurpose' in result
        assert 'strategicPerspectives' in result
        assert 'strategicThemes' in result
        assert 'keyPerformanceRequirements' in result

    def test_mock_connection_test(self):
        """Test mock connection test."""
        client = MockClaudeClient()
        assert client.test_connection() is True


def run_manual_tests():
    """Run tests manually for debugging."""
    print("=" * 60)
    print("MILESTONE 2: Strategy Synthesizer Tests")
    print("=" * 60)

    mock_client = MockClaudeClient()
    synthesizer = StrategySynthesizer(claude_client=mock_client)

    documents = [{
        'fileName': 'strategy.pdf',
        'extractedText': MOCK_STRATEGY_CONTENT,
        'structuredSections': []
    }]

    print("\n--- Testing Strategy Analysis ---")
    result = synthesizer.analyze(documents)

    print(f"\nVision: {result['organizationalPurpose']['vision'][:80]}...")
    print(f"Mission: {result['organizationalPurpose']['mission'][:80]}...")
    print(f"Values: {result['organizationalPurpose']['values']}")

    counts = synthesizer.get_objective_count(result)
    print(f"\nObjective Counts: {counts}")

    print(f"\nStrategic Themes: {len(result['strategicThemes'])}")
    for theme in result['strategicThemes']:
        print(f"  - {theme['name']}: links {theme['linkedObjectives']}")

    print(f"\nKey Performance Requirements: {len(result['keyPerformanceRequirements'])}")

    # Validate cross-perspective linkages
    validation = synthesizer.validate_cross_perspective_linkages(result)
    print(f"\nCross-perspective validation: {validation['valid']}")
    if validation['warnings']:
        print(f"Warnings: {validation['warnings']}")

    print("\n" + "=" * 60)
    print("All manual tests completed!")


if __name__ == '__main__':
    run_manual_tests()
