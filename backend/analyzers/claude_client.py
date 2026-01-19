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

    # Model tiers for cost/speed optimization
    SONNET_MODEL = "claude-sonnet-4-20250514"  # Best quality, higher cost
    HAIKU_MODEL = "claude-3-5-haiku-20241022"   # Fast, cheap, good quality
    DEFAULT_MODEL = SONNET_MODEL

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

    def _detect_strategy_scope(self, documents_text: str) -> Dict[str, Any]:
        """
        Detect if the strategy document is team/department-specific or organization-wide.

        Args:
            documents_text: Combined text from strategy documents

        Returns:
            Dict with is_team_specific (bool) and entity_name (str or None)
        """
        import re

        text_lower = documents_text.lower()

        # Common team/department indicators
        team_patterns = [
            # Explicit team/department strategy mentions
            r'([A-Za-z&\s]+(?:team|department|division|function|unit))\s+(?:strategy|strategic|goals|objectives)',
            r'(?:strategy|strategic|goals|objectives)\s+(?:for|of)\s+([A-Za-z&\s]+(?:team|department|division|function|unit))',
            # Department abbreviations with strategic context
            r'([A-Z]{2,6})\s+(?:strategic\s+)?goals',
            r'([A-Z]{2,6})\s+strategy',
            # Functional area strategies
            r'((?:HR|IT|Finance|Marketing|Sales|Operations|R&D|Engineering|Legal|OD|ODTM|L&D|Talent|People)[^a-z]*)\s*(?:strategic|strategy|goals)',
            # Team name patterns
            r'(OD\s*&?\s*Talent\s*Management|Talent\s*Management|Organisation(?:al)?\s*Development)',
            r'(Human\s*Resources?|People\s*(?:&\s*)?(?:Culture|Operations))',
        ]

        # Look for team/department indicators
        for pattern in team_patterns:
            matches = re.findall(pattern, documents_text, re.IGNORECASE)
            if matches:
                entity_name = matches[0].strip() if isinstance(matches[0], str) else matches[0]
                # Clean up the entity name
                entity_name = re.sub(r'\s+', ' ', entity_name).strip()
                if len(entity_name) > 2:
                    return {
                        'is_team_specific': True,
                        'entity_name': entity_name,
                        'scope': 'team' if 'team' in entity_name.lower() else 'department'
                    }

        # Check for functional keywords without explicit "company" or "corporate" context
        functional_keywords = [
            'talent management', 'talent development', 'talent acquisition',
            'organisational development', 'organizational development',
            'learning and development', 'l&d', 'employee engagement',
            'succession planning', 'performance management',
            'hr strategy', 'people strategy', 'workforce planning'
        ]

        # Check if document is heavily focused on a specific function
        keyword_matches = sum(1 for kw in functional_keywords if kw in text_lower)

        # If many functional keywords and no company-wide indicators, likely team-specific
        company_indicators = ['corporate strategy', 'company strategy', 'enterprise strategy',
                            'our vision', 'our mission', 'company-wide', 'organization-wide',
                            'annual report', 'investor', 'shareholder']
        has_company_context = any(ind in text_lower for ind in company_indicators)

        if keyword_matches >= 3 and not has_company_context:
            # Try to identify the function
            if any(kw in text_lower for kw in ['talent', 'od ', 'odtm', 'organisational development', 'organizational development']):
                return {
                    'is_team_specific': True,
                    'entity_name': 'OD & Talent Management',
                    'scope': 'department'
                }
            elif any(kw in text_lower for kw in ['hr ', 'human resource', 'people ']):
                return {
                    'is_team_specific': True,
                    'entity_name': 'Human Resources',
                    'scope': 'department'
                }

        return {
            'is_team_specific': False,
            'entity_name': None,
            'scope': 'organization'
        }

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
        # Detect if this is a team/department-specific strategy
        strategy_scope = self._detect_strategy_scope(documents_text)

        system_prompt = """You are an expert in strategic planning frameworks including
Balanced Scorecard, Strategy Maps, and OKRs. You analyze organizational and team strategy documents
and extract structured strategic frameworks. Always return valid JSON.

CRITICAL: If the document is a TEAM or DEPARTMENT strategy (not company-wide), you MUST:
1. Set strategyScope to "team" or "department"
2. Include the team/department name in scopeEntity
3. For vision/mission, extract the TEAM's purpose, NOT invent a company-wide vision
4. If no explicit team vision exists, state "Team purpose derived from strategic goals" and summarize their focus"""

        scope_context = ""
        if strategy_scope['is_team_specific']:
            scope_context = f"""
IMPORTANT CONTEXT: This appears to be a TEAM/DEPARTMENT strategy document for "{strategy_scope['entity_name']}".
- DO NOT invent or assume company-wide vision/mission statements
- Extract the team's strategic goals and objectives as stated
- The "vision" should reflect this team's purpose, not the parent organization
- If no explicit vision/mission is stated, derive it from the team's stated goals
"""

        prompt = f"""Analyze the following strategy documents and extract a coherent strategic framework.
{scope_context}
DOCUMENTS:
{documents_text}

OUTPUT REQUIREMENTS:
1. FIRST determine the scope: Is this a company-wide strategy OR a team/department strategy?
2. If TEAM/DEPARTMENT strategy:
   - Set strategyScope to "team" or "department"
   - Set scopeEntity to the team/department name (e.g., "OD & Talent Management", "HR", "Finance")
   - For vision: State the team's purpose based on their goals (do NOT invent company vision)
   - For mission: Describe what this team does based on the document
3. Extract strategic objectives into Balanced Scorecard perspectives:
   - Financial: Budget, cost efficiency, ROI objectives (if applicable to this team)
   - Customer: Internal stakeholders, service delivery objectives
   - Internal Process: Process improvement, delivery, operational objectives
   - Learning & Growth: Capabilities, development, engagement objectives
4. Identify strategic themes that connect objectives
5. Derive Key Performance Requirements

Return ONLY valid JSON matching this structure:
{{
    "strategyScope": "organization|department|team",
    "scopeEntity": "string - name of team/department if not organization-wide, otherwise null",
    "organizationalPurpose": {{
        "vision": "string - team/dept purpose if scoped, or org vision if company-wide",
        "mission": "string - what this entity does/delivers",
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
        employee_context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze alignment between goals and strategic framework.

        Args:
            strategic_framework: Structured strategic framework from analyze_strategy
            goal_document_text: Text content of goal document
            employee_context: Optional employee metadata (job title, seniority, department, goals with weights)
            model: Optional model override (defaults to SONNET for senior, HAIKU for others)

        Returns:
            Alignment analysis with scores and recommendations
        """
        import json

        system_prompt = """You are an expert in performance management and strategy execution.
Analyze employee goals against organizational strategy. Reference specific vision, mission, and objectives.
Always return valid JSON."""

        # Extract key strategic elements
        org_purpose = strategic_framework.get('organizationalPurpose', {})
        vision = org_purpose.get('vision', 'Not specified')
        mission = org_purpose.get('mission', 'Not specified')
        values = org_purpose.get('values', [])
        themes = [t.get('name', '') for t in strategic_framework.get('strategicThemes', []) if t.get('name')]

        # Build compact strategic summary
        strategic_ref = f"""STRATEGIC REFERENCE:
- VISION: "{vision}"
- MISSION: "{mission}"
- VALUES: {', '.join(values) if values else 'N/A'}
- THEMES: {', '.join(themes) if themes else 'N/A'}"""

        # Build employee context
        emp_section = ""
        if employee_context:
            emp_section = f"""
EMPLOYEE: {employee_context.get('employeeName', 'Unknown')} | {employee_context.get('jobTitle', 'N/A')} | {employee_context.get('department', 'N/A')} | {employee_context.get('seniorityLevel', 'N/A')}"""
            goals_with_weights = employee_context.get('goalsWithWeights', [])
            if goals_with_weights:
                emp_section += "\nGOAL WEIGHTS: " + "; ".join([f"{gw.get('goalText', '')[:60]}({gw.get('weight', 'N/A')})" for gw in goals_with_weights[:5]])

        # Compact objectives summary (avoid sending full framework JSON when possible)
        objectives_summary = []
        for perspective in ['financial', 'customer', 'internalProcess', 'learningGrowth']:
            objs = strategic_framework.get('strategicPerspectives', {}).get(perspective, {}).get('objectives', [])
            for obj in objs[:4]:  # Limit to 4 per perspective
                objectives_summary.append(f"{obj.get('id', '?')}: {obj.get('objective', '')[:80]}")

        prompt = f"""Analyze goal alignment with strategic framework.

{strategic_ref}

STRATEGIC OBJECTIVES:
{chr(10).join(objectives_summary)}
{emp_section}

GOALS TO ANALYZE:
{goal_document_text}

SCORING (0-100):
- Alignment: 40% objective mapping, 30% vision/mission, 20% theme alignment, 10% role fit
- Impact: Scope of influence and strategic leverage
- Coherence: Internal consistency and balanced coverage

Return JSON:
{{
    "overallAlignmentScore": 75,
    "overallImpactScore": 68,
    "overallCoherenceScore": 72,
    "strategyCoherenceCheck": {{
        "confidenceScore": 85,
        "belongsToStrategy": true,
        "potentialMismatches": [],
        "assessment": "Assessment of goal-strategy fit"
    }},
    "strategicTieBack": {{
        "visionAlignment": "How goals connect to vision",
        "missionContribution": "How goals support mission",
        "valuesReflected": [],
        "strategicThemesCovered": [],
        "strategicThemesGaps": []
    }},
    "roleAppropriatenessAssessment": "Assessment",
    "goals": [
        {{
            "goalId": "G1",
            "goalText": "Goal text",
            "alignmentScore": 82,
            "alignmentScoreBreakdown": {{
                "objectiveMappingScore": 85,
                "objectiveMappingRationale": "Rationale",
                "visionMissionScore": 80,
                "visionMissionRationale": "Rationale",
                "themeAlignmentScore": 75,
                "themeAlignmentRationale": "Rationale",
                "roleAppropriatenessScore": 90,
                "roleAppropriatenessRationale": "Rationale"
            }},
            "impactScore": 70,
            "alignedObjectives": ["F1", "P2"],
            "strategicTieBack": {{
                "visionConnection": "Connection",
                "missionSupport": "Support",
                "strategicThemes": [],
                "objectiveMapping": "Mapping"
            }},
            "alignmentRationale": "Detailed rationale",
            "impactRationale": "Impact assessment",
            "roleAppropriateness": "Role fit assessment",
            "gaps": [],
            "smartAssessment": {{
                "specific": true,
                "measurable": true,
                "achievable": true,
                "relevant": true,
                "timeBound": false,
                "notes": ""
            }}
        }}
    ],
    "goalSetCoherence": {{
        "internalConsistency": "Assessment",
        "balancedCoverage": "Assessment",
        "weightDistributionAssessment": "Assessment",
        "overallCoherenceNotes": "Notes"
    }},
    "strategicCoverage": {{
        "financial": {{ "covered": 2, "total": 3, "percentage": 67 }},
        "customer": {{ "covered": 1, "total": 4, "percentage": 25 }},
        "process": {{ "covered": 3, "total": 3, "percentage": 100 }},
        "learning": {{ "covered": 0, "total": 2, "percentage": 0 }}
    }},
    "recommendations": []
}}"""

        # Use specified model or default
        response = self.complete(prompt, system_prompt=system_prompt, model=model, max_tokens=6144)

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
        Generate improved goal recommendations specific to the employee's role.

        Args:
            strategic_framework: Structured strategic framework
            current_goals: Current goal document text
            alignment_analysis: Results from alignment analysis (includes employeeContext)

        Returns:
            Recommendations for improved goals with original goal references
        """
        import json

        # Extract employee context for role-appropriate recommendations
        employee_context = alignment_analysis.get('employeeContext', {})
        employee_name = employee_context.get('employeeName', 'Unknown')
        job_title = employee_context.get('jobTitle', 'Not specified')
        department = employee_context.get('department', 'Not specified')
        seniority = employee_context.get('seniorityLevel', 'Not specified')

        # Extract existing goals for reference
        existing_goals = alignment_analysis.get('goals', [])
        goals_summary = []
        for i, goal in enumerate(existing_goals[:7], 1):
            goal_text = goal.get('goalText', '')[:150]
            alignment = goal.get('alignmentScore', 0)
            gaps = goal.get('gaps', [])
            goals_summary.append(f"G{i}: \"{goal_text}\" (Alignment:{alignment}, Gaps: {', '.join(gaps[:2]) if gaps else 'None'})")

        # Compact strategic summary
        org_purpose = strategic_framework.get('organizationalPurpose', {})
        vision = org_purpose.get('vision', 'N/A')[:150]
        mission = org_purpose.get('mission', 'N/A')[:150]

        system_prompt = f"""You are an expert in performance management for the {department} department.
