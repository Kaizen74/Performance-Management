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

    MAX_GOAL_DOCUMENTS = 500
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

        # PRIORITY 1: Check for goalsWithWeights in employeeMetadata (from goals_table_processor)
        goals_with_weights = emp_meta.get('goalsWithWeights', [])
        if goals_with_weights:
            context['goalsWithWeights'] = goals_with_weights
            return context

        # PRIORITY 2: Check raw goals data at document level
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

        # PRIORITY 3: Extract goals from structured sections
        import re
        structured = goal_document.get('structuredSections', [])
        for section in structured:
            if section.get('heading', '').lower() == 'goals':
                content = section.get('content', '')
                # Parse "Goal N: <text>" format
                goal_pattern = re.compile(r'Goal\s*(\d+)\s*[:.]?\s*(.+?)(?=Goal\s*\d+|$|\n\n)', re.IGNORECASE | re.DOTALL)
                matches = goal_pattern.findall(content)

                if matches:
                    goals_with_weights = []
                    for match in matches:
                        goal_block = match[1].strip()
                        goal_lines = goal_block.split('\n')
                        goal_text = goal_lines[0].strip()

                        # Extract optional fields from following lines
                        weight = ''
                        category = ''
                        description = ''
                        for line in goal_lines[1:]:
                            line_lower = line.strip().lower()
                            if line_lower.startswith('weight:'):
                                weight = line.split(':', 1)[-1].strip()
                            elif line_lower.startswith('category:'):
                                category = line.split(':', 1)[-1].strip()
                            elif line_lower.startswith('description:'):
                                description = line.split(':', 1)[-1].strip()

                        if goal_text:
                            goals_with_weights.append({
                                'goalText': goal_text,
                                'weight': weight,
                                'category': category,
                                'description': description
                            })

                    if goals_with_weights:
                        context['goalsWithWeights'] = goals_with_weights
                        return context

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

        # Ensure strategy coherence check (mismatch detection)
        if 'strategyCoherenceCheck' not in analysis:
            analysis['strategyCoherenceCheck'] = {
                'confidenceScore': 75,
                'belongsToStrategy': True,
                'potentialMismatches': [],
                'assessment': ''
            }
        else:
            scc = analysis['strategyCoherenceCheck']
            scc['confidenceScore'] = self._clamp_score(scc.get('confidenceScore', 75))
            scc['belongsToStrategy'] = scc.get('belongsToStrategy', True)
            scc['potentialMismatches'] = scc.get('potentialMismatches', [])
            scc['assessment'] = scc.get('assessment', '')

        # Ensure strategic tie-back (explicit strategy reference)
        if 'strategicTieBack' not in analysis:
            analysis['strategicTieBack'] = {
                'visionAlignment': '',
                'missionContribution': '',
                'valuesReflected': [],
                'strategicThemesCovered': [],
                'strategicThemesGaps': []
            }
        else:
            stb = analysis['strategicTieBack']
            stb['visionAlignment'] = stb.get('visionAlignment', '')
            stb['missionContribution'] = stb.get('missionContribution', '')
            stb['valuesReflected'] = stb.get('valuesReflected', [])
            stb['strategicThemesCovered'] = stb.get('strategicThemesCovered', [])
            stb['strategicThemesGaps'] = stb.get('strategicThemesGaps', [])

        # Ensure role appropriateness assessment
        if 'roleAppropriatenessAssessment' not in analysis:
            analysis['roleAppropriatenessAssessment'] = ''

        # Ensure goals array
        if 'goals' not in analysis:
            analysis['goals'] = []

        # Ensure overall alignment score breakdown
        if 'overallAlignmentScoreBreakdown' not in analysis:
            analysis['overallAlignmentScoreBreakdown'] = {
                'averageGoalScore': analysis.get('overallAlignmentScore', 50),
                'themeCoverageBonus': 0,
                'themeGapPenalty': 0,
                'coherenceBonus': 0,
                'strategyMismatchPenalty': 0,
                'themeCoveragePercentage': 0,
                'strategyConfidence': 75
            }

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

            # Ensure per-goal alignment score breakdown
            if 'alignmentScoreBreakdown' not in goal:
                goal['alignmentScoreBreakdown'] = {
                    'totalScore': goal['alignmentScore'],
                    'objectiveMappingScore': 70,
                    'objectiveMappingRationale': 'Maps to strategic objectives',
                    'visionMissionScore': 70,
                    'visionMissionRationale': 'Supports organizational vision and mission',
                    'themeAlignmentScore': 60,
                    'themeAlignmentRationale': 'Related to strategic themes',
                    'roleAppropriatenessScore': 70,
                    'roleAppropriatenessRationale': 'Appropriate for role level'
                }

            # Ensure per-goal strategic tie-back
            if 'strategicTieBack' not in goal:
                goal['strategicTieBack'] = {
                    'visionConnection': '',
                    'missionSupport': '',
                    'strategicThemes': [],
                    'objectiveMapping': ''
                }
            else:
                gtb = goal['strategicTieBack']
                gtb['visionConnection'] = gtb.get('visionConnection', '')
                gtb['missionSupport'] = gtb.get('missionSupport', '')
                gtb['strategicThemes'] = gtb.get('strategicThemes', [])
                gtb['objectiveMapping'] = gtb.get('objectiveMapping', '')

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
    Generates role-contextualized rationales based on employee metadata and strategic framework.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "mock-key"

    def analyze_goal_alignment(
        self,
        strategic_framework: Dict[str, Any],
        goal_document_text: str,
        employee_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Return mock alignment analysis with strategy-tied scoring and role-contextualized rationales."""
        # Extract strategic content for explicit referencing
        org_purpose = strategic_framework.get('organizationalPurpose', {})
        self.vision = org_purpose.get('vision', 'To be an industry leader')
        self.mission = org_purpose.get('mission', 'Delivering value to stakeholders')
        self.values = org_purpose.get('values', ['Excellence', 'Innovation', 'Integrity'])

        strategic_themes = strategic_framework.get('strategicThemes', [])
        self.theme_names = [t.get('name', '') for t in strategic_themes if t.get('name')]
        if not self.theme_names:
            self.theme_names = ['Operational Excellence', 'Customer Focus', 'Innovation']

        # Extract strategic objectives for scoring
        self.strategic_objectives = self._extract_objectives(strategic_framework)

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

        # Extract structured goals from employee context if available (from Excel/CSV)
        structured_goals = None
        if employee_context:
            structured_goals = employee_context.get('goalsWithWeights', [])

        # Detect goals from text or use structured goals
        goals = self._parse_goals(
            goal_document_text, job_title, seniority, department,
            structured_goals=structured_goals
        )

        # Classify each goal using the Rigor × Alignment matrix
        classified_goals = self._classify_goals_matrix(goals, strategic_framework)

        # Calculate Coherence Index based on quadrant scoring
        coherence_analysis = self._calculate_coherence_index(classified_goals, strategic_framework)

        # Generate narrative analysis
        narrative = self._generate_coherence_narrative(coherence_analysis, strategic_framework)

        # Generate role-appropriate assessment
        role_assessment = self._generate_role_assessment(job_title, seniority, len(goals))

        # Generate coherence assessment
        coherence = self._generate_coherence_assessment(goals, seniority)

        # Generate strategy coherence check
        strategy_coherence = self._generate_strategy_coherence_check(goals, department)

        # Generate strategic tie-back
        strategic_tie_back = self._generate_strategic_tie_back(goals, seniority)

        # Calculate meaningful overall scores based on strategy tie-back
        overall_scores = self._calculate_overall_scores(
            goals, strategy_coherence, strategic_tie_back, seniority
        )

        return {
            "overallAlignmentScore": overall_scores['alignment'],
            "overallAlignmentScoreBreakdown": overall_scores['alignmentBreakdown'],
            "overallImpactScore": overall_scores['impact'],
            "overallCoherenceScore": overall_scores['coherence'],
            "strategyCoherenceCheck": strategy_coherence,
            "strategicTieBack": strategic_tie_back,
            "roleAppropriatenessAssessment": role_assessment,
            "goals": classified_goals,  # Now includes quadrant classification
            "goalSetCoherence": coherence,
            "coherenceIndex": coherence_analysis,  # New: Quadrant-based coherence index
            "strategicNarrative": narrative,  # New: Generated narrative analysis
            "recommendations": self._generate_recommendations(job_title, seniority, department)
        }

    def _extract_objectives(self, framework: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract strategic objectives from framework for scoring reference."""
        objectives = {}
        perspectives = framework.get('strategicPerspectives', {})

        for p_name, p_data in perspectives.items():
            obj_list = p_data.get('objectives', [])
            for obj in obj_list:
                obj_id = obj.get('id', '')
                obj_text = obj.get('objective', '')
                if obj_id:
                    objectives[obj_id] = obj_text

        return objectives

    def _classify_goals_matrix(
        self,
        goals: List[Dict[str, Any]],
        framework: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Classify each goal using the Rigor × Alignment matrix.

        Quadrants:
        - Strategic Driver (Aligned + Outcome): 100 points
        - Busy Work Trap (Aligned + Output): 50 points
        - Rogue Project (Misaligned + Outcome): 25 points
        - Distraction (Misaligned + Output): 0 points
        """
        # Define verb categories for rigor check
        outcome_verbs = [
            'increase', 'decrease', 'reduce', 'grow', 'save', 'convert',
            'generate', 'close', 'retain', 'achieve', 'deliver', 'attain',
            'expand', 'improve', 'maximize', 'minimize', 'accelerate',
            'eliminate', 'double', 'triple', 'cut', 'boost'
        ]
        output_verbs = [
            'research', 'analyze', 'meet', 'draft', 'create', 'launch',
            'support', 'review', 'maintain', 'send', 'prepare', 'develop',
            'implement', 'establish', 'coordinate', 'organize', 'plan',
            'document', 'attend', 'participate', 'assist', 'help', 'lead'
        ]

        # Extract strategic pillars/themes for alignment check
        themes = framework.get('strategicThemes', [])
        theme_keywords = {}
        for theme in themes:
            name = theme.get('name', '')
            desc = theme.get('description', '')
            # Build keywords from theme name and description
            keywords = set(name.lower().split())
            keywords.update(word.lower() for word in desc.split() if len(word) > 4)
            theme_keywords[name] = keywords

        # Also extract objective keywords
        perspectives = framework.get('strategicPerspectives', {})
        objective_keywords = set()
        for p_data in perspectives.values():
            for obj in p_data.get('objectives', []):
                obj_text = obj.get('objective', '').lower()
                objective_keywords.update(word for word in obj_text.split() if len(word) > 4)

        classified_goals = []
        for goal in goals:
            goal_text = goal.get('goalText', '').lower()
            goal_words = goal_text.split()

            # Check 1: Rigor (Output vs Outcome)
            is_outcome = False
            rigor_verb = None
            for word in goal_words[:5]:  # Check first few words
                clean_word = word.strip('.,;:').lower()
                if clean_word in outcome_verbs:
                    is_outcome = True
                    rigor_verb = clean_word
                    break
                elif clean_word in output_verbs:
                    rigor_verb = clean_word
                    break

            # Also check for quantifiable targets (strong indicator of outcome)
            has_metrics = any(char.isdigit() for char in goal_text) or '%' in goal_text
            if has_metrics and any(v in goal_text for v in ['increase', 'reduce', 'grow', 'achieve']):
                is_outcome = True

            # Financial goals with specific targets are inherently outcome-oriented
            # Patterns like "S$10.1M", "$5M", "baseline", "threshold", "target" indicate measurable financial outcomes
            is_financial_goal = (
                goal_text.startswith('[financial]') or
                any(indicator in goal_text for indicator in ['baseline', 'threshold', 'superior', 'target']) and
                any(char.isdigit() for char in goal_text)
            )
            has_currency = any(curr in goal_text for curr in ['$', 's$', '€', '£', 'usd', 'sgd'])

            if is_financial_goal and has_currency and has_metrics:
                is_outcome = True  # Financial targets are measurable outcomes

            # People/HR goals with specific targets are inherently outcome-oriented
            # Goals measuring retention, engagement, collaboration are Learning & Growth outcomes
            people_indicators = ['retention', 'engagement', 'collaboration', 'employee', 'talent',
                                'turnover', 'satisfaction', 'culture', 'workforce', 'headcount']
            is_people_goal = (
                goal_text.startswith('[people]') or
                goal_text.startswith('[hr]') or
                goal_text.startswith('[learning') or
                (any(indicator in goal_text for indicator in people_indicators) and
                 any(indicator in goal_text for indicator in ['target', 'threshold', 'superior', 'score']) and
                 has_metrics)
            )

            if is_people_goal and has_metrics:
                is_outcome = True  # People metrics with targets are measurable outcomes

            # Check 2: Alignment (does it map to strategic pillars?)
            is_aligned = False
            aligned_themes = []
            alignment_evidence = []

            # Check against each theme
            for theme_name, keywords in theme_keywords.items():
                matches = [kw for kw in keywords if kw in goal_text and len(kw) > 3]
                if len(matches) >= 2 or any(kw in goal_text for kw in keywords if len(kw) > 6):
                    is_aligned = True
                    aligned_themes.append(theme_name)
                    alignment_evidence.extend(matches[:2])

            # Check against strategic objectives
            obj_matches = [kw for kw in objective_keywords if kw in goal_text]
            if len(obj_matches) >= 2:
                is_aligned = True
                alignment_evidence.extend(obj_matches[:2])

            # Special check: Financial goals with specific targets are inherently strategic
            # They directly contribute to organizational financial success
            if is_financial_goal and has_currency and has_metrics:
                # Financial goals with measurable targets (baseline, threshold, superior)
                # are strategically aligned - they directly drive financial outcomes
                is_aligned = True
                if 'Financial' not in aligned_themes and 'financial' not in [t.lower() for t in aligned_themes]:
                    aligned_themes.append('Financial Performance')
                    alignment_evidence.extend(['financial target', 'measurable outcome'])

            # Special check: People/HR goals with specific targets are inherently strategic
            # They directly contribute to organizational capacity through Learning & Growth perspective
            if is_people_goal and has_metrics:
                # People goals with measurable targets (retention, engagement, collaboration scores)
                # are strategically aligned - they drive organizational capability and culture
                is_aligned = True
                if 'People' not in aligned_themes and 'Learning' not in aligned_themes:
                    aligned_themes.append('People & Culture')
                    alignment_evidence.extend(['people metric', 'organizational capacity'])

            # For other commercial goals without financial targets, check for alignment
            is_commercial = any(ind in goal_text for ind in ['revenue', 'sales', 'quota', 'deal'])
            if is_commercial and not aligned_themes and not is_financial_goal:
                # Generic commercial goal without specific strategic alignment = misaligned
                is_aligned = False

            # Determine quadrant and assign points
            if is_aligned and is_outcome:
                quadrant = "Strategic Driver"
                quadrant_points = 100
                quadrant_description = "High value: Links to strategy AND defines measurable result"
            elif is_aligned and not is_outcome:
                quadrant = "Busy Work Trap"
                quadrant_points = 50
                quadrant_description = "Right intent, weak execution: Links to strategy but defines task, not result"
            elif not is_aligned and is_outcome:
                quadrant = "Rogue Project"
                quadrant_points = 25
                quadrant_description = "Good execution, wrong direction: Measurable result but doesn't serve current strategy"
            else:
                quadrant = "Distraction"
                quadrant_points = 0
                quadrant_description = "Low value: Unrelated task that doesn't advance strategic goals"

            # Add classification to goal
            goal['quadrantClassification'] = {
                'quadrant': quadrant,
                'points': quadrant_points,
                'description': quadrant_description,
                'rigorCheck': {
                    'isOutcome': is_outcome,
                    'verbDetected': rigor_verb,
                    'hasMetrics': has_metrics
                },
                'alignmentCheck': {
                    'isAligned': is_aligned,
                    'alignedThemes': aligned_themes,
                    'evidence': list(set(alignment_evidence))[:3]
                }
            }

            # Update alignment rationale to reflect actual classification
            goal['alignmentRationale'] = self._generate_quadrant_rationale(
                goal_text=goal.get('goalText', ''),
                quadrant=quadrant,
                is_aligned=is_aligned,
                is_outcome=is_outcome,
                aligned_themes=aligned_themes,
                alignment_evidence=alignment_evidence,
                linked_objectives=goal.get('linkedObjectives', []),
                alignment_score=goal.get('alignmentScore', 50)
            )

            classified_goals.append(goal)

        return classified_goals

    def _generate_quadrant_rationale(
        self,
        goal_text: str,
        quadrant: str,
        is_aligned: bool,
        is_outcome: bool,
        aligned_themes: List[str],
        alignment_evidence: List[str],
        linked_objectives: List[str],
        alignment_score: int
    ) -> str:
        """Generate alignment rationale that accurately reflects the quadrant classification."""
        obj_str = ", ".join(linked_objectives) if linked_objectives else "none identified"
        themes_str = ", ".join(aligned_themes) if aligned_themes else "none"
        evidence_str = ", ".join(set(alignment_evidence[:3])) if alignment_evidence else "none"

        if quadrant == "Strategic Driver":
            return (
                f"STRONG ALIGNMENT: This goal directly supports strategic objectives ({obj_str}) "
                f"with clear outcome-oriented language. It connects to themes: {themes_str}. "
                f"The measurable focus ensures accountability and progress tracking. "
                f"Evidence of strategic linkage: {evidence_str}."
            )
        elif quadrant == "Busy Work Trap":
            return (
                f"PARTIAL ALIGNMENT: While this goal connects to strategic themes ({themes_str}) "
                f"and objectives ({obj_str}), it describes activities/tasks rather than measurable outcomes. "
                f"Consider reframing to specify WHAT result will be achieved, not just what will be done. "
                f"Current form risks effort without demonstrable strategic impact."
            )
        elif quadrant == "Rogue Project":
            return (
                f"MISALIGNED INITIATIVE: Although this goal has measurable outcomes, it does not clearly "
                f"connect to current strategic priorities. No strong alignment to strategic themes was found. "
                f"Linked objectives ({obj_str}) appear loosely connected at best. "
                f"Recommend revisiting to ensure effort advances organizational strategy, not personal interests."
            )
        else:  # Distraction
            return (
                f"WEAK ALIGNMENT: This goal lacks both strategic alignment AND measurable outcomes. "
                f"It describes an activity ('{goal_text[:50]}...') without clear connection to "
                f"organizational priorities or quantifiable results. No evidence of strategic linkage found. "
                f"This type of goal risks consuming time without advancing the organization's mission. "
                f"Strongly recommend revising to include specific outcomes tied to strategic objectives."
            )

    def _calculate_coherence_index(
        self,
        classified_goals: List[Dict[str, Any]],
        framework: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate the Coherence Index based on quadrant scoring.

        Formula: (Sum of all Goal Points) / (Total Number of Goals)
        """
        if not classified_goals:
            return {
                'score': 0,
                'verdict': 'No goals to analyze',
                'quadrantDistribution': {},
                'pillarCoverage': {}
            }

        # Calculate total points and distribution
        total_points = 0
        quadrant_counts = {
            'Strategic Driver': 0,
            'Busy Work Trap': 0,
            'Rogue Project': 0,
            'Distraction': 0
        }
        quadrant_examples = {
            'Strategic Driver': [],
            'Busy Work Trap': [],
            'Rogue Project': [],
            'Distraction': []
        }

        for goal in classified_goals:
            classification = goal.get('quadrantClassification', {})
            quadrant = classification.get('quadrant', 'Distraction')
            points = classification.get('points', 0)
            total_points += points
            quadrant_counts[quadrant] += 1

            # Store examples for narrative
            if len(quadrant_examples[quadrant]) < 2:
                quadrant_examples[quadrant].append({
                    'goalText': goal.get('goalText', '')[:100],
                    'verb': classification.get('rigorCheck', {}).get('verbDetected'),
                    'alignedThemes': classification.get('alignmentCheck', {}).get('alignedThemes', [])
                })

        # Calculate coherence index (0-100)
        num_goals = len(classified_goals)
        coherence_index = (total_points / num_goals) if num_goals > 0 else 0

        # Determine verdict
        if coherence_index >= 80:
            verdict = "Highly Aligned & Rigorous"
        elif coherence_index >= 50:
            verdict = "Strategically Intentioned but Operationally Weak"
        else:
            verdict = "Strategic Drift Detected"

        # Check pillar/theme coverage
        themes = framework.get('strategicThemes', [])
        theme_names = [t.get('name', '') for t in themes]
        covered_themes = set()
        for goal in classified_goals:
            aligned = goal.get('quadrantClassification', {}).get('alignmentCheck', {}).get('alignedThemes', [])
            covered_themes.update(aligned)

        uncovered_themes = [t for t in theme_names if t not in covered_themes]
        low_coverage_themes = []  # Could enhance with count-based analysis

        return {
            'score': round(coherence_index, 1),
            'verdict': verdict,
            'totalPoints': total_points,
            'maxPossiblePoints': num_goals * 100,
            'quadrantDistribution': quadrant_counts,
            'quadrantExamples': quadrant_examples,
            'pillarCoverage': {
                'totalPillars': len(theme_names),
                'coveredPillars': list(covered_themes),
                'uncoveredPillars': uncovered_themes,
                'coveragePercentage': round(len(covered_themes) / len(theme_names) * 100, 1) if theme_names else 0
            }
        }

    def _generate_coherence_narrative(
        self,
        coherence_analysis: Dict[str, Any],
        framework: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate the narrative analysis based on coherence index results.
        """
        score = coherence_analysis.get('score', 0)
        verdict = coherence_analysis.get('verdict', '')
        distribution = coherence_analysis.get('quadrantDistribution', {})
        examples = coherence_analysis.get('quadrantExamples', {})
        pillar_coverage = coherence_analysis.get('pillarCoverage', {})

        # Section 1: Strategy Coherence Score
        coherence_section = f"""Overall Coherence Index: {score}%

Verdict: {verdict}

This score is calculated by assigning weighted points to each goal based on its classification:
- Strategic Drivers (aligned outcomes): {distribution.get('Strategic Driver', 0)} goals × 100 points
- Busy Work Traps (aligned outputs): {distribution.get('Busy Work Trap', 0)} goals × 50 points
- Rogue Projects (misaligned outcomes): {distribution.get('Rogue Project', 0)} goals × 25 points
- Distractions (misaligned outputs): {distribution.get('Distraction', 0)} goals × 0 points"""

        # Section 2: Alignment Narrative
        strategic_drivers = distribution.get('Strategic Driver', 0)
        rogue_projects = distribution.get('Rogue Project', 0)

        alignment_narrative = f"""Alignment Analysis: {strategic_drivers} goals qualify as Strategic Drivers while {rogue_projects} are classified as Rogue Projects.

"""
        if rogue_projects > 0:
            rogue_examples = examples.get('Rogue Project', [])
            alignment_narrative += "Legacy Behavior Detection: Some goals demonstrate measurable outcomes but fail to connect to the current strategic priorities. "
            if rogue_examples:
                alignment_narrative += f"For example: '{rogue_examples[0].get('goalText', '')[:80]}...' targets a quantifiable result but does not explicitly align with the strategic themes: {', '.join(pillar_coverage.get('coveredPillars', ['Not specified'])[:3])}."
        else:
            alignment_narrative += "No significant legacy behavior detected - goals appear to be written with current strategy in mind."

        # Section 3: Rigor Narrative
        busy_work = distribution.get('Busy Work Trap', 0)
        distractions = distribution.get('Distraction', 0)

        rigor_narrative = f"""Rigor Analysis: {busy_work + distractions} goals use output-oriented language (tasks) rather than outcome-oriented language (results).

"""
        if busy_work > 0:
            busy_examples = examples.get('Busy Work Trap', [])
            rigor_narrative += "Motion vs Progress Warning: Several goals confuse activity with achievement. "
            if busy_examples:
                verb = busy_examples[0].get('verb', 'analyze')
                rigor_narrative += f"For example, a goal using '{verb}' could be strengthened by reframing: Instead of 'Analyze customer feedback', consider 'Increase customer satisfaction score by 10% through feedback-driven improvements'."

        # Section 4: Orphan Check
        uncovered = pillar_coverage.get('uncoveredPillars', [])
        coverage_pct = pillar_coverage.get('coveragePercentage', 0)

        orphan_narrative = f"""Strategic Pillar Coverage: {coverage_pct}% of strategic themes are addressed by current goals.

"""
        if uncovered:
            orphan_narrative += f"Warning: The following strategic pillars are under-supported: {', '.join(uncovered)}. This indicates a high risk of execution failure for these specific objectives. Consider adding goals that directly advance these strategic priorities."
        else:
            orphan_narrative += "All strategic pillars have at least one supporting goal. Monitor for adequate depth of coverage."

        return {
            'coherenceScore': coherence_section,
            'alignmentNarrative': alignment_narrative,
            'rigorNarrative': rigor_narrative,
            'orphanCheck': orphan_narrative,
            'fullNarrative': f"""STRATEGIC GOAL COHERENCE ASSESSMENT

{coherence_section}

---

ALIGNMENT ANALYSIS (The "What")

{alignment_narrative}

---

RIGOR ANALYSIS (The "How")

{rigor_narrative}

---

STRATEGIC COVERAGE CHECK

{orphan_narrative}"""
        }

    def _calculate_overall_scores(
        self,
        goals: List[Dict[str, Any]],
        strategy_coherence: Dict[str, Any],
        strategic_tie_back: Dict[str, Any],
        seniority: str
    ) -> Dict[str, Any]:
        """Calculate meaningful overall scores based on strategy tie-back."""
        if not goals:
            return {
                'alignment': 50,
                'alignmentBreakdown': {
                    'averageGoalScore': 50,
                    'themeCoverageBonus': 0,
                    'coherenceBonus': 0,
                    'strategyMismatchPenalty': 0
                },
                'impact': 50,
                'coherence': 50
            }

        # Calculate average of individual goal alignment scores
        goal_alignment_scores = [g.get('alignmentScore', 50) for g in goals]
        avg_goal_score = sum(goal_alignment_scores) / len(goal_alignment_scores)

        # Theme coverage bonus
        themes_covered = len(strategic_tie_back.get('strategicThemesCovered', []))
        total_themes = len(self.theme_names)
        theme_coverage_pct = (themes_covered / total_themes * 100) if total_themes > 0 else 0

        theme_bonus = 0
        if theme_coverage_pct >= 75:
            theme_bonus = 10
        elif theme_coverage_pct >= 50:
            theme_bonus = 5

        # Theme gap penalty (for critical themes not covered)
        theme_gaps = len(strategic_tie_back.get('strategicThemesGaps', []))
        theme_penalty = min(theme_gaps * 3, 15)  # Cap at 15 points penalty

        # Coherence bonus (if goals form a unified narrative)
        coherence_bonus = 5 if len(goals) >= 3 else 0

        # Strategy mismatch penalty
        strategy_confidence = strategy_coherence.get('confidenceScore', 100)
        mismatch_penalty = 0
        if strategy_confidence < 50:
            # Major mismatch - cap score at 40
            mismatch_penalty = max(0, avg_goal_score - 40)
        elif strategy_confidence < 70:
            # Moderate concern - apply penalty
            mismatch_penalty = 10

        # Calculate final alignment score
        alignment_score = avg_goal_score + theme_bonus - theme_penalty + coherence_bonus - mismatch_penalty
        alignment_score = max(0, min(100, round(alignment_score)))

        # Calculate impact score based on seniority and alignment
        impact_base = self._calculate_impact_base(seniority)
        impact_alignment_factor = alignment_score / 100
        impact_score = round(impact_base * impact_alignment_factor)
        impact_score = max(0, min(100, impact_score))

        # Calculate coherence score
        coherence_factors = [
            75,  # Base internal consistency
            60 + theme_coverage_pct * 0.3,  # Balanced coverage
            70  # Weight distribution
        ]
        coherence_score = round(sum(coherence_factors) / len(coherence_factors))
        coherence_score = max(0, min(100, coherence_score))

        return {
            'alignment': alignment_score,
            'alignmentBreakdown': {
                'averageGoalScore': round(avg_goal_score, 1),
                'themeCoverageBonus': theme_bonus,
                'themeGapPenalty': -theme_penalty,
                'coherenceBonus': coherence_bonus,
                'strategyMismatchPenalty': -mismatch_penalty,
                'themeCoveragePercentage': round(theme_coverage_pct, 1),
                'strategyConfidence': strategy_confidence
            },
            'impact': impact_score,
            'coherence': coherence_score
        }

    def _calculate_impact_base(self, seniority: str) -> int:
        """Calculate base impact score by seniority level."""
        # Higher seniority = higher potential impact
        # New categories: individual contributor, team leader, senior management
        impact_bases = {
            'senior management': 85,
            'team leader': 75,
            'individual contributor': 65,
            # Legacy mappings for backward compatibility
            'executive': 85,
            'senior': 75,
            'mid': 65,
            'junior': 55
        }
        return impact_bases.get(seniority, 65)

    def _parse_goals(
        self,
        text: str,
        job_title: str,
        seniority: str,
        department: str,
        structured_goals: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Parse goals and generate role-contextualized rationales.

        Args:
            text: Raw document text (fallback for parsing)
            job_title: Employee job title
            seniority: Seniority level
            department: Department name
            structured_goals: Pre-parsed goals from Excel/CSV (preferred source)
        """
        goals = []
        goal_num = 0

        # PRIORITY 1: Use structured goals from Excel/CSV if available
        if structured_goals and len(structured_goals) > 0:
            for goal_data in structured_goals:
                goal_text = goal_data.get('goalText', '').strip()
                if goal_text and len(goal_text) > 5:  # Minimal validation
                    goal_num += 1
                    # Include additional context from structured data
                    weight = goal_data.get('weight', '')
                    category = goal_data.get('category', '')

                    # Create enhanced goal text if weight/category available
                    enhanced_text = goal_text
                    if category:
                        enhanced_text = f"[{category}] {goal_text}"

                    goals.append(self._create_goal_analysis(
                        goal_num, enhanced_text[:300], job_title, seniority, department,
                        weight=weight, category=category
                    ))

            if goals:
                return goals

        # PRIORITY 2: Parse from structured text format (from goals_table_processor)
        # Look for "Goal N:" pattern from the processor output
        import re
        goal_pattern = re.compile(r'Goal\s*(\d+)\s*[:.]?\s*(.+?)(?=Goal\s*\d+|$)', re.IGNORECASE | re.DOTALL)
        matches = goal_pattern.findall(text)

        if matches:
            for match in matches:
                goal_text = match[1].strip()
                # Clean up: remove Description/Category/Weight lines that may follow
                goal_lines = goal_text.split('\n')
                main_goal = goal_lines[0].strip()

                if main_goal and len(main_goal) > 10:
                    goal_num += 1
                    # Extract category if present in following lines
                    category = ''
                    weight = ''
                    for line in goal_lines[1:]:
                        if 'category:' in line.lower():
                            category = line.split(':', 1)[-1].strip()
                        if 'weight:' in line.lower():
                            weight = line.split(':', 1)[-1].strip()

                    goals.append(self._create_goal_analysis(
                        goal_num, main_goal[:300], job_title, seniority, department,
                        weight=weight, category=category
                    ))

            if goals:
                return goals

        # PRIORITY 2.5: Parse category-prefixed goals like "[Financial] Target / Baseline..."
        # This format is common in SAP SuccessFactors exports
        category_pattern = re.compile(r'\[([^\]]+)\]\s*(.+?)(?=\[|$)', re.IGNORECASE | re.DOTALL)
        category_matches = category_pattern.findall(text)

        if category_matches:
            for cat_match in category_matches:
                category = cat_match[0].strip()
                goal_text = cat_match[1].strip()
                # Clean up goal text - remove trailing whitespace and limit length
                goal_text = ' '.join(goal_text.split())  # Normalize whitespace

                if goal_text and len(goal_text) > 10:
                    goal_num += 1
                    goals.append(self._create_goal_analysis(
                        goal_num, f"[{category}] {goal_text[:290]}", job_title, seniority, department,
                        category=category
                    ))

            if goals:
                return goals

        # PRIORITY 3: Parse from bullet points or numbered lists
        lines = text.split('\n')
        bullet_pattern = re.compile(r'^[\s]*[-•*]\s*(.+)$')
        numbered_pattern = re.compile(r'^[\s]*\d+[\.\)]\s*(.+)$')

        for line in lines:
            line = line.strip()

            # Check for bullet points
            bullet_match = bullet_pattern.match(line)
            if bullet_match:
                goal_text = bullet_match.group(1).strip()
                if len(goal_text) > 15:
                    goal_num += 1
                    goals.append(self._create_goal_analysis(
                        goal_num, goal_text[:300], job_title, seniority, department
                    ))
                continue

            # Check for numbered lists
            numbered_match = numbered_pattern.match(line)
            if numbered_match:
                goal_text = numbered_match.group(1).strip()
                if len(goal_text) > 15:
                    goal_num += 1
                    goals.append(self._create_goal_analysis(
                        goal_num, goal_text[:300], job_title, seniority, department
                    ))
                continue

        if goals:
            return goals

        # PRIORITY 4: Fallback - look for action-oriented lines
        for line in lines:
            line_lower = line.lower().strip()
            # Look for lines that might be goals based on action verbs
            action_verbs = ['reduce', 'improve', 'implement', 'achieve', 'complete',
                           'increase', 'develop', 'establish', 'launch', 'deliver',
                           'create', 'build', 'optimize', 'streamline', 'lead',
                           'manage', 'support', 'maintain', 'grow', 'expand']

            if any(verb in line_lower for verb in action_verbs) and len(line) > 20:
                # Skip header-like lines
                if not any(skip in line_lower for skip in ['employee:', 'position:', 'department:', 'level:', 'goals:']):
                    goal_num += 1
                    goals.append(self._create_goal_analysis(
                        goal_num, line.strip()[:300], job_title, seniority, department
                    ))

        # Ensure at least one goal
        if not goals:
            goals = [self._create_goal_analysis(
                1, "Unable to parse specific goals from document",
                job_title, seniority, department
            )]

        return goals

    def _create_goal_analysis(
        self,
        goal_num: int,
        goal_text: str,
        job_title: str,
        seniority: str,
        department: str,
        weight: str = '',
        category: str = ''
    ) -> Dict[str, Any]:
        """Create a goal analysis with strategy-tied scoring and role-contextualized rationales.

        Args:
            goal_num: Goal number (1-indexed)
            goal_text: The goal text
            job_title: Employee job title
            seniority: Seniority level
            department: Department name
            weight: Optional goal weight from Excel
            category: Optional goal category from Excel
        """
        # Detect goal category for objective assignment
        text_lower = goal_text.lower()
        has_metrics = any(char.isdigit() for char in goal_text) or '%' in goal_text

        is_financial_goal = (
            text_lower.startswith('[financial]') or
            (category and category.lower() == 'financial') or
            (any(indicator in text_lower for indicator in ['baseline', 'threshold', 'superior', 'target']) and
             any(curr in text_lower for curr in ['$', 's$', '€', '£']) and
             has_metrics)
        )

        # Detect People/HR goals for Learning & Growth perspective
        people_indicators = ['retention', 'engagement', 'collaboration', 'employee', 'talent',
                            'turnover', 'satisfaction', 'culture', 'workforce', 'headcount']
        is_people_goal = (
            text_lower.startswith('[people]') or
            text_lower.startswith('[hr]') or
            text_lower.startswith('[learning') or
            (category and category.lower() in ['people', 'hr', 'learning', 'talent']) or
            (any(indicator in text_lower for indicator in people_indicators) and
             any(indicator in text_lower for indicator in ['target', 'threshold', 'superior', 'score']) and
             has_metrics)
        )

        aligned_objectives = self._assign_mock_objectives(goal_num, is_financial=is_financial_goal, is_people=is_people_goal)

        # Calculate alignment score using weighted formula based on strategy tie-back
        score_breakdown = self._calculate_goal_alignment_score(
            goal_text, aligned_objectives, seniority, goal_num
        )
        alignment_score = score_breakdown['totalScore']

        # Impact score based on seniority and goal characteristics
        impact_score = self._calculate_goal_impact_score(goal_text, seniority, alignment_score)

        # Generate role-specific alignment rationale with strategy reference
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

        # Generate per-goal strategic tie-back
        strategic_tie_back = self._generate_goal_strategic_tie_back(
            goal_text, aligned_objectives
        )

        # Generate SMART assessment
        smart = self._assess_smart(goal_text)

        return {
            "goalId": f"G{goal_num}",
            "goalText": goal_text,
            "alignmentScore": alignment_score,
            "alignmentScoreBreakdown": score_breakdown,
            "impactScore": impact_score,
            "alignedObjectives": aligned_objectives,
            "strategicTieBack": strategic_tie_back,
            "alignmentRationale": alignment_rationale,
            "impactRationale": impact_rationale,
            "roleAppropriateness": role_appropriateness,
            "gaps": self._identify_gaps(goal_num, seniority),
            "smartAssessment": smart
        }

    def _calculate_goal_alignment_score(
        self,
        goal_text: str,
        aligned_objectives: List[str],
        seniority: str,
        goal_num: int
    ) -> Dict[str, Any]:
        """
        Calculate alignment score using weighted formula based on strategy tie-back.

        Weights:
        - Strategic Objective Mapping: 40%
        - Vision/Mission Connection: 30%
        - Strategic Theme Alignment: 20%
        - Role-Appropriate Translation: 10%
        """
        text_lower = goal_text.lower()

        # 1. Strategic Objective Mapping (40% weight)
        num_objectives = len(aligned_objectives)
        if num_objectives >= 2:
            obj_mapping_score = 100
            obj_rationale = f"Maps to {num_objectives} strategic objectives ({', '.join(aligned_objectives)}) with clear linkage"
        elif num_objectives == 1:
            obj_mapping_score = 70
            obj_rationale = f"Maps to objective {aligned_objectives[0]} with reasonable connection"
        else:
            obj_mapping_score = 30
            obj_rationale = "Limited connection to strategic objectives identified"

        # 2. Vision/Mission Connection (30% weight)
        # Check for keywords that indicate strategic awareness
        vision_keywords = ['leader', 'excellence', 'innovation', 'value', 'growth', 'customer', 'stakeholder']
        mission_keywords = ['deliver', 'serve', 'achieve', 'enable', 'support', 'improve']

        # Detect if this is a financial goal with specific targets
        is_financial_goal = (
            text_lower.startswith('[financial]') or
            (any(indicator in text_lower for indicator in ['baseline', 'threshold', 'superior', 'target']) and
             any(curr in text_lower for curr in ['$', 's$', '€', '£']) and
             any(char.isdigit() for char in goal_text))
        )

        vision_hits = sum(1 for kw in vision_keywords if kw in text_lower)
        mission_hits = sum(1 for kw in mission_keywords if kw in text_lower)

        # Detect People/HR goals for Learning & Growth perspective
        people_indicators = ['retention', 'engagement', 'collaboration', 'employee', 'talent',
                            'turnover', 'satisfaction', 'culture', 'workforce', 'headcount']
        has_metrics = any(char.isdigit() for char in goal_text) or '%' in goal_text
        is_people_goal = (
            text_lower.startswith('[people]') or
            text_lower.startswith('[hr]') or
            text_lower.startswith('[learning') or
            (any(indicator in text_lower for indicator in people_indicators) and
             any(indicator in text_lower for indicator in ['target', 'threshold', 'superior', 'score']) and
             has_metrics)
        )

        # Financial goals with measurable targets inherently support organizational mission
        if is_financial_goal:
            vision_mission_score = 85
            vm_rationale = (
                f"Financial goals with specific targets (baseline/threshold/superior) directly contribute "
                f"to organizational success and mission '{self.mission[:40]}...'"
            )
        # People/HR goals with measurable targets support organizational capacity
        elif is_people_goal:
            vision_mission_score = 85
            vm_rationale = (
                f"People goals with specific targets (retention/engagement/collaboration) directly contribute "
                f"to organizational capacity and mission '{self.mission[:40]}...'"
            )
        elif vision_hits >= 2 or mission_hits >= 2:
            vision_mission_score = 85
            vm_rationale = f"Goal clearly supports the vision '{self.vision[:50]}...' and mission through explicit strategic language"
        elif vision_hits >= 1 or mission_hits >= 1:
            vision_mission_score = 70
            vm_rationale = f"Goal supports the mission '{self.mission[:50]}...' without explicit reference"
        else:
            vision_mission_score = 45
            vm_rationale = "Tangential relationship to stated vision and mission"

        # 3. Strategic Theme Alignment (20% weight)
        # Check if goal text relates to any strategic themes
        theme_score = 40  # Default: no theme match
        theme_rationale = "Does not directly address identified strategic themes"

        # Financial goals with specific targets are inherently aligned with financial themes
        if is_financial_goal:
            theme_score = 90
            theme_rationale = (
                "Financial goal with measurable targets directly addresses the Financial perspective "
                "of the strategic framework. Measurable financial outcomes are core to organizational success."
            )
        # People/HR goals with specific targets are inherently aligned with Learning & Growth themes
        elif is_people_goal:
            theme_score = 90
            theme_rationale = (
                "People goal with measurable targets directly addresses the Learning & Growth perspective "
                "of the strategic framework. Employee engagement, retention, and culture are core to organizational capacity."
            )
        else:
            for theme in self.theme_names:
                theme_words = theme.lower().split()
                if any(tw in text_lower for tw in theme_words if len(tw) > 3):
                    theme_score = 85
                    theme_rationale = f"Directly addresses strategic theme: '{theme}'"
                    break

            # Also check for common theme-related terms
            theme_indicators = ['efficiency', 'customer', 'quality', 'innovation', 'digital', 'sustainability', 'growth']
            if theme_score < 85 and any(ind in text_lower for ind in theme_indicators):
                theme_score = 65
                theme_rationale = "Partially related to strategic themes through operational focus"

        # 4. Role-Appropriate Translation (10% weight)
        role_scores = {
            'executive': {'enterprise': 100, 'strategic': 90, 'team': 60, 'individual': 40},
            'senior': {'enterprise': 80, 'strategic': 100, 'team': 90, 'individual': 60},
            'mid': {'enterprise': 60, 'strategic': 80, 'team': 100, 'individual': 80},
            'junior': {'enterprise': 40, 'strategic': 60, 'team': 80, 'individual': 100}
        }

        # Detect goal scope from text
        scope = 'team'  # Default
        if any(w in text_lower for w in ['organization', 'company', 'enterprise', 'portfolio']):
            scope = 'enterprise'
        elif any(w in text_lower for w in ['strategy', 'strategic', 'vision', 'transformation']):
            scope = 'strategic'
        elif any(w in text_lower for w in ['my', 'personal', 'learn', 'skill', 'complete']):
            scope = 'individual'

        role_score = role_scores.get(seniority, role_scores['mid']).get(scope, 70)

        if role_score >= 90:
            role_rationale = f"Perfect translation of strategy for {seniority} level - appropriate scope and ambition"
        elif role_score >= 70:
            role_rationale = f"Acceptable scope for {seniority} level, could be better aligned to role expectations"
        else:
            role_rationale = f"Goal scope may be mismatched for {seniority} level position"

        # Calculate weighted total
        total_score = round(
            (obj_mapping_score * 0.40) +
            (vision_mission_score * 0.30) +
            (theme_score * 0.20) +
            (role_score * 0.10)
        )

        return {
            'totalScore': max(0, min(100, total_score)),
            'objectiveMappingScore': obj_mapping_score,
            'objectiveMappingRationale': obj_rationale,
            'visionMissionScore': vision_mission_score,
            'visionMissionRationale': vm_rationale,
            'themeAlignmentScore': theme_score,
            'themeAlignmentRationale': theme_rationale,
            'roleAppropriatenessScore': role_score,
            'roleAppropriatenessRationale': role_rationale
        }

    def _calculate_goal_impact_score(
        self,
        goal_text: str,
        seniority: str,
        alignment_score: int
    ) -> int:
        """Calculate impact score based on seniority, alignment, and goal characteristics."""
        # Base impact by seniority (higher seniority = higher potential impact)
        # New categories: individual contributor, team leader, senior management
        base_scores = {
            'senior management': 80,
            'team leader': 70,
            'individual contributor': 60,
            # Legacy mappings
            'executive': 80,
            'senior': 70,
            'mid': 60,
            'junior': 50
        }
        base = base_scores.get(seniority, 60)

        # Adjust based on goal alignment (better aligned = more impactful)
        alignment_factor = alignment_score / 100

        # Check for leverage indicators (goals that enable others)
        text_lower = goal_text.lower()
        leverage_keywords = ['enable', 'support', 'lead', 'mentor', 'establish', 'framework', 'system']
        leverage_bonus = 10 if any(kw in text_lower for kw in leverage_keywords) else 0

        # Check for measurable outcomes
        has_metrics = any(char.isdigit() for char in goal_text) or any(
            w in text_lower for w in ['%', 'percent', 'increase', 'reduce', 'improve by']
        )
        metrics_bonus = 5 if has_metrics else 0

        impact_score = round(base * alignment_factor + leverage_bonus + metrics_bonus)
        return max(0, min(100, impact_score))

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

        # New seniority categories: individual contributor, team leader, senior management
        if seniority == 'senior management' or seniority == 'executive':
            return (
                f"As a {job_title}, this goal demonstrates enterprise-level strategic thinking by "
                f"directly enabling objectives {obj_str}. The scope and ambition are appropriate for "
                f"a senior management role, focusing on outcomes that cascade throughout {department}. "
                f"This goal shows strong translation of organizational vision into leadership action. "
                f"Senior management goals should closely relate to organizational strategy and include team leadership elements."
            )
        elif seniority == 'team leader' or seniority == 'senior':
            return (
                f"This goal effectively bridges strategic intent to operational execution, which is "
                f"appropriate for a {job_title} as a team leader. It connects to objectives {obj_str} "
                f"by translating organizational priorities into actionable team initiatives within {department}. "
                f"Team leaders should have at least one goal focused on leadership or team development."
            )
        elif seniority == 'junior':
            return (
                f"For a {job_title} at an early career stage, this goal appropriately focuses on "
                f"foundational contributions that support objectives {obj_str}. It demonstrates emerging "
                f"understanding of how individual work connects to {department}'s strategic priorities, "
                f"though the linkage could be more explicitly articulated."
            )
        else:  # individual contributor (default)
            return (
                f"As a {job_title} (individual contributor), this goal reflects understanding of how "
                f"functional work contributes to organizational strategy. It supports objectives {obj_str} "
                f"through individual execution in {department}. The goal appropriately focuses on "
                f"personal contribution and technical/functional excellence."
            )

    def _generate_impact_rationale(
        self,
        goal_text: str,
        job_title: str,
        seniority: str,
        department: str
    ) -> str:
        """Generate role-contextualized impact rationale."""
        # New seniority categories: individual contributor, team leader, senior management
        if seniority == 'senior management' or seniority == 'executive':
            return (
                f"Given the {job_title} role's span of influence, successful achievement would have "
                f"significant strategic leverage, potentially enabling multiple downstream objectives "
                f"and setting direction for {department}. Impact extends beyond direct outcomes to "
                f"organizational capability building. Senior management should drive goals closely aligned "
                f"with organizational vision and strategy."
            )
        elif seniority == 'team leader' or seniority == 'senior':
            return (
                f"As a {job_title} (team leader), successful execution would demonstrate leadership in "
                f"{department} and create enabling conditions for team success. The impact multiplier "
                f"comes from both direct contribution and influence on team members' effectiveness. "
                f"Team leaders should include at least one leadership or team development goal."
            )
        elif seniority == 'junior':
            return (
                f"For a {job_title}, this goal's impact is appropriately scoped to direct individual "
                f"contribution within {department}. Success builds foundational capabilities and "
                f"demonstrates readiness for increased responsibility."
            )
        else:  # individual contributor
            return (
                f"As an individual contributor ({job_title}), this goal positions for meaningful "
                f"functional impact within {department}. Success would contribute directly to team "
                f"objectives through technical/functional excellence and individual execution."
            )

    def _generate_role_appropriateness(
        self,
        goal_text: str,
        job_title: str,
        seniority: str
    ) -> str:
        """Assess if goal is appropriate for the role/level."""
        # New seniority categories: individual contributor, team leader, senior management
        if seniority == 'senior management' or seniority == 'executive':
            return (
                f"The goal's scope is generally appropriate for a senior management {job_title} role, "
                f"focusing on strategic outcomes rather than tactical activities. Ensure "
                f"the goal emphasizes enterprise impact, leadership enablement, and aligns closely "
                f"with organizational vision and strategy."
            )
        elif seniority == 'team leader' or seniority == 'senior':
            return (
                f"This goal is well-suited for a {job_title} as a team leader, appropriately balancing "
                f"strategic alignment with operational leadership. The scope reflects expected "
                f"influence over team outcomes. Ensure at least one goal addresses leadership or team development."
            )
        elif seniority == 'junior':
            return (
                f"For a {job_title} at the junior level, this goal is appropriately focused on "
                f"skill development and direct contribution. The scope is achievable while "
                f"providing meaningful learning opportunities."
            )
        else:  # individual contributor
            return (
                f"The goal's scope and complexity are appropriate for a {job_title} as an individual "
                f"contributor, requiring technical/functional expertise and focused execution."
            )

    def _generate_role_assessment(self, job_title: str, seniority: str, goal_count: int) -> str:
        """Generate overall role appropriateness assessment."""
        # New seniority categories: individual contributor, team leader, senior management
        if seniority == 'senior management' or seniority == 'executive':
            return (
                f"As a {job_title} (senior management), the goal set should show strategic focus and "
                f"alignment with organizational vision. The {goal_count} goals should include leadership "
                f"elements and demonstrate how work cascades to enable others' success. "
                f"Senior management goals should closely relate to organizational strategy."
            )
        elif seniority == 'team leader' or seniority == 'senior':
            return (
                f"The goal set for this {job_title} (team leader) should bridge strategy and execution. "
                f"The {goal_count} goals should include at least one leadership or team development goal. "
                f"Consider strengthening cross-functional collaboration and people management elements."
            )
        elif seniority == 'junior':
            return (
                f"For a {job_title} at the junior level, this goal set appropriately emphasizes skill building "
                f"and direct contribution. The {goal_count} goals are achievable and provide clear success criteria. "
                f"Consider adding goals that demonstrate understanding of broader organizational context."
            )
        else:  # individual contributor
            return (
                f"This {job_title} (individual contributor) has a goal set focused on functional contribution "
                f"and technical excellence. The {goal_count} goals should demonstrate solid understanding of "
                f"how individual work connects to team and organizational objectives."
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

    def _generate_strategy_coherence_check(
        self,
        goals: List[Dict[str, Any]],
        department: str
    ) -> Dict[str, Any]:
        """Generate strategy-goal coherence check (mismatch detection)."""
        return {
            "confidenceScore": 85,
            "belongsToStrategy": True,
            "potentialMismatches": [],
            "assessment": (
                f"The goals for {department} appear to be well-aligned with the organizational strategy. "
                f"The goals reference themes consistent with the vision '{self.vision[:50]}...' and "
                f"support the mission of '{self.mission[:50]}...'. No significant mismatches detected "
                f"between the goal content and the strategic framework provided. The goals appear to be "
                f"written for this specific organizational context."
            )
        }

    def _generate_strategic_tie_back(
        self,
        goals: List[Dict[str, Any]],
        seniority: str
    ) -> Dict[str, str]:
        """Generate overall strategic tie-back assessment."""
        covered_themes = self.theme_names[:2] if len(self.theme_names) >= 2 else self.theme_names
        gap_themes = self.theme_names[2:] if len(self.theme_names) > 2 else []

        return {
            "visionAlignment": (
                f"The goal set connects to the organizational vision '{self.vision}' by focusing on "
                f"operational improvements and capability development that advance the organization's "
                f"strategic aspirations. The goals demonstrate understanding of the long-term direction."
            ),
            "missionContribution": (
                f"These goals support the mission '{self.mission}' through direct contribution to "
                f"key operational outcomes. The employee demonstrates awareness of how their work "
                f"enables the organization to deliver on its core purpose."
            ),
            "valuesReflected": self.values[:3] if self.values else ['Excellence', 'Integrity'],
            "strategicThemesCovered": covered_themes,
            "strategicThemesGaps": gap_themes if gap_themes else ["Learning & Growth initiatives"]
        }

    def _generate_goal_strategic_tie_back(
        self,
        goal_text: str,
        aligned_objectives: List[str]
    ) -> Dict[str, Any]:
        """Generate per-goal strategic tie-back."""
        obj_str = ", ".join(aligned_objectives)
        theme = self.theme_names[0] if self.theme_names else "Operational Excellence"

        return {
            "visionConnection": (
                f"This goal contributes to the vision '{self.vision[:60]}...' by "
                f"enabling specific operational capabilities that advance strategic positioning."
            ),
            "missionSupport": (
                f"Supports the mission '{self.mission[:60]}...' through direct contribution "
                f"to stakeholder value and organizational effectiveness."
            ),
            "strategicThemes": [theme],
            "objectiveMapping": (
                f"Maps to objectives {obj_str} because the goal directly addresses "
                f"capabilities and outcomes specified in these strategic objectives."
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

        # New seniority categories: individual contributor, team leader, senior management
        if seniority == 'senior management' or seniority == 'executive':
            base_recommendations.extend([
                "Ensure goals closely align with organizational vision and strategy",
                "Include goals that enable and cascade to leadership team success",
                "Add at least one leadership or team management goal"
            ])
        elif seniority == 'team leader' or seniority == 'senior':
            base_recommendations.extend([
                f"Add cross-functional collaboration goals within {department}",
                "Include at least one leadership or team development goal",
                "Consider goals that develop direct reports' capabilities"
            ])
        elif seniority == 'junior':
            base_recommendations.extend([
                "Add goals focused on skill development in strategic areas",
                f"Consider stretch goals that demonstrate readiness for growth in {department}"
            ])
        else:  # individual contributor
            base_recommendations.extend([
                "Add goals demonstrating functional/technical excellence",
                "Consider goals showing how individual work supports team objectives"
            ])

        return base_recommendations[:5]  # Return top 5

    def _assign_mock_objectives(self, goal_num: int, is_financial: bool = False, is_people: bool = False) -> List[str]:
        """Assign mock objective alignments.

        Args:
            goal_num: Goal number for cycling through objectives pool
            is_financial: If True, assign financial objectives (F1, F2)
            is_people: If True, assign learning & growth objectives (L1, L2)
        """
        # Financial goals get financial perspective objectives
        if is_financial:
            return ["F1", "F2"]

        # People/HR goals get learning & growth perspective objectives
        if is_people:
            return ["L1", "L2"]

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
        # New seniority categories: individual contributor, team leader, senior management
        if goal_num % 2 == 0:
            if seniority == 'senior management' or seniority == 'executive':
                return ["Goals should closely align with organizational vision and strategy",
                        "Consider adding leadership or team management goals"]
            elif seniority == 'team leader' or seniority == 'senior':
                return ["Include at least one leadership or team development goal"]
            else:  # individual contributor
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
