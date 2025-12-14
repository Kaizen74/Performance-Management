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
        # Extract actual content from documents
        vision = self._extract_vision(documents_text)
        mission = self._extract_mission(documents_text)
        values = self._extract_values(documents_text)
        strategic_themes = self._extract_themes(documents_text)
        objectives = self._extract_objectives(documents_text, strategic_themes)
        kprs = self._extract_kprs(documents_text, objectives)

        return {
            "organizationalPurpose": {
                "vision": vision,
                "mission": mission,
                "values": values
            },
            "strategicPerspectives": objectives,
            "strategicThemes": strategic_themes,
            "keyPerformanceRequirements": kprs
        }

    def _extract_vision(self, text: str) -> str:
        """Extract vision statement from document text."""
        import re

        # First try to find explicit vision section/statement
        lines = text.split('\n')

        # Look for "Vision Statement" as a header followed by the actual vision
        for i, line in enumerate(lines):
            line_clean = line.strip()
            line_lower = line_clean.lower()

            # Check if this line is a vision header
            if ('vision' in line_lower and
                ('statement' in line_lower or len(line_clean) < 30) and
                'mission' not in line_lower):
                # Look at the next few lines for the actual vision text
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    # Skip empty lines and short lines
                    if len(next_line) > 30 and not next_line.lower().startswith(('our', 'the', 'vision')):
                        # This is likely the vision statement
                        if next_line[0].isupper() or next_line.startswith('"'):
                            # Clean up quotes if present
                            vision = next_line.strip('"\'')
                            if len(vision) > 30:
                                return vision
                    elif len(next_line) > 30 and next_line[0].isupper():
                        return next_line.strip('"\'')

        # Look for pattern "Vision:" or "Our Vision:" followed by text
        patterns = [
            r'vision statement[:\s]*[\n\r]+([^\n]{30,300})',
            r'our vision[:\s]*[\n\r]+([^\n]{30,300})',
            r'vision[:\s]+["\'"]?([^"\'\n]{30,300})["\'"]?',
            r'vision[:\s]*[\n\r]+([^\n]{30,300})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                start, end = match.span(1)
                vision = text[start:end].strip()
                vision = re.sub(r'^[:\s\-"\']+', '', vision)
                vision = re.sub(r'["\'\s]+$', '', vision)
                if len(vision) > 30:
                    return vision

        # Look for sentences that look like vision statements
        vision_indicators = [
            "world's leading", "leading provider", "to be the", "become the",
            "recognized as", "premier", "best-in-class", "global leader"
        ]

        for line in lines:
            line_clean = line.strip()
            if len(line_clean) > 30 and len(line_clean) < 250:
                line_lower = line_clean.lower()
                for indicator in vision_indicators:
                    if indicator in line_lower:
                        return line_clean.strip('"\'')

        return "Vision not explicitly stated in uploaded documents"

    def _extract_mission(self, text: str) -> str:
        """Extract mission/purpose statement from document text."""
        import re

        lines = text.split('\n')

        # Look for "Purpose Statement" or "Mission Statement" as a header
        for i, line in enumerate(lines):
            line_clean = line.strip()
            line_lower = line_clean.lower()

            # Check if this line is a mission/purpose header
            if (('mission' in line_lower or 'purpose' in line_lower) and
                ('statement' in line_lower or len(line_clean) < 30)):
                # Look at the next few lines for the actual statement
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if len(next_line) > 20:
                        # This is likely the mission/purpose statement
                        mission = next_line.strip('"\'')
                        if len(mission) > 20:
                            return mission

        # Look for explicit patterns
        patterns = [
            r'purpose statement[:\s]*[\n\r]+([^\n]{20,300})',
            r'our purpose[:\s]*[\n\r]+([^\n]{20,300})',
            r'mission statement[:\s]*[\n\r]+([^\n]{20,300})',
            r'our mission[:\s]*[\n\r]+([^\n]{20,300})',
            r'purpose[:\s]+["\'"]?([^"\'\n]{20,300})["\'"]?',
            r'mission[:\s]+["\'"]?([^"\'\n]{20,300})["\'"]?',
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                start, end = match.span(1)
                mission = text[start:end].strip()
                mission = re.sub(r'^[:\s\-"\']+', '', mission)
                mission = re.sub(r'["\'\s]+$', '', mission)
                if len(mission) > 20:
                    return mission

        # Look for mission-like phrases
        mission_indicators = [
            "powering", "enabling", "delivering", "connecting",
            "we exist to", "our purpose is", "we are committed to"
        ]

        for line in lines:
            line_clean = line.strip()
            if len(line_clean) > 20 and len(line_clean) < 200:
                line_lower = line_clean.lower()
                for indicator in mission_indicators:
                    if line_lower.startswith(indicator) or indicator in line_lower:
                        return line_clean.strip('"\'')

        return "Mission/Purpose not explicitly stated in uploaded documents"

    def _extract_values(self, text: str) -> List[str]:
        """Extract organizational values from document text."""
        import re

        values = []
        text_lower = text.lower()
        lines = text.split('\n')

        # Common corporate values - expanded list including SATS values
        common_values = [
            # SATS specific values
            'safety', 'customer focus', 'respect', 'excellence', 'teamwork',
            # General corporate values
            'integrity', 'innovation', 'collaboration', 'accountability',
            'transparency', 'sustainability', 'quality', 'diversity',
            'inclusion', 'trust', 'agility', 'passion', 'empowerment',
            'leadership', 'commitment', 'responsibility', 'ethics',
            'professionalism', 'continuous improvement', 'service excellence',
            'people', 'performance', 'growth', 'caring'
        ]

        # Look for explicit values section - "Our Values", "Core Values", "People Values", etc.
        in_values_section = False
        values_section_lines = 0

        for i, line in enumerate(lines):
            line_clean = line.strip()
            line_lower = line_clean.lower()

            # Detect start of values section
            if (('value' in line_lower and len(line_clean) < 50) or
                'core values' in line_lower or
                'our values' in line_lower or
                'people values' in line_lower or
                'company values' in line_lower or
                'organizational values' in line_lower):
                in_values_section = True
                values_section_lines = 0
                continue

            if in_values_section:
                values_section_lines += 1

                # Check for bullet points, circles, or value names
                clean_line = re.sub(r'^[\s\-•*\d.○◯●]+', '', line_clean).strip()

                # Remove explanatory text after value name
                if ':' in clean_line:
                    clean_line = clean_line.split(':')[0].strip()
                if ' - ' in clean_line:
                    clean_line = clean_line.split(' - ')[0].strip()
                if '–' in clean_line:
                    clean_line = clean_line.split('–')[0].strip()

                # Check if this looks like a value name (short, capitalized)
                if clean_line and 2 < len(clean_line) < 40:
                    # Check if it's a known value or looks like a value name
                    clean_lower = clean_line.lower()
                    is_known_value = any(val in clean_lower for val in common_values)
                    is_capitalized = clean_line[0].isupper()
                    is_short_phrase = len(clean_line.split()) <= 3

                    if (is_known_value or (is_capitalized and is_short_phrase)):
                        if clean_line.lower() not in [v.lower() for v in values]:
                            values.append(clean_line.title())

                # Exit section after finding several values or hitting empty line/new section
                if len(line_clean) == 0 and values_section_lines > 2:
                    if values:  # Only exit if we found some values
                        in_values_section = False
                if values_section_lines > 15:
                    in_values_section = False

        # If no explicit values section found, look for value mentions in context
        if not values:
            for value in common_values:
                if value in text_lower:
                    # Check if it's mentioned in a values context
                    value_patterns = [
                        rf'value[s]?[:\s].*{value}',
                        rf'{value}.*value',
                        rf'core.*{value}',
                        rf'we (?:value|believe in).*{value}',
                        rf'our {value}',
                    ]
                    for pattern in value_patterns:
                        if re.search(pattern, text_lower):
                            if value.title() not in values:
                                values.append(value.title())
                            break

        # Remove duplicates while preserving order
        seen = set()
        unique_values = []
        for v in values:
            v_lower = v.lower()
            if v_lower not in seen:
                seen.add(v_lower)
                unique_values.append(v)

        if not unique_values:
            return ["Values not explicitly stated in uploaded documents"]

        return unique_values[:10]  # Cap at 10 values

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
        """Check if text is a coherent sentence/phrase, not fragmented keywords."""
        import re

        # Too short or too long
        if len(text) < 15 or len(text) > 300:
            return False

        # Count words
        words = text.split()
        if len(words) < 4:
            return False

        # Check for common sentence structure indicators
        # Should have at least one verb-like word
        action_words = ['achieve', 'improve', 'increase', 'reduce', 'maintain', 'deliver',
                        'ensure', 'drive', 'develop', 'build', 'create', 'implement',
                        'establish', 'enhance', 'optimize', 'grow', 'expand', 'strengthen',
                        'provide', 'support', 'enable', 'transform', 'lead', 'manage']

        has_action = any(word in text.lower() for word in action_words)
        if not has_action:
            return False

        # Check it's not just a list of keywords (should have connecting words)
        connecting_words = ['the', 'to', 'and', 'of', 'in', 'for', 'by', 'with', 'our', 'a', 'an', 'through']
        connecting_count = sum(1 for word in words if word.lower() in connecting_words)
        if connecting_count < 1:
            return False

        # Shouldn't start with ## or other markdown artifacts
        if text.startswith('#') or text.startswith('|'):
            return False

        # Shouldn't be all caps (likely a heading misidentified)
        if text.isupper():
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
        """Extract strategic objectives organized by BSC perspective."""
        import re

        perspectives = {
            "financial": {"objectives": [], "keywords": ['revenue', 'profit', 'cost', 'margin', 'growth', 'roi', 'shareholder', 'ebitda', 'financial']},
            "customer": {"objectives": [], "keywords": ['customer', 'client', 'satisfaction', 'nps', 'market share', 'loyalty', 'service']},
            "internalProcess": {"objectives": [], "keywords": ['process', 'operational', 'efficiency', 'quality', 'delivery', 'cycle time', 'productivity']},
            "learningGrowth": {"objectives": [], "keywords": ['employee', 'training', 'skill', 'talent', 'culture', 'capability', 'engagement', 'learning']}
        }

        text_lower = text.lower()
        theme_names = [t['name'].lower() for t in themes]

        # Look for objective-like statements
        objective_patterns = [
            r'(?:objective|goal|target|aim)[:\s]+([^\n.]{20,150})',
            r'(?:achieve|attain|reach|improve|increase|reduce|maintain)[:\s]+([^\n.]{15,150})',
            r'(?:by \d{4})[,\s]+([^\n.]{20,150})',
            r'(\d+%[^\n.]{10,100})',
        ]

        found_objectives = []
        for pattern in objective_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                cleaned = self._clean_objective_text(match)
                if cleaned not in found_objectives and self._is_coherent_text(cleaned):
                    found_objectives.append(cleaned)

        # Also look for bullet points and numbered items that look like objectives
        lines = text.split('\n')
        for line in lines:
            line_clean = re.sub(r'^[\s\-•*\d.]+', '', line).strip()
            line_clean = self._clean_objective_text(line_clean)
            if self._is_coherent_text(line_clean):
                if line_clean.lower() not in [o.lower() for o in found_objectives]:
                    found_objectives.append(line_clean)

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