You generate improved performance goals that are SPECIFIC to the employee's role and department.
CRITICAL: Each recommendation MUST revise one of the employee's EXISTING goals - do NOT suggest unrelated goals.
Goals for a {job_title} in {department} should be relevant to their actual work responsibilities.
Always return valid JSON."""

        prompt = f"""Generate up to 5 revised goals for this SPECIFIC employee to improve strategic alignment.

EMPLOYEE (recommendations must be appropriate for this role):
- Name: {employee_name}
- Job Title: {job_title}
- Department: {department}
- Seniority: {seniority}

EMPLOYEE'S CURRENT GOALS (each recommendation MUST revise one of these):
{chr(10).join(goals_summary)}

STRATEGIC CONTEXT:
- Vision: {vision}
- Mission: {mission}
- Current Alignment: {alignment_analysis.get('overallAlignmentScore', 0)}/100
- Current Impact: {alignment_analysis.get('overallImpactScore', 0)}/100

CRITICAL CONSTRAINTS:
1. ONLY revise the employee's existing goals listed above
2. Recommendations MUST be appropriate for {job_title} in {department}
3. Do NOT suggest goals outside the employee's department scope
4. Reference the original goal being revised in each recommendation

Return JSON:
{{
    "recommendations": [
        {{
            "recommendationId": "R1",
            "originalGoalId": "G1",
            "originalGoal": "Copy the exact original goal text here",
            "revisedGoal": {{
                "objective": "Improved goal statement for {job_title}",
                "keyResults": ["KR1", "KR2", "KR3"],
                "timeline": "FY2025",
                "metrics": ["Metric1", "Metric2"]
            }},
            "strategicLinkages": ["F1", "C2"],
            "predictedAlignmentGain": 8,
            "evidence": {{
                "source": "Gap analysis",
                "finding": "Why this revision improves alignment"
            }},
            "implementationNotes": "Guidance for {job_title} in {department}"
        }}
    ],
    "projectedNewAlignmentScore": 85,
    "projectedNewImpactScore": 80
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

    def generate_portfolio_recommendations(
        self,
        strategic_framework: Dict[str, Any],
        all_analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate portfolio-wide recommendations synthesizing themes across all employees.

        Args:
            strategic_framework: Structured strategic framework
            all_analyses: List of all employee goal analyses

        Returns:
            Executive summary with key themes and systemic recommendations
        """
        import json

        system_prompt = """You are a strategic OE (Organizational Effectiveness) consultant specializing in
performance management and goal alignment. You analyze patterns across multiple employees' goals
to identify systemic themes, gaps, and opportunities for organizational improvement.
Your recommendations are executive-level, actionable, and grounded in the strategic framework.
Always return valid JSON."""

        # Summarize analyses for the prompt
        analyses_summary = []
        for analysis in all_analyses:
            analyses_summary.append({
                "employee": analysis.get("documentName", "Unknown"),
                "role": analysis.get("employeeContext", {}).get("role", ""),
                "alignmentScore": analysis.get("overallAlignmentScore", 0),
                "impactScore": analysis.get("overallImpactScore", 0),
                "quadrantDistribution": analysis.get("coherenceIndex", {}).get("quadrantDistribution", {}),
                "gaps": analysis.get("strategicCoverage", {}),
                "topGoals": [g.get("goal", "")[:100] for g in analysis.get("goals", [])[:3]]
            })

        prompt = f"""Analyze this portfolio of {len(all_analyses)} employees' goals and generate an executive summary
with key themes and strategic recommendations for organizational improvement.

STRATEGIC FRAMEWORK:
{json.dumps(strategic_framework, indent=2)}

EMPLOYEE ANALYSES SUMMARY:
{json.dumps(analyses_summary, indent=2)}

Provide:
1. EXECUTIVE SUMMARY: 2-3 paragraph synthesis of the portfolio's strategic health
2. KEY THEMES: 3-5 patterns observed across employees (both positive and concerning)
3. STRATEGIC GAPS: Top 3-5 organizational blind spots where goals don't address strategy
4. SYSTEMIC RECOMMENDATIONS: 4-6 organization-wide changes to improve goal quality
5. PRIORITY ACTIONS: Top 3 immediate actions for leadership

Return ONLY valid JSON matching this structure:
{{
    "executiveSummary": {{
        "overallHealth": "string - one sentence verdict",
        "narrative": "string - 2-3 paragraph detailed summary",
        "portfolioScore": number (0-100)
    }},
    "keyThemes": [
        {{
            "themeId": "T1",
            "title": "string",
            "description": "string",
            "frequency": "string - e.g., '75% of employees'",
            "impact": "positive" | "neutral" | "negative",
            "affectedPerspectives": ["financial", "customer", "process", "learning"]
        }}
    ],
    "strategicGaps": [
        {{
            "gapId": "G1",
            "title": "string",
            "description": "string",
            "affectedObjectives": ["F1", "C2"],
            "severity": "critical" | "moderate" | "minor",
            "businessRisk": "string"
        }}
    ],
    "systemicRecommendations": [
        {{
            "recommendationId": "SR1",
            "title": "string",
            "description": "string",
            "rationale": "string",
            "targetAudience": "string - e.g., 'All managers', 'HR/Talent team'",
            "expectedOutcome": "string",
            "linkedGaps": ["G1", "G2"]
        }}
    ],
    "priorityActions": [
        {{
            "actionId": "A1",
            "action": "string",
            "owner": "string - suggested owner role",
            "timeframe": "string - e.g., 'Next 30 days'",
            "expectedImpact": "string"
        }}
    ],
    "metadata": {{
        "employeesAnalyzed": number,
        "averageAlignmentScore": number,
        "averageImpactScore": number,
        "generatedAt": "ISO timestamp"
    }}
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

            result = json.loads(content.strip())

            # Add metadata if not present
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"]["employeesAnalyzed"] = len(all_analyses)
            result["metadata"]["averageAlignmentScore"] = round(
                sum(a.get("overallAlignmentScore", 0) for a in all_analyses) / max(len(all_analyses), 1), 1
            )
            result["metadata"]["averageImpactScore"] = round(
                sum(a.get("overallImpactScore", 0) for a in all_analyses) / max(len(all_analyses), 1), 1
            )

            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse portfolio recommendations as JSON: {str(e)}")

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
