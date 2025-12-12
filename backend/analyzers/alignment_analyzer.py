"""
Alignment Analyzer
Deep semantic analysis of employee goals against strategic framework.
"""

import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime

from .claude_client import ClaudeClient


@dataclass
class GoalAnalysis:
    """Analysis result for a single goal."""
    goalId: str
    goalText: str
    alignmentScore: int
    impactScore: int
    alignedObjectives: List[str]
    alignmentRationale: str
    impactRationale: str
    gaps: List[str]


@dataclass
class StrategicCoverage:
    """Coverage metrics for a strategic perspective."""
    covered: int
    total: int
    percentage: float


@dataclass
class DocumentAnalysis:
    """Complete analysis result for a goal document."""
    documentId: str
    fileName: str
    overallAlignmentScore: int
    overallImpactScore: int
    goals: List[GoalAnalysis]
    strategicCoverage: Dict[str, StrategicCoverage]
    recommendations: List[str]
    metadata: Dict[str, Any]


class AlignmentAnalyzer:
    """
    Analyzes alignment between employee goals and strategic framework.
    Uses Claude API for semantic analysis (not keyword matching).
    """

    MAX_GOAL_DOCUMENTS = 15
    PERSPECTIVES = ['financial', 'customer', 'process', 'learning']

    def __init__(
        self,
        strategic_framework: Dict[str, Any],
        claude_client: Optional[ClaudeClient] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the alignment analyzer.

        Args:
            strategic_framework: Strategic framework from StrategySynthesizer
            claude_client: Pre-configured Claude client (for testing)
            api_key: API key for Claude
        """
        self.framework = strategic_framework
        if claude_client:
            self.client = claude_client
        elif api_key:
            self.client = ClaudeClient(api_key=api_key)
        else:
            self.client = ClaudeClient()

    def analyze(self, goal_document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single goal document against the strategic framework.

        Args:
            goal_document: Processed goal document with 'extractedText'

        Returns:
            Analysis result with alignment and impact scores
        """
        document_text = goal_document.get('extractedText', '')
        file_name = goal_document.get('fileName', 'Unknown')

        if not document_text:
            raise ValueError("Goal document must contain extractedText")

        # Extract employee context if available (from goals table upload)
        employee_context = self._extract_employee_context(goal_document)

        # Use Claude to analyze alignment with employee context
        raw_analysis = self.client.analyze_goal_alignment(
            self.framework,
            document_text,
            employee_context=employee_context
        )

        # Validate and enhance analysis
        analysis = self._validate_analysis(raw_analysis)

        # Calculate strategic coverage
        coverage = self._calculate_coverage(analysis)
        analysis['strategicCoverage'] = coverage

        # Add metadata
        analysis['documentId'] = str(uuid.uuid4())
        analysis['fileName'] = file_name
        analysis['metadata'] = {
            'analysisTimestamp': datetime.utcnow().isoformat() + 'Z',
            'goalCount': len(analysis.get('goals', [])),
            'frameworkId': self.framework.get('metadata', {}).get('frameworkId', 'unknown')
        }

        # Preserve employee metadata in analysis
        if employee_context:
            analysis['employeeContext'] = employee_context

        return analysis

    def _extract_employee_context(self, goal_document: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract employee context from goal document metadata.

        Args:
            goal_document: Processed goal document

        Returns:
            Employee context dictionary or None
        """
        # Check for employeeMetadata (from goals table upload)
        emp_meta = goal_document.get('employeeMetadata', {})
        doc_meta = goal_document.get('metadata', {})

        # Try to extract employee info from various possible locations
        employee_name = emp_meta.get('employeeName') or doc_meta.get('employeeName')
        job_title = emp_meta.get('jobTitle') or doc_meta.get('jobTitle')
        department = emp_meta.get('department') or doc_meta.get('department')
        seniority_level = emp_meta.get('seniorityLevel') or doc_meta.get('seniorityLevel')

        # If no employee context available, return None
        if not any([employee_name, job_title, department, seniority_level]):
            return None

        # Build context
        context = {
            'employeeName': employee_name or 'Unknown',
            'jobTitle': job_title,
            'department': department,
            'seniorityLevel': seniority_level
        }

        # Extract goals with weights if available from structured sections
        goals_with_weights = []
        structured = goal_document.get('structuredSections', [])
        for section in structured:
            if section.get('heading', '').lower() == 'goals':
                # Parse goals from content (format from goals_table_processor)
                content = section.get('content', '')
                for line in content.split('\n'):
                    if line.strip().startswith('Goal'):
                        # Extract goal text and weight if present
                        goal_info = {'goalText': line.strip()}
                        if 'Weight:' in content:
                            # Try to find weight on nearby line
                            pass  # Weight parsing handled below
                        goals_with_weights.append(goal_info)

        # Also check raw goals data if from goals_table_processor
        raw_goals = goal_document.get('goals', [])
        if raw_goals:
            goals_with_weights = []
            for goal in raw_goals:
                if isinstance(goal, dict):
                    goals_with_weights.append({
                        'goalText': goal.get('goalText', ''),
                        'weight': goal.get('weight', ''),
                        'category': goal.get('category', '')
                    })

        if goals_with_weights:
            context['goalsWithWeights'] = goals_with_weights

        return context

    def analyze_batch(self, goal_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple goal documents.

        Args:
            goal_documents: List of processed goal documents

        Returns:
            List of analysis results
        """
        if len(goal_documents) > self.MAX_GOAL_DOCUMENTS:
            raise ValueError(f"Maximum {self.MAX_GOAL_DOCUMENTS} documents allowed")

        results = []
        for doc in goal_documents:
            try:
                result = self.analyze(doc)
                results.append(result)
            except Exception as e:
                results.append({
                    'documentId': str(uuid.uuid4()),
                    'fileName': doc.get('fileName', 'Unknown'),
                    'error': str(e),
                    'overallAlignmentScore': 0,
                    'overallImpactScore': 0,
                    'goals': [],
                    'strategicCoverage': {},
                    'recommendations': []
                })

        return results

    def _validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and ensure analysis has required structure.

        Args:
            analysis: Raw analysis from Claude

        Returns:
            Validated analysis
        """
        # Ensure overall scores
        analysis['overallAlignmentScore'] = self._clamp_score(
            analysis.get('overallAlignmentScore', 50)
        )
        analysis['overallImpactScore'] = self._clamp_score(
            analysis.get('overallImpactScore', 50)
        )
        analysis['overallCoherenceScore'] = self._clamp_score(
            analysis.get('overallCoherenceScore', 50)
        )

        # Ensure role appropriateness assessment
        if 'roleAppropriatenessAssessment' not in analysis:
            analysis['roleAppropriatenessAssessment'] = ''

        # Ensure goals array
        if 'goals' not in analysis:
            analysis['goals'] = []

        for i, goal in enumerate(analysis['goals']):
            if 'goalId' not in goal:
                goal['goalId'] = f"G{i+1}"
            goal['goalText'] = goal.get('goalText', '')
            goal['alignmentScore'] = self._clamp_score(goal.get('alignmentScore', 50))
            goal['impactScore'] = self._clamp_score(goal.get('impactScore', 50))
            goal['alignedObjectives'] = goal.get('alignedObjectives', [])
            goal['alignmentRationale'] = goal.get('alignmentRationale', '')
            goal['impactRationale'] = goal.get('impactRationale', '')
            goal['roleAppropriateness'] = goal.get('roleAppropriateness', '')
            goal['gaps'] = goal.get('gaps', [])

            # Ensure SMART assessment
            if 'smartAssessment' not in goal:
                goal['smartAssessment'] = {
                    'specific': True,
                    'measurable': True,
                    'achievable': True,
                    'relevant': True,
                    'timeBound': True,
                    'notes': ''
                }

        # Ensure goal set coherence
        if 'goalSetCoherence' not in analysis:
            analysis['goalSetCoherence'] = {
                'internalConsistency': '',
                'balancedCoverage': '',
                'weightDistributionAssessment': '',
                'overallCoherenceNotes': ''
            }

        # Ensure recommendations
        if 'recommendations' not in analysis:
            analysis['recommendations'] = []

        return analysis

    def _clamp_score(self, score: int) -> int:
        """Clamp score to 0-100 range."""
        try:
            score = int(score)
            return max(0, min(100, score))
        except (TypeError, ValueError):
            return 50

    def _calculate_coverage(self, analysis: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate strategic coverage from goal alignments.

        Args:
            analysis: Goal analysis with aligned objectives

        Returns:
            Coverage metrics per perspective
        """
        # Get all objective IDs from framework
        objective_ids_by_perspective = self._get_objectives_by_perspective()

        # Collect all aligned objectives from goals
        aligned_ids = set()
        for goal in analysis.get('goals', []):
            aligned_ids.update(goal.get('alignedObjectives', []))

        # Calculate coverage per perspective
        coverage = {}
        perspective_map = {
            'financial': 'F',
            'customer': 'C',
            'process': ['P', 'I'],  # Process or Internal
            'learning': 'L'
        }

        for perspective, prefix in perspective_map.items():
            if isinstance(prefix, list):
                total_ids = [
                    oid for oid in objective_ids_by_perspective.get('internalProcess', [])
                ]
            else:
                total_ids = [
                    oid for oid in objective_ids_by_perspective.get(
                        self._perspective_key(perspective), []
                    )
                ]

            if not total_ids:
                coverage[perspective] = {
                    'covered': 0,
                    'total': 0,
                    'percentage': 0
                }
                continue

            covered_count = sum(1 for oid in total_ids if oid in aligned_ids)
            total_count = len(total_ids)
            percentage = (covered_count / total_count * 100) if total_count > 0 else 0

            coverage[perspective] = {
                'covered': covered_count,
                'total': total_count,
                'percentage': round(percentage, 1)
            }

        return coverage

    def _perspective_key(self, short_name: str) -> str:
        """Map short perspective names to framework keys."""
        mapping = {
            'financial': 'financial',
            'customer': 'customer',
            'process': 'internalProcess',
            'learning': 'learningGrowth'
        }
        return mapping.get(short_name, short_name)

    def _get_objectives_by_perspective(self) -> Dict[str, List[str]]:
        """Get objective IDs grouped by perspective."""
        objectives = {}
        perspectives = self.framework.get('strategicPerspectives', {})

        for p_name, p_data in perspectives.items():
            obj_ids = [obj['id'] for obj in p_data.get('objectives', []) if 'id' in obj]
            objectives[p_name] = obj_ids

        return objectives

    def calculate_tier(self, alignment_score: int, impact_score: int) -> Dict[str, str]:
        """
        Calculate tier based on alignment and impact scores.

        Args:
            alignment_score: Alignment score (0-100)
            impact_score: Impact score (0-100)

        Returns:
            Tier information with tier name, color, and label
        """
        composite = (alignment_score * 0.6) + (impact_score * 0.4)

        if composite >= 80:
            return {
                'tier': 'high',
                'color': 'teal',
                'label': 'Strong Strategic Fit',
                'composite': round(composite, 1)
            }
        elif composite >= 50:
            return {
                'tier': 'moderate',
                'color': 'amber',
                'label': 'Partial Alignment',
                'composite': round(composite, 1)
            }
        else:
            return {
                'tier': 'low',
                'color': 'rose',
                'label': 'Requires Revision',
                'composite': round(composite, 1)
            }

    def get_gap_analysis(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate gap analysis across all analyzed documents.

        Args:
            analyses: List of document analysis results

        Returns:
            Comprehensive gap analysis
        """
        all_objectives = self._get_objectives_by_perspective()

        # Collect all aligned objectives
        covered_objectives = set()
        for analysis in analyses:
            for goal in analysis.get('goals', []):
                covered_objectives.update(goal.get('alignedObjectives', []))

        # Find uncovered objectives
        uncovered = {}
        for p_name, obj_ids in all_objectives.items():
            uncovered_ids = [oid for oid in obj_ids if oid not in covered_objectives]
            if uncovered_ids:
                uncovered[p_name] = uncovered_ids

        # Find orphaned goals (low alignment)
        orphaned_goals = []
        for analysis in analyses:
            for goal in analysis.get('goals', []):
                if goal.get('alignmentScore', 0) < 30:
                    orphaned_goals.append({
                        'document': analysis.get('fileName'),
                        'goalId': goal.get('goalId'),
                        'goalText': goal.get('goalText', '')[:100]
                    })

        # Calculate overall coverage
        total_objectives = sum(len(ids) for ids in all_objectives.values())
        covered_count = len(covered_objectives)
        coverage_pct = (covered_count / total_objectives * 100) if total_objectives > 0 else 0

        return {
            'totalObjectives': total_objectives,
            'coveredObjectives': covered_count,
            'coveragePercentage': round(coverage_pct, 1),
            'uncoveredByPerspective': uncovered,
            'orphanedGoals': orphaned_goals,
            'criticalGaps': self._identify_critical_gaps(uncovered)
        }

    def _identify_critical_gaps(self, uncovered: Dict[str, List[str]]) -> List[str]:
        """Identify critical gaps in strategic coverage."""
        critical = []

        # Get KPRs from framework
        kprs = self.framework.get('keyPerformanceRequirements', [])
        critical_kprs = [k for k in kprs if k.get('priority') == 'critical']

        for kpr in critical_kprs:
            linked = kpr.get('linkedObjectiveIds', [])
            for obj_id in linked:
                for p_name, uncovered_ids in uncovered.items():
                    if obj_id in uncovered_ids:
                        critical.append(
                            f"Critical KPR '{kpr.get('requirement', '')[:50]}...' "
                            f"lacks goal coverage for objective {obj_id}"
                        )

        return critical

    def get_portfolio_summary(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate portfolio summary across all documents.

        Args:
            analyses: List of document analysis results

        Returns:
            Portfolio summary with rankings and statistics
        """
        valid_analyses = [a for a in analyses if 'error' not in a]

        if not valid_analyses:
            return {
                'totalDocuments': len(analyses),
                'validDocuments': 0,
                'averageAlignmentScore': 0,
                'averageImpactScore': 0,
                'tierDistribution': {},
                'topPerformers': [],
                'needsAttention': []
            }

        # Calculate averages
        avg_alignment = sum(a['overallAlignmentScore'] for a in valid_analyses) / len(valid_analyses)
        avg_impact = sum(a['overallImpactScore'] for a in valid_analyses) / len(valid_analyses)

        # Calculate tier distribution
        tier_dist = {'high': 0, 'moderate': 0, 'low': 0}
        for a in valid_analyses:
            tier = self.calculate_tier(a['overallAlignmentScore'], a['overallImpactScore'])
            tier_dist[tier['tier']] += 1

        # Identify top performers and needs attention
        sorted_by_alignment = sorted(valid_analyses, key=lambda x: x['overallAlignmentScore'], reverse=True)
        top_performers = [
            {'fileName': a['fileName'], 'alignmentScore': a['overallAlignmentScore']}
            for a in sorted_by_alignment[:3]
        ]
        needs_attention = [
            {'fileName': a['fileName'], 'alignmentScore': a['overallAlignmentScore']}
            for a in sorted_by_alignment[-3:] if a['overallAlignmentScore'] < 50
        ]

        return {
            'totalDocuments': len(analyses),
            'validDocuments': len(valid_analyses),
            'averageAlignmentScore': round(avg_alignment, 1),
            'averageImpactScore': round(avg_impact, 1),
            'tierDistribution': tier_dist,
            'topPerformers': top_performers,
            'needsAttention': needs_attention
        }


class MockAlignmentClient:
    """
    Mock client for testing alignment analysis without API calls.
    Generates role-contextualized rationales based on employee metadata.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "mock-key"

    def analyze_goal_alignment(
        self,
        strategic_framework: Dict[str, Any],
        goal_document_text: str,
        employee_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Return mock alignment analysis with role-contextualized rationales."""
        # Extract employee info for contextualized rationales
        emp_name = "the employee"
        job_title = "team member"
        seniority = "mid"
        department = "the organization"

        if employee_context:
            emp_name = employee_context.get('employeeName', emp_name)
            job_title = employee_context.get('jobTitle') or job_title
            seniority = employee_context.get('seniorityLevel') or seniority
            department = employee_context.get('department') or department

        # Detect goals from text (simple parsing)
        goals = self._parse_goals(goal_document_text, job_title, seniority, department)

        # Generate role-appropriate assessment
        role_assessment = self._generate_role_assessment(job_title, seniority, len(goals))

        # Generate coherence assessment
        coherence = self._generate_coherence_assessment(goals, seniority)

        return {
            "overallAlignmentScore": 72,
            "overallImpactScore": 68,
            "overallCoherenceScore": 70,
            "roleAppropriatenessAssessment": role_assessment,
            "goals": goals,
            "goalSetCoherence": coherence,
            "recommendations": self._generate_recommendations(job_title, seniority, department)
        }

    def _parse_goals(
        self,
        text: str,
        job_title: str,
        seniority: str,
        department: str
    ) -> List[Dict[str, Any]]:
        """Parse goals and generate role-contextualized rationales."""
        goals = []
        lines = text.split('\n')

        goal_num = 0
        for line in lines:
            line_lower = line.lower().strip()
            # Look for lines that might be goals
            if (line_lower.startswith('goal') or
                line_lower.startswith('objective') or
                'reduce' in line_lower or
                'improve' in line_lower or
                'implement' in line_lower or
                'achieve' in line_lower or
                'complete' in line_lower):

                if len(line) > 20:  # Substantial text
                    goal_num += 1
                    goals.append(self._create_goal_analysis(
                        goal_num, line.strip()[:200], job_title, seniority, department
                    ))

        # Ensure at least some goals
        if not goals:
            goals = [self._create_goal_analysis(1, "Process improvement goal", job_title, seniority, department)]

        return goals

    def _create_goal_analysis(
        self,
        goal_num: int,
        goal_text: str,
        job_title: str,
        seniority: str,
        department: str
    ) -> Dict[str, Any]:
        """Create a goal analysis with role-contextualized rationales."""
        aligned_objectives = self._assign_mock_objectives(goal_num)
        alignment_score = 70 + (goal_num % 20)
        impact_score = 65 + (goal_num % 25)

        # Generate role-specific alignment rationale
        alignment_rationale = self._generate_alignment_rationale(
            goal_text, job_title, seniority, department, aligned_objectives
        )

        # Generate role-specific impact rationale
        impact_rationale = self._generate_impact_rationale(
            goal_text, job_title, seniority, department
        )

        # Generate role appropriateness assessment
        role_appropriateness = self._generate_role_appropriateness(
            goal_text, job_title, seniority
        )

        # Generate SMART assessment
        smart = self._assess_smart(goal_text)

        return {
            "goalId": f"G{goal_num}",
            "goalText": goal_text,
            "alignmentScore": alignment_score,
            "impactScore": impact_score,
            "alignedObjectives": aligned_objectives,
            "alignmentRationale": alignment_rationale,
            "impactRationale": impact_rationale,
            "roleAppropriateness": role_appropriateness,
            "gaps": self._identify_gaps(goal_num, seniority),
            "smartAssessment": smart
        }

    def _generate_alignment_rationale(
        self,
        goal_text: str,
        job_title: str,
        seniority: str,
        department: str,
        aligned_objectives: List[str]
    ) -> str:
        """Generate role-contextualized alignment rationale."""
        obj_str = ", ".join(aligned_objectives)

        if seniority == 'executive':
            return (
                f"As a {job_title}, this goal demonstrates enterprise-level strategic thinking by "
                f"directly enabling objectives {obj_str}. The scope and ambition are appropriate for "
                f"an executive role, focusing on outcomes that cascade throughout {department}. "
                f"This goal shows strong translation of organizational vision into leadership action."
            )
        elif seniority == 'senior':
            return (
                f"This goal effectively bridges strategic intent to operational execution, which is "
                f"appropriate for a {job_title} at the senior level. It connects to objectives {obj_str} "
                f"by translating organizational priorities into actionable team initiatives within {department}. "
                f"The goal shows understanding of how to operationalize strategy."
            )
        elif seniority == 'junior':
            return (
                f"For a {job_title} at an early career stage, this goal appropriately focuses on "
                f"foundational contributions that support objectives {obj_str}. It demonstrates emerging "
                f"understanding of how individual work connects to {department}'s strategic priorities, "
                f"though the linkage could be more explicitly articulated."
            )
        else:  # mid-level
            return (
                f"As a {job_title}, this goal reflects solid understanding of how functional work "
                f"contributes to organizational strategy. It supports objectives {obj_str} through "
                f"team-level execution in {department}. The goal appropriately balances individual "
                f"contribution with awareness of broader strategic context."
            )

    def _generate_impact_rationale(
        self,
        goal_text: str,
        job_title: str,
        seniority: str,
        department: str
    ) -> str:
        """Generate role-contextualized impact rationale."""
        if seniority == 'executive':
            return (
                f"Given the {job_title} role's span of influence, successful achievement would have "
                f"significant strategic leverage, potentially enabling multiple downstream objectives "
                f"and setting direction for {department}. Impact extends beyond direct outcomes to "
                f"organizational capability building."
            )
        elif seniority == 'senior':
            return (
                f"As a {job_title}, successful execution would demonstrate leadership in {department} "
                f"and create enabling conditions for team success. The impact multiplier comes from "
                f"both direct contribution and influence on others' effectiveness."
            )
        elif seniority == 'junior':
            return (
                f"For a {job_title}, this goal's impact is appropriately scoped to direct individual "
                f"contribution within {department}. Success builds foundational capabilities and "
                f"demonstrates readiness for increased responsibility."
            )
        else:
            return (
                f"The {job_title} role positions this goal for meaningful functional impact within "
                f"{department}. Success would contribute directly to team objectives while demonstrating "
                f"the ability to execute on strategic priorities."
            )

    def _generate_role_appropriateness(
        self,
        goal_text: str,
        job_title: str,
        seniority: str
    ) -> str:
        """Assess if goal is appropriate for the role/level."""
        if seniority == 'executive':
            return (
                f"The goal's scope is generally appropriate for an executive {job_title} role, "
                f"focusing on strategic outcomes rather than tactical activities. Consider ensuring "
                f"the goal emphasizes enterprise impact and leadership enablement."
            )
        elif seniority == 'senior':
            return (
                f"This goal is well-suited for a senior {job_title}, appropriately balancing "
                f"strategic alignment with operational leadership. The scope reflects expected "
                f"influence over team and cross-functional outcomes."
            )
        elif seniority == 'junior':
            return (
                f"For a {job_title} at the junior level, this goal is appropriately focused on "
                f"skill development and direct contribution. The scope is achievable while "
                f"providing meaningful learning opportunities."
            )
        else:
            return (
                f"The goal's scope and complexity are appropriate for a mid-level {job_title}, "
                f"requiring both individual expertise and collaborative execution."
            )

    def _generate_role_assessment(self, job_title: str, seniority: str, goal_count: int) -> str:
        """Generate overall role appropriateness assessment."""
        if seniority == 'executive':
            return (
                f"As a {job_title} at the executive level, the goal set shows appropriate strategic focus. "
                f"The {goal_count} goals generally reflect enterprise-level thinking, though some could "
                f"be elevated to focus more on enabling organizational capabilities rather than direct execution. "
                f"Executive goals should cascade to enable others' success."
            )
        elif seniority == 'senior':
            return (
                f"The goal set for this {job_title} (senior level) appropriately bridges strategy and execution. "
                f"The {goal_count} goals show good balance between leadership responsibilities and operational "
                f"impact. Consider strengthening cross-functional collaboration elements."
            )
        elif seniority == 'junior':
            return (
                f"For a {job_title} at the junior level, this goal set appropriately emphasizes skill building "
                f"and direct contribution. The {goal_count} goals are achievable and provide clear success criteria. "
                f"Consider adding goals that demonstrate understanding of broader organizational context."
            )
        else:
            return (
                f"This {job_title} (mid-level) has a goal set that balances individual contribution with team impact. "
                f"The {goal_count} goals show solid understanding of functional responsibilities. Consider adding "
                f"stretch goals that demonstrate readiness for advancement."
            )

    def _generate_coherence_assessment(
        self,
        goals: List[Dict[str, Any]],
        seniority: str
    ) -> Dict[str, str]:
        """Generate goal set coherence assessment."""
        goal_count = len(goals)

        return {
            "internalConsistency": (
                f"The {goal_count} goals are generally complementary, with process-focused goals supporting "
                f"outcome-oriented objectives. No significant conflicts identified, though some goals "
                f"could be more explicitly linked to show interdependencies."
            ),
            "balancedCoverage": (
                "The goal set shows strong coverage of internal process objectives but could benefit from "
                "additional focus on customer-facing and learning/growth perspectives. Consider adding goals "
                "that address capability development and stakeholder value creation."
            ),
            "weightDistributionAssessment": (
                "If weights are assigned, verify that strategic priorities (customer satisfaction, "
                "operational excellence) receive appropriate emphasis. Current distribution appears "
                "reasonable but should align with organizational strategic emphasis areas."
            ),
            "overallCoherenceNotes": (
                f"Overall, this goal set tells a coherent story of contribution at the {seniority} level. "
                f"The goals work together to demonstrate both individual expertise and organizational awareness. "
                f"Strengthening explicit linkages between goals would improve the strategic narrative."
            )
        }

    def _generate_recommendations(
        self,
        job_title: str,
        seniority: str,
        department: str
    ) -> List[str]:
        """Generate role-specific recommendations."""
        base_recommendations = [
            f"Add goals addressing customer perspective objectives relevant to {department}",
            "Strengthen linkage to sustainability and ESG initiatives",
            "Include more measurable targets with specific timelines"
        ]

        if seniority == 'executive':
            base_recommendations.extend([
                "Consider adding goals focused on organizational capability building",
                "Include goals that enable and cascade to leadership team success"
            ])
        elif seniority == 'senior':
            base_recommendations.extend([
                f"Add cross-functional collaboration goals within {department}",
                "Consider goals that develop team members' capabilities"
            ])
        elif seniority == 'junior':
            base_recommendations.extend([
                "Add goals focused on skill development in strategic areas",
                f"Consider stretch goals that demonstrate readiness for growth in {department}"
            ])
        else:
            base_recommendations.extend([
                "Add goals demonstrating cross-functional impact",
                "Consider including innovation or improvement-focused goals"
            ])

        return base_recommendations[:5]  # Return top 5

    def _assign_mock_objectives(self, goal_num: int) -> List[str]:
        """Assign mock objective alignments."""
        objectives_pool = [
            ["P1", "P3"],
            ["P2", "L1"],
            ["C1", "C2"],
            ["F1", "P3"],
            ["L1", "L2"]
        ]
        return objectives_pool[goal_num % len(objectives_pool)]

    def _identify_gaps(self, goal_num: int, seniority: str) -> List[str]:
        """Identify gaps based on goal and seniority."""
        if goal_num % 2 == 0:
            if seniority == 'executive':
                return ["No explicit linkage to shareholder value metrics"]
            elif seniority == 'senior':
                return ["Could strengthen connection to team development outcomes"]
            else:
                return ["No direct link to customer satisfaction metrics"]
        return []

    def _assess_smart(self, goal_text: str) -> Dict[str, Any]:
        """Assess SMART criteria for a goal."""
        text_lower = goal_text.lower()

        has_number = any(char.isdigit() for char in goal_text)
        has_timeframe = any(word in text_lower for word in ['by', 'within', 'q1', 'q2', 'q3', 'q4', 'year', 'month'])
        has_action = any(word in text_lower for word in ['reduce', 'improve', 'increase', 'achieve', 'complete', 'implement'])

        return {
            "specific": has_action,
            "measurable": has_number,
            "achievable": True,  # Assume achievable without more context
            "relevant": True,  # Assume relevant since it's in goals
            "timeBound": has_timeframe,
            "notes": (
                "Goal could be strengthened by adding " +
                ("specific metrics, " if not has_number else "") +
                ("clear timelines, " if not has_timeframe else "") +
                ("action-oriented language" if not has_action else "")
            ).rstrip(", ") or "Goal meets SMART criteria well"
        }

    def test_connection(self) -> bool:
        return True
