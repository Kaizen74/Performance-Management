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
        goal_document_text: str,
        employee_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze alignment between goals and strategic framework.

        Args:
            strategic_framework: Structured strategic framework from analyze_strategy
            goal_document_text: Text content of goal document
            employee_context: Optional employee metadata (job title, seniority, department, goals with weights)

        Returns:
            Alignment analysis with scores and recommendations
        """
        import json

        system_prompt = """You are an expert in performance management, strategy execution, and organizational effectiveness.
You analyze employee goals against organizational strategy to assess alignment, coherence, and strategic impact.
Use semantic understanding to evaluate how well goals translate organizational strategy into role-appropriate actions.
Consider the employee's position, seniority level, and scope of influence when evaluating goal appropriateness.
IMPORTANT: Always explicitly reference the specific vision, mission, and strategic objectives when explaining alignment.
Always return valid JSON."""

        # Extract key strategic elements for explicit referencing
        org_purpose = strategic_framework.get('organizationalPurpose', {})
        vision = org_purpose.get('vision', 'Not specified')
        mission = org_purpose.get('mission', 'Not specified')
        values = org_purpose.get('values', [])

        strategic_themes = strategic_framework.get('strategicThemes', [])
        theme_names = [t.get('name', '') for t in strategic_themes if t.get('name')]

        # Build strategic reference summary
        strategic_summary = f"""
KEY STRATEGIC REFERENCE POINTS (use these explicitly in your analysis):
- VISION: "{vision}"
- MISSION: "{mission}"
- VALUES: {', '.join(values) if values else 'Not specified'}
- STRATEGIC THEMES: {', '.join(theme_names) if theme_names else 'Not specified'}
"""

        # Build employee context section if available
        employee_section = ""
        if employee_context:
            employee_section = f"""
EMPLOYEE CONTEXT:
- Name: {employee_context.get('employeeName', 'Unknown')}
- Job Title: {employee_context.get('jobTitle', 'Not specified')}
- Department: {employee_context.get('department', 'Not specified')}
- Seniority Level: {employee_context.get('seniorityLevel', 'Not specified')}
"""
            # Include goal weights if available
            goals_with_weights = employee_context.get('goalsWithWeights', [])
            if goals_with_weights:
                employee_section += "\nGOAL WEIGHTS:\n"
                for gw in goals_with_weights:
                    weight = gw.get('weight', 'N/A')
                    employee_section += f"- {gw.get('goalText', '')[:80]}... (Weight: {weight})\n"

        prompt = f"""Analyze the alignment between employee goals and the strategic framework, considering the employee's role and level.
{strategic_summary}
FULL STRATEGIC FRAMEWORK:
{json.dumps(strategic_framework, indent=2)}
{employee_section}
EMPLOYEE GOAL DOCUMENT:
{goal_document_text}

ANALYSIS REQUIREMENTS:

0. STRATEGY-GOAL COHERENCE CHECK (CRITICAL - DO THIS FIRST):
   - Assess whether the employee's goals appear to be relevant to this specific organizational strategy
   - Look for MISMATCHES: Do the goals reference different strategic priorities, different industry context, or different organizational focus than the strategy documents?
   - If goals mention specific initiatives, products, or priorities NOT found in the strategy, flag this as a potential mismatch
   - Consider if the employee might be from a different team/department than the strategy document covers
   - Provide a coherence confidence score (0-100) indicating how confident you are these goals belong to this strategy

1. EXPLICIT STRATEGIC TIE-BACK: For each goal, you MUST:
   - Quote or directly reference which part of the vision/mission this goal supports
   - Identify which specific strategic themes from the framework this goal addresses
   - Explain how this goal contributes to the stated organizational values
   - Map to specific strategic objectives by ID (F1, C2, P3, L1, etc.)

2. ROLE-APPROPRIATE ALIGNMENT: For each goal, assess:
   - Does this goal reflect appropriate strategic translation for this role/level?
   - For executives: Are goals focused on enterprise-wide outcomes and strategic enablement?
   - For senior staff: Do goals bridge strategy to operational excellence?
   - For mid-level: Are goals focused on team/functional contributions to strategic objectives?
   - For junior staff: Do goals demonstrate understanding of how daily work connects to strategy?

