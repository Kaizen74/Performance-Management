"""
Strategy Synthesizer
Transforms strategy documents into structured strategic framework (Balanced Scorecard / Strategy Map).
"""

import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime

from .claude_client import ClaudeClient


@dataclass
class StrategicObjective:
    """Represents a strategic objective within a BSC perspective."""
    id: str
    objective: str
    keyMeasures: List[str]
    strategicThemes: List[str]


@dataclass
class StrategicPerspective:
    """Represents a Balanced Scorecard perspective."""
    objectives: List[StrategicObjective]


@dataclass
class StrategicTheme:
    """Represents a strategic theme connecting objectives."""
    themeId: str
    name: str
    description: str
    linkedObjectives: List[str]


@dataclass
class KeyPerformanceRequirement:
    """Represents a key performance requirement."""
    id: str
    requirement: str
    perspective: str
    priority: str
    linkedObjectiveIds: List[str]


@dataclass
class OrganizationalPurpose:
    """Represents organization's vision, mission, and values."""
    vision: str
    mission: str
    values: List[str]


@dataclass
class StrategicFramework:
    """Complete strategic framework output."""
    frameworkId: str
    organizationalPurpose: OrganizationalPurpose
    strategicPerspectives: Dict[str, StrategicPerspective]
    strategicThemes: List[StrategicTheme]
    keyPerformanceRequirements: List[KeyPerformanceRequirement]
    metadata: Dict[str, Any] = field(default_factory=dict)


