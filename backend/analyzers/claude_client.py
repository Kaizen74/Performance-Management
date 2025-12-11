"""
Claude API Client
Wrapper for Anthropic Claude API with retry logic and error handling.
"""

import os
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ClaudeResponse:
    """Structured response from Claude API."""
    content: str
    model: str
    usage: Dict[str, int]
    stop_reason: str


class ClaudeClient:
    """
    Client for interacting with Anthropic Claude API.
    Handles authentication, retries, and response parsing.
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize the Anthropic client."""
        if not self.api_key:
            raise ValueError(
                "API key required. Provide via constructor or ANTHROPIC_API_KEY env var."
            )

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "anthropic package required. Install with: pip install anthropic"
            )

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3
    ) -> ClaudeResponse:
        """
        Send a completion request to Claude.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            model: Model to use (defaults to claude-sonnet-4-20250514)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)

        Returns:
            ClaudeResponse with content and metadata
        """
        model = model or self.DEFAULT_MODEL
        messages = [{"role": "user", "content": prompt}]

        for attempt in range(self.MAX_RETRIES):
            try:
                kwargs = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": messages,
                    "temperature": temperature
                }

                if system_prompt:
                    kwargs["system"] = system_prompt

                response = self.client.messages.create(**kwargs)

                return ClaudeResponse(
                    content=response.content[0].text,
                    model=response.model,
                    usage={
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens
                    },
                    stop_reason=response.stop_reason
                )

            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue
                raise RuntimeError(f"Claude API error after {self.MAX_RETRIES} retries: {str(e)}")

    def analyze_strategy(
        self,
        documents_text: str,
        output_schema: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze strategy documents and extract structured framework.

        Args:
            documents_text: Combined text from strategy documents
            output_schema: Optional JSON schema for output structure

        Returns:
            Parsed JSON response with strategic framework
        """
        system_prompt = """You are an expert in strategic planning frameworks including
Balanced Scorecard, Strategy Maps, and OKRs. You analyze organizational strategy documents
and extract structured strategic frameworks. Always return valid JSON."""

        prompt = f"""Analyze the following organizational strategy documents and extract a coherent strategic framework.

DOCUMENTS:
{documents_text}

OUTPUT REQUIREMENTS:
1. Identify the core vision, mission, and organizational values
2. Extract strategic objectives and categorize into Balanced Scorecard perspectives:
   - Financial: Revenue, profitability, shareholder value objectives
   - Customer: Value proposition, customer satisfaction, market position
   - Internal Process: Operational excellence, innovation, regulatory compliance
   - Learning & Growth: Capabilities, culture, technology, human capital
3. Identify strategic themes that connect objectives across perspectives
4. Derive Key Performance Requirements that leadership must achieve

Apply the "Golden Thread" principle - ensure vertical alignment from vision to specific performance requirements.

Return ONLY valid JSON matching this structure:
{{
    "organizationalPurpose": {{
        "vision": "string",
        "mission": "string",
        "values": ["string"]
    }},
    "strategicPerspectives": {{
        "financial": {{
            "objectives": [
                {{
                    "id": "F1",
                    "objective": "string",
                    "keyMeasures": ["string"],
                    "strategicThemes": ["string"]
                }}
            ]
        }},
        "customer": {{ "objectives": [...] }},
        "internalProcess": {{ "objectives": [...] }},
        "learningGrowth": {{ "objectives": [...] }}
    }},
    "strategicThemes": [
        {{
            "themeId": "T1",
            "name": "string",
            "description": "string",
            "linkedObjectives": ["F1", "C2", "P3"]
        }}
    ],
    "keyPerformanceRequirements": [
        {{
            "id": "KPR1",
            "requirement": "string",
            "perspective": "financial|customer|process|learning",
            "priority": "critical|high|medium",
            "linkedObjectiveIds": ["F1", "C1"]
        }}
    ]
}}"""

        response = self.complete(prompt, system_prompt=system_prompt, max_tokens=8192)

        # Parse JSON from response
        import json
        try:
            # Try to extract JSON from response
            content = response.content.strip()

            # Handle markdown code blocks
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Claude response as JSON: {str(e)}")

    def analyze_goal_alignment(
        self,
        strategic_framework: Dict[str, Any],
        goal_document_text: str
    ) -> Dict[str, Any]:
        """
        Analyze alignment between goals and strategic framework.

        Args:
            strategic_framework: Structured strategic framework from analyze_strategy
            goal_document_text: Text content of goal document

        Returns:
            Alignment analysis with scores and recommendations
        """
        import json

        system_prompt = """You are an expert in performance management and strategy execution.
You analyze employee goals against organizational strategy to assess alignment and impact.
Use semantic understanding, not just keyword matching. Always return valid JSON."""

        prompt = f"""Analyze the alignment between employee goals and the strategic framework.

STRATEGIC FRAMEWORK:
{json.dumps(strategic_framework, indent=2)}

EMPLOYEE GOAL DOCUMENT:
{goal_document_text}

ANALYSIS TASK:
1. ALIGNMENT ANALYSIS: For each goal in this document:
   - Identify which strategic objectives it directly supports
   - Assess semantic alignment strength (not just keyword overlap)
   - Identify missing linkages (strategic priorities not addressed)

2. IMPACT ANALYSIS: Evaluate each goal's potential impact:
   - Strategic leverage: Does this goal enable multiple objectives?
   - Measurability: Are targets SMART and trackable?
   - Ambition level: Stretch goal or incremental improvement?

3. GAP ANALYSIS:
   - Which critical strategic objectives have no supporting goals?
   - Which goals are "orphaned" (no clear strategic linkage)?

SCORING CRITERIA:
- Alignment Score (0-100): Semantic connection to strategic framework
- Impact Score (0-100): Potential contribution to strategic outcomes

Return ONLY valid JSON matching this structure:
{{
    "overallAlignmentScore": 75,
    "overallImpactScore": 68,
    "goals": [
        {{
            "goalId": "G1",
            "goalText": "string",
            "alignmentScore": 82,
            "impactScore": 70,
            "alignedObjectives": ["F1", "P2"],
            "alignmentRationale": "string",
            "impactRationale": "string",
            "gaps": ["string"]
        }}
    ],
    "strategicCoverage": {{
        "financial": {{ "covered": 2, "total": 3, "percentage": 67 }},
        "customer": {{ "covered": 1, "total": 4, "percentage": 25 }},
        "process": {{ "covered": 3, "total": 3, "percentage": 100 }},
        "learning": {{ "covered": 0, "total": 2, "percentage": 0 }}
    }},
    "recommendations": ["string"]
}}"""

        response = self.complete(prompt, system_prompt=system_prompt, max_tokens=8192)

        # Parse JSON from response
        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse alignment analysis as JSON: {str(e)}")

    def generate_recommendations(
        self,
        strategic_framework: Dict[str, Any],
        current_goals: str,
        alignment_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate improved goal recommendations.

        Args:
            strategic_framework: Structured strategic framework
            current_goals: Current goal document text
            alignment_analysis: Results from alignment analysis

        Returns:
            Recommendations for improved goals
        """
        import json

        system_prompt = """You are an expert in performance management, OKRs, and strategic goal-setting.
You generate improved performance goals that align with organizational strategy.
Goals should be SMART and evidence-based. Always return valid JSON."""

        prompt = f"""Generate 5 revised performance goals that would significantly improve strategic alignment.

STRATEGIC FRAMEWORK:
{json.dumps(strategic_framework, indent=2)}

CURRENT GOALS:
{current_goals}

ALIGNMENT ANALYSIS:
{json.dumps(alignment_analysis, indent=2)}

For each of 5 recommendations, provide:
1. Revised Goal Statement (SMART format with OKR structure)
2. Strategic Linkage: Which objectives this supports
3. Predicted Alignment Score Improvement
4. Evidence/Rationale: Why this goal structure is effective
5. Implementation Considerations: Dependencies, risks, timeline

CONSTRAINTS:
- Goals must be achievable within typical performance cycle
- Build on existing competencies shown in current goals
- Consider team/organizational capacity

Return ONLY valid JSON matching this structure:
{{
    "recommendations": [
        {{
            "recommendationId": "R1",
            "revisedGoal": {{
                "objective": "string",
                "keyResults": ["string"],
                "timeline": "string",
                "metrics": ["string"]
            }},
            "strategicLinkages": ["F1", "C2", "P1"],
            "predictedAlignmentGain": 15,
            "evidence": {{
                "source": "string",
                "finding": "string"
            }},
            "implementationNotes": "string"
        }}
    ],
    "projectedNewAlignmentScore": 88,
    "projectedNewImpactScore": 82
}}"""

        response = self.complete(prompt, system_prompt=system_prompt, max_tokens=8192)

        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse recommendations as JSON: {str(e)}")

    def test_connection(self) -> bool:
        """
        Test the API connection with a simple request.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.complete(
                "Respond with just 'OK'",
                max_tokens=10,
                temperature=0
            )
            return "OK" in response.content.upper()
        except Exception:
            return False