3. GOAL COHERENCE ASSESSMENT: Evaluate the employee's goal SET as a whole:
   - Internal consistency: Do goals complement each other or conflict?
   - Balanced coverage: Does the set address multiple strategic perspectives appropriately for this role?
   - Weight distribution: If weights provided, is emphasis appropriately placed on strategic priorities?
   - Scope appropriateness: Are goals within this person's sphere of influence?

4. STRATEGIC TRANSLATION QUALITY:
   - Does this employee demonstrate understanding of the SPECIFIC organizational strategy provided?
   - Are goals specific enough to be measurable yet connected to the stated vision and mission?
   - Do goals show appropriate ambition level for seniority (stretch for seniors, foundational for juniors)?

5. IMPACT ANALYSIS: Evaluate potential strategic contribution:
   - Direct vs. indirect strategic support
   - Leverage potential (does this goal enable others' success?)
   - Timeline alignment with strategic planning horizons

SCORING CRITERIA:
- Alignment Score (0-100): How well goals translate THIS SPECIFIC strategy for this role
- Impact Score (0-100): Potential strategic contribution given role scope
- Coherence Score (0-100): How well the goal SET works together
- Strategy Coherence Score (0-100): Confidence that goals belong to this strategy context

Return ONLY valid JSON matching this structure:
{{
    "overallAlignmentScore": 75,
    "overallImpactScore": 68,
    "overallCoherenceScore": 72,
    "strategyCoherenceCheck": {{
        "confidenceScore": 85,
        "belongsToStrategy": true,
        "potentialMismatches": ["string - any identified mismatches between goals and strategy context"],
        "assessment": "Detailed assessment of whether these goals appear to be written for this specific organizational strategy, with evidence"
    }},
    "strategicTieBack": {{
        "visionAlignment": "How the goal set as a whole connects to: [quote the vision]",
        "missionContribution": "How goals support the mission: [quote the mission]",
        "valuesReflected": ["list which organizational values are reflected in the goals"],
        "strategicThemesCovered": ["list which strategic themes from the framework are addressed"],
        "strategicThemesGaps": ["list which strategic themes are NOT addressed by any goals"]
    }},
    "roleAppropriatenessAssessment": "string - assessment of whether goals are appropriate for this role/level",
    "goals": [
        {{
            "goalId": "G1",
            "goalText": "string",
            "alignmentScore": 82,
            "impactScore": 70,
            "alignedObjectives": ["F1", "P2"],
            "strategicTieBack": {{
                "visionConnection": "How this specific goal connects to the organizational vision",
                "missionSupport": "How this goal supports the stated mission",
                "strategicThemes": ["which strategic themes this goal addresses"],
                "objectiveMapping": "Explanation of why this maps to objectives F1, P2"
            }},
            "alignmentRationale": "Detailed explanation referencing SPECIFIC strategic content - quote vision/mission/themes",
            "impactRationale": "Assessment of potential strategic contribution given this employee's scope and influence",
            "roleAppropriateness": "Assessment of whether this goal is appropriate for the employee's level",
            "gaps": ["string"],
            "smartAssessment": {{
                "specific": true,
                "measurable": true,
                "achievable": true,
                "relevant": true,
                "timeBound": false,
                "notes": "string"
            }}
        }}
    ],
    "goalSetCoherence": {{
        "internalConsistency": "string - do goals support or conflict with each other?",
        "balancedCoverage": "string - are multiple strategic perspectives addressed?",
        "weightDistributionAssessment": "string - if weights provided, are they well-distributed?",
        "overallCoherenceNotes": "string - how well does this goal set work as a unified whole?"
    }},
    "strategicCoverage": {{
        "financial": {{ "covered": 2, "total": 3, "percentage": 67 }},
        "customer": {{ "covered": 1, "total": 4, "percentage": 25 }},
        "process": {{ "covered": 3, "total": 3, "percentage": 100 }},
        "learning": {{ "covered": 0, "total": 2, "percentage": 0 }}
    }},
    "recommendations": ["string - specific recommendations referencing the actual strategic content"]
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
