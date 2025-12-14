"""
Goal Recommendation Engine
Generates revised performance goals grounded in emerging practices.
"""

import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .claude_client import ClaudeClient


@dataclass
class RevisedGoal:
    """Structure for a revised goal recommendation."""
    objective: str
    keyResults: List[str]
    timeline: str
    metrics: List[str]


@dataclass
class Evidence:
    """Evidence supporting a recommendation."""
    source: str
    finding: str
    url: Optional[str] = None


@dataclass
class GoalRecommendation:
    """A single goal recommendation."""
    recommendationId: str
    revisedGoal: RevisedGoal
    strategicLinkages: List[str]
    predictedAlignmentGain: int
    evidence: Evidence
    implementationNotes: str


class GoalRecommendationEngine:
    """
    Generates improved performance goals based on strategic framework
    and alignment analysis. Uses Claude API with evidence-based reasoning.
    """

    RECOMMENDATIONS_COUNT = 5

    def __init__(
        self,
        claude_client: Optional[ClaudeClient] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the recommendation engine.

        Args:
            claude_client: Pre-configured Claude client (for testing)
            api_key: API key for Claude
        """
        if claude_client:
            self.client = claude_client
        elif api_key:
            self.client = ClaudeClient(api_key=api_key)
        else:
            self.client = ClaudeClient()

    def generate_recommendations(
        self,
        strategic_framework: Dict[str, Any],
        goal_document: Dict[str, Any],
        alignment_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate goal recommendations for a document.

        Args:
            strategic_framework: Strategic framework from StrategySynthesizer
            goal_document: Processed goal document with analysis
            alignment_analysis: Optional alignment analysis results

        Returns:
            Recommendations with projected improvements
        """
        document_text = goal_document.get('extractedText', '')
        current_score = goal_document.get('overallAlignmentScore', 50)

        if alignment_analysis is None:
            alignment_analysis = {
                'overallAlignmentScore': current_score,
                'overallImpactScore': goal_document.get('overallImpactScore', 50),
                'goals': goal_document.get('goals', []),
                'strategicCoverage': goal_document.get('strategicCoverage', {}),
                'recommendations': []
            }

        # Generate recommendations using Claude
        raw_recommendations = self.client.generate_recommendations(
            strategic_framework,
            document_text,
            alignment_analysis
        )

        # Validate and enhance recommendations
        recommendations = self._validate_recommendations(raw_recommendations)

        # Add metadata
        recommendations['documentId'] = goal_document.get('documentId', str(uuid.uuid4()))
        recommendations['metadata'] = {
            'generationTimestamp': datetime.utcnow().isoformat() + 'Z',
            'currentAlignmentScore': current_score,
            'recommendationCount': len(recommendations.get('recommendations', []))
        }

        return recommendations

    def _validate_recommendations(self, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and ensure recommendations have required structure.

        Args:
            recommendations: Raw recommendations from Claude

        Returns:
            Validated recommendations
        """
        # Ensure recommendations array
        if 'recommendations' not in recommendations:
            recommendations['recommendations'] = []

        for i, rec in enumerate(recommendations['recommendations']):
            if 'recommendationId' not in rec:
                rec['recommendationId'] = f"R{i+1}"

            # Ensure revised goal structure
            if 'revisedGoal' not in rec:
                rec['revisedGoal'] = {}

            goal = rec['revisedGoal']
            goal['objective'] = goal.get('objective', '')
            goal['keyResults'] = goal.get('keyResults', [])
            goal['timeline'] = goal.get('timeline', 'Q4 2025')
            goal['metrics'] = goal.get('metrics', [])

            # Ensure other fields
            rec['strategicLinkages'] = rec.get('strategicLinkages', [])
            rec['predictedAlignmentGain'] = self._clamp_gain(rec.get('predictedAlignmentGain', 10))

            # Ensure evidence
            if 'evidence' not in rec:
                rec['evidence'] = {}
            rec['evidence']['source'] = rec['evidence'].get('source', 'Best practices')
            rec['evidence']['finding'] = rec['evidence'].get('finding', '')

            rec['implementationNotes'] = rec.get('implementationNotes', '')

        # Ensure projected scores
        recommendations['projectedNewAlignmentScore'] = self._clamp_score(
            recommendations.get('projectedNewAlignmentScore', 75)
        )
        recommendations['projectedNewImpactScore'] = self._clamp_score(
            recommendations.get('projectedNewImpactScore', 70)
        )

        return recommendations

    def _clamp_score(self, score: int) -> int:
        """Clamp score to 0-100 range."""
        try:
            return max(0, min(100, int(score)))
        except (TypeError, ValueError):
            return 50

    def _clamp_gain(self, gain: int) -> int:
        """Clamp gain to reasonable range (0-50)."""
        try:
            return max(0, min(50, int(gain)))
        except (TypeError, ValueError):
            return 10

    def generate_batch_recommendations(
        self,
        strategic_framework: Dict[str, Any],
        analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for multiple documents.

        Args:
            strategic_framework: Strategic framework
            analyses: List of alignment analysis results

        Returns:
            List of recommendation sets
        """
        results = []
        for analysis in analyses:
            try:
                recommendations = self.generate_recommendations(
                    strategic_framework,
                    analysis,
                    analysis
                )
                results.append(recommendations)
            except Exception as e:
                results.append({
                    'documentId': analysis.get('documentId', str(uuid.uuid4())),
                    'error': str(e),
                    'recommendations': []
                })

        return results

    def prioritize_recommendations(
        self,
        recommendations: Dict[str, Any],
        framework: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Prioritize recommendations based on strategic importance.

        Args:
            recommendations: Generated recommendations
            framework: Strategic framework

        Returns:
            Sorted list of recommendations
        """
        recs = recommendations.get('recommendations', [])
        if not recs:
            return []

        # Get critical KPR objectives
        critical_objectives = set()
        for kpr in framework.get('keyPerformanceRequirements', []):
            if kpr.get('priority') == 'critical':
                critical_objectives.update(kpr.get('linkedObjectiveIds', []))

        # Score each recommendation
        def score_rec(rec):
            score = rec.get('predictedAlignmentGain', 0)
            # Bonus for linking to critical objectives
            for linkage in rec.get('strategicLinkages', []):
                if linkage in critical_objectives:
                    score += 10
            return score

        sorted_recs = sorted(recs, key=score_rec, reverse=True)
        return sorted_recs

    def get_coverage_improvement(
        self,
        current_coverage: Dict[str, Dict[str, Any]],
        recommendations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate expected coverage improvement from recommendations.

        Args:
            current_coverage: Current strategic coverage
            recommendations: Generated recommendations

        Returns:
            Coverage improvement analysis
        """
        # Collect new objective coverage from recommendations
        new_covered = set()
        for rec in recommendations.get('recommendations', []):
            new_covered.update(rec.get('strategicLinkages', []))

        # Map objectives to perspectives
        perspective_map = {
            'F': 'financial',
            'C': 'customer',
            'P': 'process',
            'I': 'process',
            'L': 'learning'
        }

        improvements = {}
        for perspective in ['financial', 'customer', 'process', 'learning']:
            current = current_coverage.get(perspective, {})
            current_pct = current.get('percentage', 0)
            total = current.get('total', 0)

            # Count new coverage for this perspective
            prefix = perspective[0].upper()
            if perspective == 'process':
                new_for_perspective = sum(
                    1 for obj_id in new_covered
                    if obj_id[0] in ['P', 'I']
                )
            else:
                new_for_perspective = sum(
                    1 for obj_id in new_covered
                    if obj_id[0] == prefix
                )

            # Calculate projected percentage
            if total > 0:
                projected_covered = min(total, current.get('covered', 0) + new_for_perspective)
                projected_pct = (projected_covered / total) * 100
            else:
                projected_pct = current_pct

            improvements[perspective] = {
                'current': round(current_pct, 1),
                'projected': round(projected_pct, 1),
                'improvement': round(projected_pct - current_pct, 1)
            }

        return improvements


class MockRecommendationClient:
    """
    Mock client for testing recommendation generation without API calls.
    Generates contextual recommendations based on actual employee goals.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "mock-key"

    def generate_recommendations(
        self,
        strategic_framework: Dict[str, Any],
        current_goals: str,
        alignment_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate contextual recommendations based on actual employee goals."""
        current_score = alignment_analysis.get('overallAlignmentScore', 50)
        current_impact = alignment_analysis.get('overallImpactScore', 50)
        goals = alignment_analysis.get('goals', [])
        employee_context = alignment_analysis.get('employeeContext', {})

        # Extract strategic objectives from framework
        objectives = strategic_framework.get('strategicObjectives', [])
        obj_map = {obj.get('objectiveId', ''): obj for obj in objectives}

        # Identify goals needing improvement (Distraction, Busy Work Trap, Rogue Project)
        goals_to_improve = []
        for goal in goals:
            quadrant = goal.get('classification', {}).get('quadrant', '')
            if quadrant in ['Distraction', 'Busy Work Trap', 'Rogue Project']:
                goals_to_improve.append(goal)

        # If no weak goals, use all goals sorted by alignment score
        if not goals_to_improve:
            goals_to_improve = sorted(
                goals,
                key=lambda g: g.get('alignmentScore', 0)
            )[:5]

        # Generate contextual recommendations
        recommendations = []
        for i, goal in enumerate(goals_to_improve[:5]):
            rec = self._create_contextual_recommendation(
                goal, i + 1, strategic_framework, employee_context
            )
            recommendations.append(rec)

        # Calculate projected improvement
        improvement_per_rec = 5 if recommendations else 0
        projected_alignment = min(100, current_score + (len(recommendations) * improvement_per_rec))
        projected_impact = min(100, current_impact + (len(recommendations) * 4))

        return {
            "recommendations": recommendations,
            "projectedNewAlignmentScore": projected_alignment,
            "projectedNewImpactScore": projected_impact
        }

    def _create_contextual_recommendation(
        self,
        goal: Dict[str, Any],
        index: int,
        framework: Dict[str, Any],
        employee_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a contextual recommendation for a specific goal."""
        goal_text = goal.get('goalText', '')
        quadrant = goal.get('classification', {}).get('quadrant', 'Distraction')
        linked_objectives = goal.get('linkedStrategicObjectives', [])
        alignment_score = goal.get('alignmentScore', 0)

        job_title = employee_context.get('jobTitle', '')
        seniority = employee_context.get('seniorityLevel', 'mid-level')
        department = employee_context.get('department', '')

        # Get strategic objectives from framework
        objectives = framework.get('strategicObjectives', [])
        obj_by_perspective = {'F': [], 'C': [], 'P': [], 'I': [], 'L': []}
        for obj in objectives:
            obj_id = obj.get('objectiveId', '')
            if obj_id and obj_id[0] in obj_by_perspective:
                obj_by_perspective[obj_id[0]].append(obj)

        # Determine what type of improvement is needed
        is_outcome = goal.get('classification', {}).get('isOutcome', False)
        is_aligned = goal.get('classification', {}).get('isAligned', False)

        # Generate revised goal based on the original and what's missing
        revised = self._generate_revised_goal(
            goal_text, quadrant, is_outcome, is_aligned,
            linked_objectives, objectives, job_title, seniority
        )

        # Suggest strategic linkages based on what's available
        suggested_linkages = self._suggest_linkages(
            goal_text, objectives, linked_objectives
        )

        # Calculate predicted gain based on current state
        base_gain = {
            'Distraction': 25,
            'Busy Work Trap': 15,
            'Rogue Project': 20,
            'Strategic Driver': 5
        }.get(quadrant, 10)

        # Generate contextual evidence
        evidence = self._generate_evidence(goal_text, quadrant, job_title)

        # Generate implementation notes
        impl_notes = self._generate_implementation_notes(
            quadrant, is_outcome, is_aligned, job_title, department
        )

        return {
            "recommendationId": f"R{index}",
            "originalGoal": goal_text[:200] + ('...' if len(goal_text) > 200 else ''),
            "originalClassification": quadrant,
            "revisedGoal": revised,
            "strategicLinkages": suggested_linkages,
            "predictedAlignmentGain": base_gain,
            "evidence": evidence,
            "implementationNotes": impl_notes
        }

    def _generate_revised_goal(
        self,
        original: str,
        quadrant: str,
        is_outcome: bool,
        is_aligned: bool,
        linked_objectives: List[str],
        all_objectives: List[Dict],
        job_title: str,
        seniority: str
    ) -> Dict[str, Any]:
        """Generate a revised goal based on the original and improvement needs."""
        # Extract key theme from original goal
        original_lower = original.lower()

        # Identify the topic area
        topic_keywords = {
            'customer': ['customer', 'client', 'service', 'satisfaction', 'nps', 'support'],
            'process': ['process', 'efficiency', 'operation', 'workflow', 'procedure', 'system'],
            'financial': ['cost', 'revenue', 'budget', 'profit', 'margin', 'savings'],
            'people': ['team', 'training', 'development', 'skill', 'capability', 'talent'],
            'quality': ['quality', 'compliance', 'standard', 'audit', 'accuracy'],
            'innovation': ['improve', 'new', 'innovation', 'digital', 'technology', 'transform']
        }

        detected_topic = 'process'  # default
        for topic, keywords in topic_keywords.items():
            if any(kw in original_lower for kw in keywords):
                detected_topic = topic
                break

        # Build contextual revised goal
        # New seniority categories: individual contributor, team leader, senior management
        role_context = f" as {job_title}" if job_title else ""
        seniority_verb = 'Lead' if seniority in ['senior management', 'team leader', 'senior', 'executive', 'director'] else 'Drive'

        # Create objective based on quadrant issues
        if quadrant == 'Distraction':
            # Needs both alignment and outcomes
            objective = self._create_aligned_outcome_goal(original, detected_topic, seniority_verb, all_objectives)
            key_results = self._create_measurable_key_results(detected_topic, seniority)
        elif quadrant == 'Busy Work Trap':
            # Has alignment but needs outcomes
            objective = self._convert_activity_to_outcome(original, detected_topic, seniority_verb)
            key_results = self._create_measurable_key_results(detected_topic, seniority)
        elif quadrant == 'Rogue Project':
            # Has outcomes but needs alignment
            objective = self._add_strategic_alignment(original, all_objectives, detected_topic)
            key_results = self._preserve_outcomes_add_alignment(original, detected_topic)
        else:
            # Strategic Driver - minor enhancements
            objective = original[:150] if len(original) <= 150 else original[:147] + '...'
            key_results = self._create_measurable_key_results(detected_topic, seniority)

        return {
            "objective": objective,
            "keyResults": key_results,
            "timeline": "Q2 2025" if seniority in ['senior management', 'team leader', 'senior', 'executive'] else "Q3 2025",
            "metrics": self._suggest_metrics(detected_topic)
        }

    def _create_aligned_outcome_goal(
        self,
        original: str,
        topic: str,
        verb: str,
        objectives: List[Dict]
    ) -> str:
        """Create a goal with both strategic alignment and measurable outcomes."""
        topic_goals = {
            'customer': f"{verb} customer experience improvement initiative resulting in measurable satisfaction gains",
            'process': f"{verb} operational excellence program to achieve quantified efficiency improvements",
            'financial': f"{verb} cost optimization initiative with defined savings targets and ROI metrics",
            'people': f"{verb} team capability development program with measurable skill advancement outcomes",
            'quality': f"{verb} quality improvement initiative with specific compliance and accuracy targets",
            'innovation': f"{verb} digital transformation project delivering measurable business value"
        }

        # Try to preserve original intent
        words = original.split()[:5]
        original_hint = ' '.join(words) if words else ''

        base_goal = topic_goals.get(topic, topic_goals['process'])

        # If original has specific context, incorporate it
        if original_hint and len(original_hint) > 10:
            return f"{base_goal}, building on '{original_hint}...'"

        return base_goal

    def _convert_activity_to_outcome(self, original: str, topic: str, verb: str) -> str:
        """Convert an activity-based goal to outcome-oriented."""
        # Replace activity words with outcome words
        activity_to_outcome = {
            'implement': 'achieve measurable results through',
            'conduct': 'deliver quantified improvements via',
            'perform': 'produce measurable outcomes by',
            'complete': 'deliver business value through',
            'attend': 'apply learnings from',
            'participate': 'contribute measurable impact through'
        }

        result = original
        for activity, outcome in activity_to_outcome.items():
            if activity in original.lower():
                result = original.lower().replace(activity, outcome)
                result = result.capitalize()
                break

        # If no change made, prefix with outcome orientation
        if result == original:
            result = f"{verb} measurable improvement in {original.lower()[:100]}"

        return result[:200]

    def _add_strategic_alignment(
        self,
        original: str,
        objectives: List[Dict],
        topic: str
    ) -> str:
        """Add strategic alignment to an outcome-oriented goal."""
        # Find relevant objective
        perspective_map = {
            'customer': 'C',
            'financial': 'F',
            'process': 'P',
            'people': 'L',
            'quality': 'P',
            'innovation': 'P'
        }
        target_prefix = perspective_map.get(topic, 'P')

        relevant_obj = None
        for obj in objectives:
            if obj.get('objectiveId', '').startswith(target_prefix):
                relevant_obj = obj
                break

        if relevant_obj:
            obj_desc = relevant_obj.get('description', '')[:50]
            return f"Contribute to '{obj_desc}' by {original.lower()[:120]}"

        return f"Align to organizational strategy by {original.lower()[:150]}"

    def _preserve_outcomes_add_alignment(self, original: str, topic: str) -> List[str]:
        """Preserve outcome nature but add strategic connection."""
        return [
            f"Achieve measurable progress on original goal: {original[:80]}...",
            "Document and report strategic contribution quarterly",
            "Collaborate with stakeholders to validate strategic impact"
        ]

    def _create_measurable_key_results(self, topic: str, seniority: str) -> List[str]:
        """Create measurable key results based on topic and seniority."""
        topic_krs = {
            'customer': [
                "Improve customer satisfaction score by 10+ points",
                "Reduce customer complaint rate by 20%",
                "Achieve 90%+ positive feedback rating"
            ],
            'process': [
                "Reduce process cycle time by 25%",
                "Achieve 95%+ process compliance rate",
                "Eliminate 3 manual process steps through automation"
            ],
            'financial': [
                "Deliver 15% cost reduction in target area",
                "Achieve ROI of 3:1 or better",
                "Stay within 5% of approved budget"
            ],
            'people': [
                "Complete targeted skill development for 80% of team",
                "Achieve 90%+ training satisfaction scores",
                "Demonstrate measurable capability improvement via assessment"
            ],
            'quality': [
                "Achieve 98%+ accuracy rate on deliverables",
                "Zero critical compliance findings",
                "Pass all scheduled audits on first attempt"
            ],
            'innovation': [
                "Launch pilot within committed timeline",
                "Achieve 20% improvement in target metric",
                "Document lessons learned and best practices"
            ]
        }

        return topic_krs.get(topic, topic_krs['process'])

    def _suggest_linkages(
        self,
        goal_text: str,
        objectives: List[Dict],
        existing_linkages: List[str]
    ) -> List[str]:
        """Suggest strategic objective linkages based on goal content."""
        goal_lower = goal_text.lower()
        suggested = []

        # Map keywords to perspectives
        keyword_perspective = {
            'F': ['cost', 'revenue', 'profit', 'margin', 'budget', 'financial', 'savings'],
            'C': ['customer', 'client', 'satisfaction', 'service', 'nps', 'retention'],
            'P': ['process', 'efficiency', 'operation', 'quality', 'compliance', 'delivery'],
            'I': ['innovation', 'digital', 'technology', 'new', 'transform', 'improve'],
            'L': ['team', 'training', 'skill', 'development', 'capability', 'learning']
        }

        matched_perspectives = set()
        for perspective, keywords in keyword_perspective.items():
            if any(kw in goal_lower for kw in keywords):
                matched_perspectives.add(perspective)

        # Add at least one from each matched perspective
        for obj in objectives:
            obj_id = obj.get('objectiveId', '')
            if obj_id and obj_id[0] in matched_perspectives:
                if obj_id not in suggested:
                    suggested.append(obj_id)
                    if len(suggested) >= 3:
                        break

        # If nothing matched, suggest first from each main perspective
        if not suggested:
            for obj in objectives[:4]:
                obj_id = obj.get('objectiveId', '')
                if obj_id:
                    suggested.append(obj_id)

        return suggested[:3]

    def _suggest_metrics(self, topic: str) -> List[str]:
        """Suggest metrics based on goal topic."""
        topic_metrics = {
            'customer': ['NPS score', 'Customer satisfaction rating', 'Response time'],
            'process': ['Cycle time', 'Throughput', 'Error rate'],
            'financial': ['Cost savings', 'ROI', 'Budget variance'],
            'people': ['Training completion', 'Skill assessment scores', 'Engagement rating'],
            'quality': ['Accuracy rate', 'Compliance score', 'Defect rate'],
            'innovation': ['Adoption rate', 'Time to value', 'User satisfaction']
        }
        return topic_metrics.get(topic, ['Progress %', 'Completion rate', 'Quality score'])

    def _generate_evidence(
        self,
        goal_text: str,
        quadrant: str,
        job_title: str
    ) -> Dict[str, str]:
        """Generate contextual evidence for the recommendation."""
        quadrant_evidence = {
            'Distraction': {
                'source': 'Performance Management Research - Harvard Business Review',
                'finding': 'Goals lacking both strategic alignment and measurable outcomes have <20% completion rates and minimal organizational impact'
            },
            'Busy Work Trap': {
                'source': 'OKR Implementation Studies - Measure What Matters',
                'finding': 'Converting activity-based goals to outcome-oriented objectives increases achievement rates by 30-40%'
            },
            'Rogue Project': {
                'source': 'Strategic Alignment Research - MIT Sloan Management Review',
                'finding': 'High-quality individual work without strategic connection captures only 40% of potential organizational value'
            },
            'Strategic Driver': {
                'source': 'High-Performance Organization Studies',
                'finding': 'Well-aligned outcome goals with clear metrics achieve 85%+ completion rates'
            }
        }
        return quadrant_evidence.get(quadrant, quadrant_evidence['Distraction'])

    def _generate_implementation_notes(
        self,
        quadrant: str,
        is_outcome: bool,
        is_aligned: bool,
        job_title: str,
        department: str
    ) -> str:
        """Generate contextual implementation notes."""
        notes = []

        if not is_aligned:
            notes.append("Review strategic framework with manager to identify strongest objective linkages")

        if not is_outcome:
            notes.append("Reframe using 'achieve/deliver/improve' language with specific quantifiable targets")

        if quadrant == 'Distraction':
            notes.append("Consider whether this goal should be deprioritized or eliminated entirely")

        if job_title:
            notes.append(f"Leverage {job_title} responsibilities to demonstrate strategic impact")

        if department:
            notes.append(f"Coordinate with {department} leadership on priority alignment")

        if not notes:
            notes.append("Continue strong alignment practices and consider stretch targets")

        return '. '.join(notes)

    def generate_portfolio_recommendations(
        self,
        strategic_framework: Dict[str, Any],
        all_analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Return mock portfolio recommendations."""
        from datetime import datetime

        avg_alignment = sum(a.get('overallAlignmentScore', 50) for a in all_analyses) / max(len(all_analyses), 1)
        avg_impact = sum(a.get('overallImpactScore', 50) for a in all_analyses) / max(len(all_analyses), 1)

        return {
            "executiveSummary": {
                "overallHealth": f"Moderate strategic alignment with execution gaps across {len(all_analyses)} employees",
                "narrative": f"""The portfolio analysis reveals a mixed picture of strategic alignment across the organization.
While {len(all_analyses)} employees demonstrate understanding of operational objectives, there are significant gaps in
connecting individual goals to the broader strategic framework. Approximately 60% of goals focus on internal process
improvements, while customer-facing and financial objectives remain underrepresented.

The most concerning pattern is the prevalence of activity-based goals rather than outcome-oriented objectives. Many employees
have set goals around completing tasks or attending training rather than achieving measurable business results. This creates
a "busy work trap" where effort is expended without strategic impact.

Positively, there is strong alignment in operational efficiency initiatives, with multiple employees targeting process
improvements that support the organization's cost reduction objectives. However, innovation and customer experience goals
are notably absent from most individual goal sets.""",
                "portfolioScore": round(avg_alignment * 0.6 + avg_impact * 0.4)
            },
            "keyThemes": [
                {
                    "themeId": "T1",
                    "title": "Process-Heavy Goal Distribution",
                    "description": "Goals disproportionately focus on internal processes over customer outcomes and financial results",
                    "frequency": "75% of employees",
                    "impact": "negative",
                    "affectedPerspectives": ["customer", "financial"]
                },
                {
                    "themeId": "T2",
                    "title": "Strong Operational Efficiency Focus",
                    "description": "Consistent emphasis on cost reduction and process improvement across teams",
                    "frequency": "80% of employees",
                    "impact": "positive",
                    "affectedPerspectives": ["process", "financial"]
                },
                {
                    "themeId": "T3",
                    "title": "Activity vs Outcome Orientation",
                    "description": "Many goals describe activities rather than measurable outcomes",
                    "frequency": "60% of employees",
                    "impact": "negative",
                    "affectedPerspectives": ["financial", "customer", "process", "learning"]
                },
                {
                    "themeId": "T4",
                    "title": "Learning Goals Underrepresented",
                    "description": "Capability building and skill development goals are minimal",
                    "frequency": "40% of employees",
                    "impact": "negative",
                    "affectedPerspectives": ["learning"]
                }
            ],
            "strategicGaps": [
                {
                    "gapId": "G1",
                    "title": "Customer Experience Blind Spot",
                    "description": "Few goals directly address customer satisfaction, NPS, or service quality improvements",
                    "affectedObjectives": ["C1", "C2", "C3"],
                    "severity": "critical",
                    "businessRisk": "May miss market shifts and lose competitive advantage in customer service"
                },
                {
                    "gapId": "G2",
                    "title": "Innovation Deficit",
                    "description": "No goals target new product development, digital transformation, or market expansion",
                    "affectedObjectives": ["F1", "C1"],
                    "severity": "critical",
                    "businessRisk": "Risk of commoditization and inability to capture growth opportunities"
                },
                {
                    "gapId": "G3",
                    "title": "Capability Development Lag",
                    "description": "Insufficient focus on skill building, succession planning, and knowledge management",
                    "affectedObjectives": ["L1", "L2", "L3"],
                    "severity": "moderate",
                    "businessRisk": "May create talent gaps and limit organizational adaptability"
                }
            ],
            "systemicRecommendations": [
                {
                    "recommendationId": "SR1",
                    "title": "Implement Balanced Scorecard Goal Requirements",
                    "description": "Require each employee to have at least one goal in each BSC perspective",
                    "rationale": "Ensures comprehensive coverage of strategic objectives across the portfolio",
                    "targetAudience": "HR/Talent team and all managers",
                    "expectedOutcome": "25% improvement in strategic coverage within one goal cycle",
                    "linkedGaps": ["G1", "G3"]
                },
                {
                    "recommendationId": "SR2",
                    "title": "Shift to OKR Framework",
                    "description": "Transition from activity-based goals to Objectives and Key Results format",
                    "rationale": "OKRs naturally emphasize outcomes over activities and improve measurability",
                    "targetAudience": "All employees with manager training first",
                    "expectedOutcome": "40% increase in outcome-oriented goals",
                    "linkedGaps": ["G1", "G2"]
                },
                {
                    "recommendationId": "SR3",
                    "title": "Introduce Customer Impact Requirements",
                    "description": "Mandate that 20% of each team's goals directly impact customer metrics",
                    "rationale": "Addresses the critical gap in customer-facing objectives",
                    "targetAudience": "Department heads and team leads",
                    "expectedOutcome": "Improved NPS and customer retention within 6 months",
                    "linkedGaps": ["G1"]
                },
                {
                    "recommendationId": "SR4",
                    "title": "Establish Goal Quality Review Process",
                    "description": "Implement peer review of goals against strategic alignment criteria before finalization",
                    "rationale": "Catches misalignment early and promotes learning across teams",
                    "targetAudience": "All managers",
                    "expectedOutcome": "15-20% improvement in average alignment scores",
                    "linkedGaps": ["G1", "G2", "G3"]
                }
            ],
            "priorityActions": [
                {
                    "actionId": "A1",
                    "action": "Conduct goal-setting workshop focused on customer impact and measurable outcomes",
                    "owner": "HR/OD Lead",
                    "timeframe": "Next 30 days",
                    "expectedImpact": "Immediate improvement in goal quality for upcoming cycle"
                },
                {
                    "actionId": "A2",
                    "action": "Review and revise the bottom 20% of employees' goals with their managers",
                    "owner": "Department Heads",
                    "timeframe": "Next 14 days",
                    "expectedImpact": "Quick wins in strategic alignment for at-risk goal sets"
                },
                {
                    "actionId": "A3",
                    "action": "Develop goal templates with built-in strategic linkage requirements",
                    "owner": "HR Systems/Talent Team",
                    "timeframe": "Next 45 days",
                    "expectedImpact": "Structural improvement in goal quality for all future submissions"
                }
            ],
            "metadata": {
                "employeesAnalyzed": len(all_analyses),
                "averageAlignmentScore": round(avg_alignment, 1),
                "averageImpactScore": round(avg_impact, 1),
                "generatedAt": datetime.utcnow().isoformat() + "Z"
            }
        }

    def test_connection(self) -> bool:
        return True
