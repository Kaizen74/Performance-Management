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
                # Only include sections with meaningful headings (not fragmented keywords)
                # A good heading should have at least 2 words or be a recognized section name
                heading_words = heading.split()
                is_valid_heading = (
                    len(heading_words) >= 2 or
                    heading.lower() in ['vision', 'mission', 'values', 'strategy', 'objectives',
                                        'goals', 'overview', 'summary', 'introduction', 'conclusion']
                )
                if heading and content and is_valid_heading and len(content) > 20:
                    section_text += f"\n{heading}\n{content}\n"

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
    Actually parses uploaded documents to extract strategic content.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize mock client."""
        self.api_key = api_key or "mock-key"

    def analyze_strategy(self, documents_text: str) -> Dict[str, Any]:
        """
        Extract strategic framework from actual document content.
        Parses the documents to find vision, mission, values, and strategic elements.
        """
        # Detect if this is a team/department-specific strategy
        scope_info = self._detect_strategy_scope(documents_text)

        # Extract actual content from documents
        vision = self._extract_vision(documents_text)
        mission = self._extract_mission(documents_text)
        values = self._extract_values(documents_text)
        strategic_themes = self._extract_themes(documents_text)
        objectives = self._extract_objectives(documents_text, strategic_themes)
        kprs = self._extract_kprs(documents_text, objectives)

        # If team-specific and no explicit vision/mission found, generate from context
        if scope_info['is_team_specific']:
            entity_name = scope_info['entity_name']
            if 'not explicitly stated' in vision.lower() or len(vision) < 30:
                vision = self._generate_team_vision(documents_text, entity_name, objectives)
            if 'not explicitly stated' in mission.lower() or len(mission) < 30:
                mission = self._generate_team_mission(documents_text, entity_name, objectives)

        result = {
            "strategyScope": scope_info['scope'],
            "scopeEntity": scope_info['entity_name'],
            "organizationalPurpose": {
                "vision": vision,
                "mission": mission,
                "values": values
            },
            "strategicPerspectives": objectives,
            "strategicThemes": strategic_themes,
            "keyPerformanceRequirements": kprs
        }

        return result

    def _detect_strategy_scope(self, documents_text: str) -> Dict[str, Any]:
        """
        Detect if the strategy document is team/department-specific or organization-wide.
        """
        import re

        text_lower = documents_text.lower()

        # Common team/department indicators
        team_patterns = [
            r'([A-Za-z&\s]+(?:team|department|division|function|unit))\s+(?:strategy|strategic|goals|objectives)',
            r'(?:strategy|strategic|goals|objectives)\s+(?:for|of)\s+([A-Za-z&\s]+)',
            r'([A-Z]{2,6})\s+(?:strategic\s+)?goals',
            r'(OD\s*&?\s*Talent\s*Management|ODTM|Talent\s*Management|Organisation(?:al)?\s*Development)',
            r'(Human\s*Resources?|People\s*(?:&\s*)?(?:Culture|Operations))',
        ]

        for pattern in team_patterns:
            matches = re.findall(pattern, documents_text, re.IGNORECASE)
            if matches:
                entity_name = matches[0].strip() if isinstance(matches[0], str) else matches[0]
                entity_name = re.sub(r'\s+', ' ', entity_name).strip()
                if len(entity_name) > 2:
                    return {
                        'is_team_specific': True,
                        'entity_name': entity_name,
                        'scope': 'team' if 'team' in entity_name.lower() else 'department'
                    }

        # Check for functional keywords
        functional_keywords = [
            'talent management', 'talent development', 'talent acquisition',
            'organisational development', 'organizational development',
            'succession planning', 'employee engagement'
        ]
        keyword_matches = sum(1 for kw in functional_keywords if kw in text_lower)

        company_indicators = ['corporate strategy', 'company strategy', 'our vision', 'our mission']
        has_company_context = any(ind in text_lower for ind in company_indicators)

        if keyword_matches >= 2 and not has_company_context:
            if any(kw in text_lower for kw in ['talent', 'odtm', 'od ', 'organisational development']):
                return {
                    'is_team_specific': True,
                    'entity_name': 'OD & Talent Management',
                    'scope': 'department'
                }

        return {
            'is_team_specific': False,
            'entity_name': None,
            'scope': 'organization'
        }

    def _generate_team_vision(self, text: str, entity_name: str, objectives: Dict) -> str:
        """Generate a team vision statement based on their strategic goals."""
        # Extract key focus areas from objectives
        focus_areas = []
        for perspective in ['learningGrowth', 'internalProcess', 'customer', 'financial']:
            objs = objectives.get(perspective, {}).get('objectives', [])
            for obj in objs[:2]:
                focus_areas.append(obj.get('objective', ''))

        if focus_areas:
            areas_text = ', '.join(focus_areas[:3])
            return f"To enable organizational excellence through {entity_name}'s strategic priorities: {areas_text}"
        return f"To be a strategic partner driving organizational capability and performance through {entity_name}"

    def _generate_team_mission(self, text: str, entity_name: str, objectives: Dict) -> str:
        """Generate a team mission statement based on their strategic goals."""
        text_lower = text.lower()

        # Extract key activities from the document
        activities = []
        if 'talent' in text_lower:
            activities.append('talent development and management')
        if 'succession' in text_lower:
            activities.append('succession planning')
        if 'engagement' in text_lower:
            activities.append('employee engagement')
        if 'culture' in text_lower or 'values' in text_lower:
            activities.append('culture and values embedding')
        if 'coaching' in text_lower:
            activities.append('executive coaching')
        if 'development' in text_lower and 'organisation' in text_lower:
            activities.append('organizational development')

        if activities:
            activities_text = ', '.join(activities[:4])
            return f"To deliver {activities_text} that enables the organization to achieve its strategic objectives"
        return f"To provide strategic {entity_name} services that build organizational capability and drive performance"

    def _extract_vision(self, text: str) -> str:
        """Extract vision statement from document text.

        STRICTLY header-based: Only extracts content from 'Vision' header lines.
        Handles both "Vision: content" and "Vision" + content on next line formats.
        """
        import re

        lines = text.split('\n')

        # Look for "Vision" as a header
        for i, line in enumerate(lines):
            line_clean = line.strip()
            line_lower = line_clean.lower()

            # Check for "VISION: content" format (content on same line)
            if line_lower.startswith('vision:') or line_lower.startswith('our vision:'):
                # Extract content after the colon
                colon_pos = line_clean.find(':')
                if colon_pos != -1:
                    content = line_clean[colon_pos + 1:].strip()
                    if content and len(content) > 20:
                        return self._clean_extracted_text(content.strip('"\''))

            # Check for header-only line (content on next line)
            is_vision_header = False
            vision_header_patterns = [
                'vision', 'our vision', 'vision statement', 'company vision',
                'corporate vision', 'strategic vision'
            ]

            if len(line_clean) < 50:
                line_stripped = line_lower.strip(':').strip()
                if line_stripped in vision_header_patterns:
                    is_vision_header = True

            if is_vision_header:
                # Collect content directly below the header
                vision_parts = []
                for j in range(i + 1, min(i + 8, len(lines))):
                    next_line = lines[j].strip()

                    # Skip empty lines at the beginning
                    if not next_line and not vision_parts:
                        continue
                    # Stop at empty line after we've collected content
                    if not next_line and vision_parts:
                        break
                    # Stop at new section headers
                    if len(next_line) < 50:
                        next_lower = next_line.lower()
                        if next_line.endswith(':') or any(h in next_lower for h in ['mission', 'purpose', 'values', 'culture', 'strategy', 'objective']):
                            break
                    # Skip metadata lines
                    if self._is_metadata_line(next_line):
                        continue
                    # Add this line to vision
                    vision_parts.append(next_line.strip('"\''))

                if vision_parts:
                    vision = ' '.join(vision_parts)
                    vision = self._clean_extracted_text(vision)
                    if len(vision) > 20:
                        return vision

        return "Vision not explicitly stated in uploaded documents"

    def _is_metadata_line(self, line: str) -> bool:
        """Check if a line appears to be metadata (page numbers, security markers, etc.)."""
        line_stripped = line.strip()

        # Pure numbers (page numbers)
        if line_stripped.isdigit():
            return True

        # Lines that are just security markers
        security_patterns = ['<restricted>', '<confidential>', '<internal>', '<public>',
                           'restricted', 'confidential', 'internal use', 'page ']
        line_lower = line_stripped.lower()
        if any(line_lower == pattern or line_lower.startswith(pattern) for pattern in security_patterns):
            return True

        # Lines that are very short and contain only numbers/special chars
        if len(line_stripped) < 10 and not any(c.isalpha() for c in line_stripped):
            return True

        return False

    def _clean_extracted_text(self, text: str) -> str:
        """Clean extracted text by removing artifacts, page numbers, and security markers."""
        import re

        # Remove common document artifacts
        # Security classification markers
        text = re.sub(r'<\s*(Restricted|Confidential|Internal|Public)\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(\s*(Restricted|Confidential|Internal|Public)\s*\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[\s*(Restricted|Confidential|Internal|Public)\s*\]', '', text, flags=re.IGNORECASE)

        # Trailing page numbers (e.g., "... text 32" or "... text | 32")
        text = re.sub(r'\s*[\|/\\]\s*\d+\s*$', '', text)
        text = re.sub(r'\s+\d{1,3}\s*$', '', text)  # Standalone numbers at end

        # Page references
        text = re.sub(r'\s*page\s+\d+\s*', ' ', text, flags=re.IGNORECASE)

        # Clean up quotes and punctuation at boundaries
        text = re.sub(r'^[:\s\-"\']+', '', text)
        text = re.sub(r'["\'\s]+$', '', text)

        # Clean up any double spaces
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove trailing fragments that look incomplete (ending with numbers or single words after period)
        text = re.sub(r'\.\s+\d+\s*$', '.', text)
        text = re.sub(r'\.\s+[A-Z][a-z]{0,3}\s*$', '.', text)  # Trailing partial words

        return text.strip()

    def _extract_mission(self, text: str) -> str:
        """Extract mission/purpose statement from document text.

        STRICTLY header-based: Only extracts content from 'Mission' or 'Purpose' header lines.
        Handles both "Mission: content" and "Mission" + content on next line formats.
        """
        import re

        lines = text.split('\n')

        # Look for "Mission" or "Purpose" as a header
        for i, line in enumerate(lines):
            line_clean = line.strip()
            line_lower = line_clean.lower()

            # Check for "MISSION: content" format (content on same line)
            mission_prefixes = ['mission:', 'our mission:', 'purpose:', 'our purpose:']
            for prefix in mission_prefixes:
                if line_lower.startswith(prefix):
                    # Extract content after the colon
                    colon_pos = line_clean.find(':')
                    if colon_pos != -1:
                        content = line_clean[colon_pos + 1:].strip()
                        if content and len(content) > 15:
                            return self._clean_extracted_text(content.strip('"\''))

            # Check for header-only line (content on next line)
            is_mission_header = False
            mission_header_patterns = [
                'mission', 'our mission', 'mission statement', 'company mission',
                'purpose', 'our purpose', 'purpose statement', 'company purpose',
                'corporate mission', 'corporate purpose'
            ]

            if len(line_clean) < 50:
                line_stripped = line_lower.strip(':').strip()
                if line_stripped in mission_header_patterns:
                    is_mission_header = True

            if is_mission_header:
                # Collect content directly below the header
                mission_parts = []
                for j in range(i + 1, min(i + 8, len(lines))):
                    next_line = lines[j].strip()

                    # Skip empty lines at the beginning
                    if not next_line and not mission_parts:
                        continue
                    # Stop at empty line after we've collected content
                    if not next_line and mission_parts:
                        break
                    # Stop at new section headers
                    if len(next_line) < 50:
                        next_lower = next_line.lower()
                        if next_line.endswith(':') or any(h in next_lower for h in ['vision', 'values', 'culture', 'strategy', 'objective']):
                            break
                    # Skip metadata lines
                    if self._is_metadata_line(next_line):
                        continue
                    # Add this line to mission
                    mission_parts.append(next_line.strip('"\''))

                if mission_parts:
                    mission = ' '.join(mission_parts)
                    mission = self._clean_extracted_text(mission)
                    if len(mission) > 15:
                        return mission

        return "Mission/Purpose not explicitly stated in uploaded documents"

    def _extract_values(self, text: str) -> List[str]:
        """Extract organizational values from document text.

        STRICTLY header-based: Only extracts content directly below 'Values' or 'Culture' headers.
        """
        import re

        values = []
        lines = text.split('\n')

        # Known SATS values for recognition
        sats_values = ['safety', 'customer focus', 'respect', 'excellence', 'teamwork']

        # Known corporate values for validation
        known_values = [
            'safety', 'customer focus', 'respect', 'excellence', 'teamwork',
            'integrity', 'innovation', 'collaboration', 'accountability',
            'transparency', 'sustainability', 'quality', 'diversity',
            'inclusion', 'trust', 'agility', 'passion', 'empowerment',
            'commitment', 'responsibility', 'ethics', 'professionalism',
            'ownership', 'openness', 'courage', 'learning', 'curiosity'
        ]

        # Terms to exclude (business segments, regions, etc.)
        excluded_terms = [
            'services', 'service', 'gateway', 'solutions', 'operations',
            'business', 'division', 'segment', 'management', 'logistics',
            'cargo', 'aviation', 'catering', 'food', 'travel', 'airline',
            'emeaa', 'emea', 'apac', 'americas', 'asia', 'europe', 'pacific',
            'region', 'global', 'international', 'centralized', 'examination',
            'strategy', 'strategic', 'objective', 'goal', 'target',
            'e-commerce', 'ecommerce', 'digital', 'technology', 'platform',
            'offerings', 'provider', 'best-in-class', 'countries', 'territories'
        ]

        # Headers that indicate a values or culture section
        values_header_patterns = [
            'values', 'our values', 'core values', 'people values', 'company values',
            'culture', 'our culture', 'company culture',
            'sats values', 'sats people values'
        ]

        # Look for values/culture headers and extract content below
        for i, line in enumerate(lines):
            line_clean = line.strip()
            line_lower = line_clean.lower()

            # Check if this line is a values/culture header
            is_values_header = False
            if len(line_clean) < 50:  # Headers are typically short
                line_stripped = line_lower.strip(':').strip()
                if line_stripped in values_header_patterns:
                    is_values_header = True
                elif line_clean.endswith(':') and any(p in line_lower for p in ['value', 'culture']):
                    # "Values:" or "Our Culture:" style headers
                    if 'vision' not in line_lower and 'mission' not in line_lower:
                        is_values_header = True

            if is_values_header:
                # Extract values from lines directly below the header
                found_values = []
                for j in range(i + 1, min(i + 20, len(lines))):
                    next_line = lines[j].strip()

                    # Skip empty lines at beginning
                    if not next_line and not found_values:
                        continue
                    # Stop at empty line after content
                    if not next_line and found_values:
                        break
                    # Stop at new section headers
                    if len(next_line) < 50:
                        next_lower = next_line.lower()
                        if next_line.endswith(':'):
                            break
                        if any(h in next_lower for h in ['vision', 'mission', 'strategy', 'objective', 'goal']):
                            break
                    # Skip metadata
                    if self._is_metadata_line(next_line):
                        continue

                    # Clean bullet points and numbering
                    clean_line = re.sub(r'^[\s\-•*\d.○◯●►▪→]+', '', next_line).strip()

                    # Extract value name (before colon or dash)
                    value_name = clean_line
                    if ':' in clean_line:
                        value_name = clean_line.split(':')[0].strip()
                    if ' - ' in value_name:
                        value_name = value_name.split(' - ')[0].strip()
                    if '–' in value_name:
                        value_name = value_name.split('–')[0].strip()

                    value_name = self._clean_extracted_text(value_name)
                    value_lower = value_name.lower() if value_name else ''

                    # Validate: must be short, capitalized, and not excluded
                    if (value_name and
                        3 < len(value_name) < 40 and
                        len(value_name.split()) <= 4 and
                        value_name[0].isupper() and
                        value_name not in found_values and
                        not any(term in value_lower for term in excluded_terms)):

                        # Prefer known values
                        is_known = any(kv in value_lower for kv in known_values)
                        if is_known or len(value_name.split()) <= 3:
                            found_values.append(value_name)

                if found_values:
                    return found_values[:10]

        # No values found under headers
        return []

    def _detect_company_name(self, text: str) -> Optional[str]:
        """Detect company name from document text for use in pattern matching.

        Looks for company names in common patterns like:
        - "About [Company]"
        - "[Company] Strategy"
        - "[Company] DNA"
        - "The [Company] Way"
        """
        import re

        # Common patterns where company name appears
        patterns = [
            r'about\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)',  # "About SATS"
            r'([A-Z][A-Za-z]+)\s+(?:strategy|strategic)',       # "SATS Strategy"
            r'([A-Z][A-Za-z]+)\s+(?:dna|culture|way|values)',   # "SATS DNA", "SATS Culture"
            r'the\s+([A-Z][A-Za-z]+)\s+way',                     # "The SATS Way"
            r'=+\s*DOCUMENT:\s*([A-Za-z]+)',                     # Document header pattern
        ]

        company_candidates = {}
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.strip().upper()
                # Skip common words that aren't company names
                skip_words = {'THE', 'OUR', 'AND', 'FOR', 'WITH', 'FROM', 'ABOUT',
                             'STRATEGIC', 'STRATEGY', 'DOCUMENT', 'CORPORATE'}
                if name not in skip_words and len(name) >= 2:
                    company_candidates[name] = company_candidates.get(name, 0) + 1

        # Return most frequently found name
        if company_candidates:
            return max(company_candidates, key=company_candidates.get)
        return None

    def _extract_themes(self, text: str) -> List[Dict[str, Any]]:
        """Extract strategic themes from document text."""
        import re

        themes = []
        text_lower = text.lower()

        # Common strategic theme patterns to look for
        theme_keywords = {
            'Digital Transformation': ['digital', 'technology', 'automation', 'ai', 'data-driven'],
            'Customer Excellence': ['customer', 'client', 'service excellence', 'customer experience'],
            'Operational Excellence': ['operational', 'efficiency', 'process', 'productivity', 'lean'],
            'Innovation': ['innovation', 'new products', 'r&d', 'research', 'creative'],
            'Sustainability': ['sustainability', 'environmental', 'green', 'carbon', 'esg'],
            'Growth': ['growth', 'expansion', 'market share', 'revenue growth', 'scale'],
            'Talent Development': ['talent', 'people', 'workforce', 'employee', 'human capital'],
            'Cost Leadership': ['cost reduction', 'cost efficiency', 'cost control', 'expense'],
            'Quality': ['quality', 'defect', 'six sigma', 'continuous improvement'],
            'Risk Management': ['risk', 'compliance', 'governance', 'control'],
        }

        theme_id = 1
        for theme_name, keywords in theme_keywords.items():
            keyword_count = sum(1 for kw in keywords if kw in text_lower)
            if keyword_count >= 2:
                # Extract a description from the text
                description = self._find_theme_description(text, keywords)
                themes.append({
                    "themeId": f"T{theme_id}",
                    "name": theme_name,
                    "description": description,
                    "linkedObjectives": []  # Will be populated by objectives
                })
                theme_id += 1

        # Look for explicitly named themes/pillars/priorities
        pillar_patterns = [
            r'strategic (?:pillar|priority|theme|focus)[:\s]+([^\n]{10,100})',
            r'(?:pillar|priority|theme) \d+[:\s]+([^\n]{10,100})',
            r'key (?:priority|focus|initiative)[:\s]+([^\n]{10,100})',
        ]

        for pattern in pillar_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                theme_name = match.strip().title()
                if not any(t['name'].lower() == theme_name.lower() for t in themes):
                    themes.append({
                        "themeId": f"T{theme_id}",
                        "name": theme_name,
                        "description": f"Strategic priority: {theme_name}",
                        "linkedObjectives": []
                    })
                    theme_id += 1

        if not themes:
            # Default themes based on Balanced Scorecard
            themes = [
                {"themeId": "T1", "name": "Strategic Focus", "description": "Primary strategic direction from uploaded documents", "linkedObjectives": []},
            ]

        return themes[:8]  # Cap at 8 themes

    def _find_theme_description(self, text: str, keywords: List[str]) -> str:
        """Find a description for a theme based on keywords."""
        import re

        for keyword in keywords:
            # Find sentences containing the keyword
            pattern = rf'[^.]*{keyword}[^.]*\.'
            matches = re.findall(pattern, text.lower())
            for match in matches:
                if 20 < len(match) < 200:
                    # Get original case
                    start = text.lower().find(match)
                    if start >= 0:
                        return text[start:start + len(match)].strip()

        return f"Focus on {keywords[0]} initiatives"

    def _is_coherent_text(self, text: str) -> bool:
        """Check if text is a coherent objective statement, not fragmented keywords."""
        import re

        # Too short or too long
        if len(text) < 20 or len(text) > 200:
            return False

        # Count words
        words = text.split()
        if len(words) < 5 or len(words) > 30:
            return False

        # Must start with a capital letter (proper sentence start)
        if not text[0].isupper():
            return False

        # Should NOT start with conjunctions or prepositions (indicates fragment)
        fragment_starts = ['and ', 'or ', 'but ', 'in ', 'on ', 'at ', 'to ', 'for ',
                          'with ', 'from ', 'by ', 'as ', 'into ', 'through ', 'across ']
        if any(text.lower().startswith(start) for start in fragment_starts):
            return False

        # Should have at least one verb-like word
        action_words = ['achieve', 'improve', 'increase', 'reduce', 'maintain', 'deliver',
                        'ensure', 'drive', 'develop', 'build', 'create', 'implement',
                        'establish', 'enhance', 'optimize', 'grow', 'expand', 'strengthen',
                        'provide', 'support', 'enable', 'transform', 'lead', 'manage',
                        'leverage', 'continue', 'innovate', 'scale']

        has_action = any(word in text.lower() for word in action_words)
        if not has_action:
            return False

        # Check it's not just a list of keywords (should have connecting words)
        connecting_words = ['the', 'to', 'and', 'of', 'in', 'for', 'by', 'with', 'our', 'a', 'an', 'through']
        connecting_count = sum(1 for word in words if word.lower() in connecting_words)
        if connecting_count < 2:
            return False

        # Shouldn't start with ## or other markdown artifacts
        if text.startswith('#') or text.startswith('|'):
            return False

        # Shouldn't be all caps (likely a heading misidentified)
        if text.isupper():
            return False

        # Should end properly (not mid-sentence)
        if text.endswith(' and') or text.endswith(' or') or text.endswith(' the'):
            return False

        return True

    def _clean_objective_text(self, text: str) -> str:
        """Clean and normalize objective text."""
        import re

        # Remove markdown artifacts
        text = re.sub(r'^#+\s*', '', text)
        text = re.sub(r'\|', ' ', text)

        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Remove leading/trailing punctuation
        text = text.strip(' \t\n\r-•*:;,.')

        # Capitalize first letter
        if text and text[0].islower():
            text = text[0].upper() + text[1:]

        return text

    def _extract_objectives(self, text: str, themes: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Extract strategic objectives organized by BSC perspective.

        Focuses on extracting complete, coherent objective statements,
        avoiding fragmented text or partial sentences.
        """
        import re

        perspectives = {
            "financial": {"objectives": [], "keywords": ['revenue', 'profit', 'cost', 'margin', 'growth', 'roi', 'shareholder', 'ebitda', 'financial', 'returns']},
            "customer": {"objectives": [], "keywords": ['customer', 'client', 'satisfaction', 'nps', 'market', 'loyalty', 'service', 'network', 'hub', 'offering']},
            "internalProcess": {"objectives": [], "keywords": ['process', 'operational', 'efficiency', 'quality', 'delivery', 'productivity', 'capability', 'system']},
            "learningGrowth": {"objectives": [], "keywords": ['employee', 'training', 'skill', 'talent', 'culture', 'capability', 'engagement', 'learning', 'people', 'workforce']}
        }

        theme_names = [t['name'].lower() for t in themes]
        found_objectives = []
        lines = text.split('\n')

        # Action verbs that typically start objectives
        action_starts = [
            'achieve', 'improve', 'increase', 'reduce', 'maintain', 'deliver',
            'ensure', 'drive', 'develop', 'build', 'create', 'implement',
            'establish', 'enhance', 'optimize', 'grow', 'expand', 'strengthen',
            'provide', 'support', 'enable', 'transform', 'lead', 'manage',
            'leverage', 'continue', 'innovate', 'scale', 'we will', 'focus on'
        ]

        # Extract objectives from complete lines that start with action verbs
        for line in lines:
            # Clean bullet points and numbering at start
            line_clean = re.sub(r'^[\s\-•*\d.○◯●►▪→A-C\)\]]+', '', line).strip()

            # Skip short lines or metadata
            if len(line_clean) < 25:
                continue
            if self._is_metadata_line(line_clean):
                continue

            # Check if line starts with an action word (good objective indicator)
            line_lower = line_clean.lower()
            starts_with_action = any(line_lower.startswith(action) for action in action_starts)

            if starts_with_action:
                # Clean and validate
                cleaned = self._clean_objective_text(line_clean)
                if self._is_coherent_text(cleaned):
                    # Avoid duplicates
                    if cleaned.lower() not in [o.lower() for o in found_objectives]:
                        found_objectives.append(cleaned)

        # Categorize objectives by perspective
        obj_counters = {'F': 1, 'C': 1, 'P': 1, 'L': 1}

        for obj_text in found_objectives[:20]:  # Process up to 20 objectives
            # Determine perspective based on keywords
            obj_text_lower = obj_text.lower()
            best_perspective = None
            best_score = 0

            for p_name, p_data in perspectives.items():
                score = sum(1 for kw in p_data['keywords'] if kw in obj_text_lower)
                if score > best_score:
                    best_score = score
                    best_perspective = p_name

            if best_perspective and best_score > 0:
                prefix_map = {'financial': 'F', 'customer': 'C', 'internalProcess': 'P', 'learningGrowth': 'L'}
                prefix = prefix_map[best_perspective]
                obj_id = f"{prefix}{obj_counters[prefix]}"
                obj_counters[prefix] += 1

                # Find related themes
                related_themes = []
                for theme in themes:
                    theme_lower = theme['name'].lower()
                    if any(word in obj_text_lower for word in theme_lower.split()):
                        related_themes.append(theme['name'])
                        if obj_id not in theme['linkedObjectives']:
                            theme['linkedObjectives'].append(obj_id)

                # Extract key measures from the text
                measures = self._extract_measures(obj_text_lower, text)

                # Use the already cleaned objective text
                obj_text_clean = obj_text
                if obj_text_clean and obj_text_clean[0].islower():
                    obj_text_clean = obj_text_clean[0].upper() + obj_text_clean[1:]

                perspectives[best_perspective]['objectives'].append({
                    "id": obj_id,
                    "objective": obj_text_clean,
                    "keyMeasures": measures if measures else ["To be defined"],
                    "strategicThemes": related_themes if related_themes else [themes[0]['name']] if themes else []
                })

        # Ensure at least one objective per perspective
        for p_name, p_data in perspectives.items():
            if not p_data['objectives']:
                prefix_map = {'financial': 'F', 'customer': 'C', 'internalProcess': 'P', 'learningGrowth': 'L'}
                prefix = prefix_map[p_name]
                default_objectives = {
                    'financial': 'Achieve financial targets as outlined in strategy documents',
                    'customer': 'Deliver value to customers and stakeholders',
                    'internalProcess': 'Optimize operational processes and efficiency',
                    'learningGrowth': 'Develop organizational capabilities and talent'
                }
                p_data['objectives'].append({
                    "id": f"{prefix}1",
                    "objective": default_objectives[p_name],
                    "keyMeasures": ["To be defined based on strategy documents"],
                    "strategicThemes": [themes[0]['name']] if themes else []
                })

        # Return only the objectives structure
        return {
            p_name: {"objectives": p_data['objectives']}
            for p_name, p_data in perspectives.items()
        }

    def _extract_measures(self, objective_text: str, full_text: str) -> List[str]:
        """Extract key measures/KPIs related to an objective."""
        import re

        measures = []

        # Look for percentage targets
        pct_matches = re.findall(r'(\d+%)', objective_text)
        for match in pct_matches:
            measures.append(f"Target: {match}")

        # Look for numeric targets
        num_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(million|billion|k|m|b)?', objective_text)
        for match in num_matches:
            if match[1]:
                measures.append(f"Target: {match[0]}{match[1]}")

        # Look for common KPI terms
        kpi_terms = ['nps', 'csat', 'roi', 'margin', 'revenue', 'cost', 'rate', 'score', 'index']
        for term in kpi_terms:
            if term in objective_text.lower():
                measures.append(f"{term.upper()} measurement")

        return list(set(measures))[:3]  # Return up to 3 unique measures

    def _extract_kprs(self, text: str, objectives: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract key performance requirements from document text."""
        import re

        kprs = []
        text_lower = text.lower()

        # Look for requirement-like statements
        req_patterns = [
            r'(?:must|shall|should|need to|required to)[:\s]+([^\n.]{20,150})',
            r'(?:critical|essential|key|important)[:\s]+([^\n.]{20,150})',
            r'(?:priority|imperative)[:\s]+([^\n.]{20,150})',
        ]

        found_requirements = []
        for pattern in req_patterns:
            matches = re.findall(pattern, text_lower)
            found_requirements.extend(matches)

        kpr_id = 1
        for req in found_requirements[:6]:  # Limit to 6 KPRs
            # Determine perspective
            perspective = 'process'  # Default
            if any(kw in req for kw in ['revenue', 'profit', 'cost', 'financial']):
                perspective = 'financial'
            elif any(kw in req for kw in ['customer', 'client', 'satisfaction']):
                perspective = 'customer'
            elif any(kw in req for kw in ['employee', 'talent', 'skill', 'learning']):
                perspective = 'learning'

            # Determine priority
            priority = 'high'
            if any(kw in req for kw in ['critical', 'essential', 'must']):
                priority = 'critical'
            elif any(kw in req for kw in ['should', 'important']):
                priority = 'high'

            # Link to relevant objectives
            linked_objs = []
            for p_name, p_data in objectives.items():
                for obj in p_data.get('objectives', []):
                    obj_text = obj.get('objective', '').lower()
                    if any(word in obj_text for word in req.split() if len(word) > 4):
                        linked_objs.append(obj['id'])

            kprs.append({
                "id": f"KPR{kpr_id}",
                "requirement": req.strip().capitalize(),
                "perspective": perspective,
                "priority": priority,
                "linkedObjectiveIds": linked_objs[:3] if linked_objs else []
            })
            kpr_id += 1

        if not kprs:
            # Add default KPR
            kprs.append({
                "id": "KPR1",
                "requirement": "Ensure strategic alignment across all organizational levels",
                "perspective": "process",
                "priority": "critical",
                "linkedObjectiveIds": ["P1"]
            })

        return kprs

    def test_connection(self) -> bool:
        """Mock connection test."""
        return True