class StrategySynthesizer:
    """
    Synthesizes strategy documents into a structured strategic framework.
    Uses Claude API for deep semantic analysis.
    """

    MAX_DOCUMENTS = 5
    PERSPECTIVES = ['financial', 'customer', 'internalProcess', 'learningGrowth']

    def __init__(self, claude_client: Optional[ClaudeClient] = None, api_key: Optional[str] = None):
        """
        Initialize the strategy synthesizer.

        Args:
            claude_client: Pre-configured Claude client (for testing)
            api_key: API key for Claude (creates new client if claude_client not provided)
        """
        if claude_client:
            self.client = claude_client
        elif api_key:
            self.client = ClaudeClient(api_key=api_key)
        else:
            # Will use environment variable
            self.client = ClaudeClient()

    def analyze(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze strategy documents and generate strategic framework.

        Args:
            documents: List of processed documents from DocumentProcessor
                      Each should have 'extractedText' and 'structuredSections'

        Returns:
            Strategic framework as dictionary
        """
        if not documents:
            raise ValueError("At least one strategy document is required")

        if len(documents) > self.MAX_DOCUMENTS:
            raise ValueError(f"Maximum {self.MAX_DOCUMENTS} documents allowed")

        # Combine document texts
        combined_text = self._combine_documents(documents)

        # Use Claude to analyze and extract framework
        raw_framework = self.client.analyze_strategy(combined_text)

        # Validate and enhance the framework
        framework = self._validate_framework(raw_framework)

        # Add metadata
        framework['metadata'] = {
            'frameworkId': str(uuid.uuid4()),
            'sourceDocuments': len(documents),
            'analysisTimestamp': datetime.utcnow().isoformat() + 'Z',
            'totalSourceWords': len(combined_text.split())
        }

        return framework

    def _combine_documents(self, documents: List[Dict[str, Any]]) -> str:
        """
        Combine multiple documents into a single text for analysis.

        Args:
            documents: List of processed documents

        Returns:
            Combined text with document separators
        """
        parts = []
        for i, doc in enumerate(documents, 1):
            filename = doc.get('fileName', f'Document {i}')
            text = doc.get('extractedText', '')

            # Also include structured sections if available
            sections = doc.get('structuredSections', [])
            section_text = ""
            for section in sections:
                heading = section.get('heading', '')
                content = section.get('content', '')
                if heading and content:
                    section_text += f"\n## {heading}\n{content}\n"

            doc_text = f"=== DOCUMENT: {filename} ===\n"
            if section_text:
                doc_text += section_text
            else:
                doc_text += text
            doc_text += "\n"

            parts.append(doc_text)

        return "\n".join(parts)

    def _validate_framework(self, framework: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and ensure framework has required structure.

        Args:
            framework: Raw framework from Claude

        Returns:
            Validated framework with any missing fields filled
        """
        # Ensure organizational purpose
        if 'organizationalPurpose' not in framework:
            framework['organizationalPurpose'] = {
                'vision': 'Not specified',
                'mission': 'Not specified',
                'values': []
            }

        purpose = framework['organizationalPurpose']
        purpose['vision'] = purpose.get('vision', 'Not specified')
        purpose['mission'] = purpose.get('mission', 'Not specified')
        purpose['values'] = purpose.get('values', [])

        # Ensure strategic perspectives
        if 'strategicPerspectives' not in framework:
            framework['strategicPerspectives'] = {}

        perspectives = framework['strategicPerspectives']
        for p in self.PERSPECTIVES:
            if p not in perspectives:
                perspectives[p] = {'objectives': []}
            elif 'objectives' not in perspectives[p]:
                perspectives[p]['objectives'] = []

            # Ensure each objective has required fields
            for i, obj in enumerate(perspectives[p]['objectives']):
                if 'id' not in obj:
                    prefix = p[0].upper()  # F, C, I, L
                    obj['id'] = f"{prefix}{i+1}"
                obj['objective'] = obj.get('objective', '')
                obj['keyMeasures'] = obj.get('keyMeasures', [])
                obj['strategicThemes'] = obj.get('strategicThemes', [])

        # Ensure strategic themes
        if 'strategicThemes' not in framework:
            framework['strategicThemes'] = []

        for i, theme in enumerate(framework['strategicThemes']):
            if 'themeId' not in theme:
                theme['themeId'] = f"T{i+1}"
            theme['name'] = theme.get('name', f'Theme {i+1}')
            theme['description'] = theme.get('description', '')
            theme['linkedObjectives'] = theme.get('linkedObjectives', [])

        # Ensure key performance requirements
        if 'keyPerformanceRequirements' not in framework:
            framework['keyPerformanceRequirements'] = []

        for i, kpr in enumerate(framework['keyPerformanceRequirements']):
            if 'id' not in kpr:
                kpr['id'] = f"KPR{i+1}"
            kpr['requirement'] = kpr.get('requirement', '')
            kpr['perspective'] = kpr.get('perspective', 'process')
            kpr['priority'] = kpr.get('priority', 'medium')
            kpr['linkedObjectiveIds'] = kpr.get('linkedObjectiveIds', [])

        return framework

    def get_objective_count(self, framework: Dict[str, Any]) -> Dict[str, int]:
        """
        Get count of objectives per perspective.

        Args:
            framework: Strategic framework

        Returns:
            Dictionary with perspective names and objective counts
        """
        counts = {}
        perspectives = framework.get('strategicPerspectives', {})
        for p in self.PERSPECTIVES:
            objectives = perspectives.get(p, {}).get('objectives', [])
            counts[p] = len(objectives)
        counts['total'] = sum(counts.values())
        return counts

    def get_all_objective_ids(self, framework: Dict[str, Any]) -> List[str]:
        """
        Get all objective IDs from the framework.

        Args:
            framework: Strategic framework

        Returns:
            List of all objective IDs
        """
        ids = []
        perspectives = framework.get('strategicPerspectives', {})
        for p in self.PERSPECTIVES:
            objectives = perspectives.get(p, {}).get('objectives', [])
            for obj in objectives:
                if 'id' in obj:
                    ids.append(obj['id'])
        return ids

    def validate_cross_perspective_linkages(self, framework: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that strategic themes link across multiple perspectives.

        Args:
            framework: Strategic framework

        Returns:
            Validation result with linkage analysis
        """
        all_ids = self.get_all_objective_ids(framework)
        themes = framework.get('strategicThemes', [])

        results = {
            'valid': True,
            'themes': [],
            'warnings': []
        }

        # Map objective IDs to perspectives
        id_to_perspective = {}
        perspectives = framework.get('strategicPerspectives', {})
        for p in self.PERSPECTIVES:
            objectives = perspectives.get(p, {}).get('objectives', [])
            for obj in objectives:
                if 'id' in obj:
                    id_to_perspective[obj['id']] = p

        for theme in themes:
            linked = theme.get('linkedObjectives', [])
            linked_perspectives = set()

            for obj_id in linked:
                if obj_id in id_to_perspective:
                    linked_perspectives.add(id_to_perspective[obj_id])

            theme_result = {
                'themeId': theme.get('themeId'),
                'name': theme.get('name'),
                'linkedPerspectives': list(linked_perspectives),
                'crossPerspective': len(linked_perspectives) > 1
            }
            results['themes'].append(theme_result)

            if len(linked_perspectives) < 2:
                results['warnings'].append(
                    f"Theme '{theme.get('name')}' only links objectives in {len(linked_perspectives)} perspective(s)"
                )

        # Check if any theme has cross-perspective linkages
        has_cross_linkage = any(t['crossPerspective'] for t in results['themes'])
        if not has_cross_linkage and themes:
            results['warnings'].append(
                "No strategic themes link objectives across multiple perspectives"
            )

        results['valid'] = len(results['warnings']) == 0

        return results


class MockClaudeClient:
    """
    Mock Claude client for testing without API calls.
    Returns predefined responses for testing.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize mock client."""
        self.api_key = api_key or "mock-key"

    def analyze_strategy(self, documents_text: str) -> Dict[str, Any]:
        """Return mock strategic framework."""
        return {
            "organizationalPurpose": {
                "vision": "To be the leading sustainable logistics provider in Asia-Pacific by 2030",
                "mission": "We deliver excellence through innovation, connecting businesses to opportunities while minimizing environmental impact",
                "values": ["Innovation", "Integrity", "Sustainability", "Excellence", "Collaboration"]
            },
            "strategicPerspectives": {
                "financial": {
                    "objectives": [
                        {
                            "id": "F1",
                            "objective": "Achieve 12% revenue CAGR through market expansion",
                            "keyMeasures": ["Revenue growth rate", "Market share"],
                            "strategicThemes": ["Growth", "Market Leadership"]
                        },
                        {
                            "id": "F2",
                            "objective": "Maintain EBITDA margin above 18%",
                            "keyMeasures": ["EBITDA margin", "Cost efficiency ratio"],
                            "strategicThemes": ["Operational Excellence"]
                        }
                    ]
                },
                "customer": {
                    "objectives": [
                        {
                            "id": "C1",
                            "objective": "Achieve NPS score above 70",
                            "keyMeasures": ["Net Promoter Score", "Customer satisfaction"],
                            "strategicThemes": ["Customer Excellence"]
                        },
                        {
                            "id": "C2",
                            "objective": "Deliver 95% on-time delivery rate",
                            "keyMeasures": ["On-time delivery %", "Order accuracy"],
                            "strategicThemes": ["Operational Excellence", "Customer Excellence"]
                        }
                    ]
                },
                "internalProcess": {
                    "objectives": [
                        {
                            "id": "P1",
                            "objective": "Implement AI-driven route optimization",
                            "keyMeasures": ["Route efficiency", "Fuel consumption"],
                            "strategicThemes": ["Digital Transformation"]
                        },
                        {
                            "id": "P2",
                            "objective": "Achieve carbon neutrality by 2028",
                            "keyMeasures": ["Carbon emissions", "Fleet electrification %"],
                            "strategicThemes": ["Sustainability"]
                        },
                        {
                            "id": "P3",
                            "objective": "Reduce operational costs by 15%",
                            "keyMeasures": ["Cost per unit", "Process efficiency"],
                            "strategicThemes": ["Operational Excellence"]
                        }
                    ]
                },
                "learningGrowth": {
                    "objectives": [
                        {
                            "id": "L1",
                            "objective": "Build digital capabilities across workforce",
                            "keyMeasures": ["Digital skills index", "Training completion"],
                            "strategicThemes": ["Digital Transformation", "Talent Development"]
                        },
                        {
                            "id": "L2",
                            "objective": "Achieve employee engagement above 80%",
                            "keyMeasures": ["Engagement score", "Retention rate"],
                            "strategicThemes": ["Talent Development"]
                        }
                    ]
                }
            },
            "strategicThemes": [
                {
                    "themeId": "T1",
                    "name": "Digital Transformation",
                    "description": "Leverage technology to transform operations and customer experience",
                    "linkedObjectives": ["P1", "L1", "C2"]
                },
                {
                    "themeId": "T2",
                    "name": "Sustainability",
                    "description": "Lead the industry in environmental responsibility",
                    "linkedObjectives": ["P2", "F1"]
                },
                {
                    "themeId": "T3",
                    "name": "Operational Excellence",
                    "description": "Continuous improvement in efficiency and quality",
                    "linkedObjectives": ["F2", "C2", "P3"]
                },
                {
                    "themeId": "T4",
                    "name": "Customer Excellence",
                    "description": "Deliver exceptional customer experience",
                    "linkedObjectives": ["C1", "C2"]
                },
                {
                    "themeId": "T5",
                    "name": "Talent Development",
                    "description": "Build future-ready workforce",
                    "linkedObjectives": ["L1", "L2"]
                }
            ],
            "keyPerformanceRequirements": [
                {
                    "id": "KPR1",
                    "requirement": "Leadership must drive digital transformation initiatives",
                    "perspective": "process",
                    "priority": "critical",
                    "linkedObjectiveIds": ["P1", "L1"]
                },
                {
                    "id": "KPR2",
                    "requirement": "Sustainability targets must be embedded in all operations",
                    "perspective": "process",
                    "priority": "critical",
                    "linkedObjectiveIds": ["P2"]
                },
                {
                    "id": "KPR3",
                    "requirement": "Customer-centricity must be core to all decisions",
                    "perspective": "customer",
                    "priority": "high",
                    "linkedObjectiveIds": ["C1", "C2"]
                },
                {
                    "id": "KPR4",
                    "requirement": "Cost discipline while investing in growth",
                    "perspective": "financial",
                    "priority": "high",
                    "linkedObjectiveIds": ["F1", "F2", "P3"]
                }
            ]
        }

    def test_connection(self) -> bool:
        """Mock connection test."""
        return True
