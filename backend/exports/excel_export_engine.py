"""
Excel Export Engine
Generates comprehensive Excel workbook consolidating all employee goal analyses.
Following openpyxl best practices.
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import RadarChart, Reference, BarChart


class ExcelExportEngine:
    """
    Generates master Excel export with all employee goal analyses.
    Creates a multi-sheet workbook following consultant-ready formatting standards.
    """

    # Color scheme matching frontend
    COLORS = {
        'high': '0D9488',      # Teal - High alignment (>80)
        'moderate': 'F59E0B',  # Amber - Moderate (50-79)
        'low': 'E11D48',       # Rose - Low (<50)
        'header': '2F5496',    # Dark blue header
        'header_alt': '4472C4',  # Alt blue header
        'success': '548235',   # Green for recommendations
        'background': 'C6EFCE',  # Light green
        'warning': 'FFEB9C',   # Light yellow
        'danger': 'FFC7CE',    # Light red
        'white': 'FFFFFF',
    }

    def __init__(
        self,
        strategic_framework: Dict[str, Any],
        analysis_results: List[Dict[str, Any]],
        recommendations: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        """
        Initialize the Excel export engine.

        Args:
            strategic_framework: Strategic framework from StrategySynthesizer
            analysis_results: List of document analysis results from AlignmentAnalyzer
            recommendations: Optional dict mapping documentId to recommendations
        """
        self.framework = strategic_framework
        self.results = analysis_results
        self.recommendations = recommendations or {}
        self.wb = Workbook()
        self._thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

    def generate_workbook(self, output_path: str) -> str:
        """
        Generate the complete Excel workbook.

        Args:
            output_path: Path to save the Excel file

        Returns:
            Path to the generated file
        """
        self._create_executive_summary_sheet()
        self._create_employee_details_sheet()
        self._create_alignment_matrix_sheet()
        self._create_recommendations_sheet()
        self._create_gap_analysis_sheet()

        # Remove default sheet if empty
        if 'Sheet' in self.wb.sheetnames and len(self.wb.sheetnames) > 1:
            del self.wb['Sheet']

        self.wb.save(output_path)
        return output_path

    def _create_executive_summary_sheet(self):
        """Create executive summary with key metrics."""
        ws = self.wb.active
        ws.title = "Executive Summary"

        # Title
        ws['A1'] = "Strategic Goal Alignment Analysis - Executive Summary"
        ws['A1'].font = Font(bold=True, size=16)
        ws.merge_cells('A1:F1')

        # Analysis metadata
        ws['A3'] = "Analysis Date:"
        ws['B3'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        ws['A3'].font = Font(bold=True)

        ws['A4'] = "Total Employees Analyzed:"
        ws['B4'] = len(self.results)
        ws['A4'].font = Font(bold=True)

        # Calculate stats from results
        valid_results = [r for r in self.results if 'error' not in r]

        ws['A5'] = "Average Alignment Score:"
        if valid_results:
            ws['B5'] = f"=AVERAGE('Employee Details'!E2:E{len(self.results)+1})"
        else:
            ws['B5'] = 0
        ws['A5'].font = Font(bold=True)

        ws['A6'] = "Average Impact Score:"
        if valid_results:
            ws['B6'] = f"=AVERAGE('Employee Details'!F2:F{len(self.results)+1})"
        else:
            ws['B6'] = 0
        ws['A6'].font = Font(bold=True)

        ws['A7'] = "Average Coherence Score:"
        if valid_results:
            ws['B7'] = f"=AVERAGE('Employee Details'!G2:G{len(self.results)+1})"
        else:
            ws['B7'] = 0
        ws['A7'].font = Font(bold=True)

        # Score Distribution by Seniority
        ws['A10'] = "Score Distribution by Seniority Level"
        ws['A10'].font = Font(bold=True, size=12)
        ws.merge_cells('A10:F10')

        # Headers for seniority breakdown
        headers = ['Seniority', 'Count', 'Avg Alignment', 'Avg Impact', 'Avg Coherence', 'Avg Composite']
        header_fill = PatternFill('solid', fgColor=self.COLORS['header'])
        header_font = Font(bold=True, color=self.COLORS['white'])

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=11, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = self._thin_border

        # Calculate seniority stats
        seniority_stats = self._calculate_seniority_stats()
        for row_idx, (level, stats) in enumerate(seniority_stats.items(), 12):
            ws.cell(row=row_idx, column=1, value=level.title()).border = self._thin_border
            ws.cell(row=row_idx, column=2, value=stats['count']).border = self._thin_border
            ws.cell(row=row_idx, column=3, value=stats['avg_alignment']).border = self._thin_border
            ws.cell(row=row_idx, column=4, value=stats['avg_impact']).border = self._thin_border
            ws.cell(row=row_idx, column=5, value=stats['avg_coherence']).border = self._thin_border
            ws.cell(row=row_idx, column=6, value=stats['avg_composite']).border = self._thin_border

        # Tier Distribution
        tier_row = 17
        ws[f'A{tier_row}'] = "Tier Distribution"
        ws[f'A{tier_row}'].font = Font(bold=True, size=12)

        tier_headers = ['Tier', 'Count', 'Percentage']
        for col, header in enumerate(tier_headers, 1):
            cell = ws.cell(row=tier_row + 1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = self._thin_border

        tier_dist = self._calculate_tier_distribution()
        tier_colors = {'High': 'high', 'Moderate': 'moderate', 'Low': 'low'}
        for row_idx, (tier, data) in enumerate(tier_dist.items(), tier_row + 2):
            tier_cell = ws.cell(row=row_idx, column=1, value=tier)
            tier_cell.fill = PatternFill('solid', fgColor=self.COLORS[tier_colors[tier]])
            tier_cell.border = self._thin_border
            ws.cell(row=row_idx, column=2, value=data['count']).border = self._thin_border
            ws.cell(row=row_idx, column=3, value=f"{data['percentage']:.1f}%").border = self._thin_border

        # Strategic Coverage Overview
        cov_row = 23
        ws[f'A{cov_row}'] = "Strategic Perspective Coverage"
        ws[f'A{cov_row}'].font = Font(bold=True, size=12)

        cov_headers = ['Perspective', 'Avg Coverage %', 'Status']
        for col, header in enumerate(cov_headers, 1):
            cell = ws.cell(row=cov_row + 1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = self._thin_border

        coverage_stats = self._calculate_perspective_coverage()
        for row_idx, (perspective, pct) in enumerate(coverage_stats.items(), cov_row + 2):
            ws.cell(row=row_idx, column=1, value=perspective.capitalize()).border = self._thin_border
            pct_cell = ws.cell(row=row_idx, column=2, value=f"{pct:.1f}%")
            pct_cell.border = self._thin_border
            status_cell = ws.cell(row=row_idx, column=3)
            if pct >= 80:
                status_cell.value = "ADEQUATE"
                status_cell.fill = PatternFill('solid', fgColor=self.COLORS['background'])
            elif pct >= 50:
                status_cell.value = "PARTIAL"
                status_cell.fill = PatternFill('solid', fgColor=self.COLORS['warning'])
            else:
                status_cell.value = "CRITICAL GAP"
                status_cell.fill = PatternFill('solid', fgColor=self.COLORS['danger'])
            status_cell.border = self._thin_border

        # Auto-fit columns
        for col in range(1, 7):
            ws.column_dimensions[get_column_letter(col)].width = 18

    def _create_employee_details_sheet(self):
        """Create master employee details with all data."""
        ws = self.wb.create_sheet("Employee Details")

        # Column headers
        headers = [
            'Employee Name',           # A
            'Job Title',               # B
            'Department',              # C
            'Seniority Level',         # D
            'Alignment Score',         # E
            'Impact Score',            # F
            'Coherence Score',         # G
            'Role Appropriateness',    # H
            'Weighted Composite',      # I
            'Tier',                    # J
            'Original Goals',          # K
            'Goal Count',              # L
            'Strategic Coverage %',    # M
            'Primary Gaps',            # N
            'Proposed Adjustment 1',   # O
            'Proposed Adjustment 2',   # P
            'Proposed Adjustment 3',   # Q
            'Proposed Adjustment 4',   # R
            'Proposed Adjustment 5',   # S
            'Projected New Score'      # T
        ]

        # Write headers with formatting
        header_fill = PatternFill('solid', fgColor=self.COLORS['header'])
        header_font = Font(bold=True, color=self.COLORS['white'])

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
            cell.border = self._thin_border

        # Freeze header row
        ws.freeze_panes = 'A2'

        # Write data rows
        for row_idx, result in enumerate(self.results, 2):
            if 'error' in result:
                # Handle error results
                ws.cell(row=row_idx, column=1, value=result.get('fileName', 'Unknown'))
                ws.cell(row=row_idx, column=5, value="ERROR")
                continue

            # Employee metadata - check both 'employeeContext' (analysis) and 'employeeMetadata' (document)
            metadata = result.get('employeeContext', {}) or result.get('employeeMetadata', {})
            ws.cell(row=row_idx, column=1, value=metadata.get('employeeName', result.get('fileName', 'Unknown')))
            ws.cell(row=row_idx, column=2, value=metadata.get('jobTitle', 'N/A'))
            ws.cell(row=row_idx, column=3, value=metadata.get('department', 'N/A'))
            ws.cell(row=row_idx, column=4, value=metadata.get('seniorityLevel', 'N/A'))

            # Scores
            alignment = result.get('overallAlignmentScore', 0)
            impact = result.get('overallImpactScore', 0)
            coherence = result.get('overallCoherenceScore', 0)
            if not coherence:
                coherence = result.get('coherenceIndex', {}).get('score', 0)

            # Role appropriateness: average of per-goal breakdown scores
            role_scores = [
                g.get('alignmentScoreBreakdown', {}).get('roleAppropriatenessScore', 0)
                for g in result.get('goals', [])
            ]
            role_scores = [s for s in role_scores if s]
            role_appropriateness = round(sum(role_scores) / len(role_scores), 1) if role_scores else 0

            ws.cell(row=row_idx, column=5, value=alignment)
            ws.cell(row=row_idx, column=6, value=impact)
            ws.cell(row=row_idx, column=7, value=coherence)
            ws.cell(row=row_idx, column=8, value=role_appropriateness)

            # Weighted composite score
            composite = result.get('weightedCompositeScore', 0)
            if not composite:
                composite = (alignment * 0.6) + (impact * 0.4)
            ws.cell(row=row_idx, column=9, value=round(composite, 1))

            # Tier formula based on composite score
            ws.cell(row=row_idx, column=10,
                    value=f'=IF(I{row_idx}>=80,"High",IF(I{row_idx}>=50,"Moderate","Low"))')

            # Original goals (concatenated)
            original_goals = "; ".join([g.get('goalText', '')[:100] for g in result.get('goals', [])])
            ws.cell(row=row_idx, column=11, value=original_goals[:500])

            ws.cell(row=row_idx, column=12, value=len(result.get('goals', [])))

            # Strategic coverage calculation
            coverage = result.get('strategicCoverage', {})
            total_covered = sum([p.get('covered', 0) for p in coverage.values()])
            total_possible = sum([p.get('total', 1) for p in coverage.values()])
            coverage_pct = (total_covered / total_possible * 100) if total_possible > 0 else 0
            ws.cell(row=row_idx, column=13, value=f"{coverage_pct:.1f}%")

            # Primary gaps from recommendations
            recs = result.get('recommendations', [])
            gaps = "; ".join(recs[:2]) if recs else "No gaps identified"
            ws.cell(row=row_idx, column=14, value=gaps[:300])

            # Get recommendations for this document
            doc_id = result.get('documentId', '')
            doc_recs = self.recommendations.get(doc_id, {}).get('recommendations', [])

            # Proposed adjustments
            for i in range(5):
                if i < len(doc_recs):
                    rec = doc_recs[i]
                    goal_obj = rec.get('revisedGoal', {}).get('objective', '')
                    ws.cell(row=row_idx, column=15+i, value=goal_obj[:200])
                else:
                    ws.cell(row=row_idx, column=15+i, value='')

            # Projected new score
            projected = self.recommendations.get(doc_id, {}).get('projectedNewAlignmentScore', '')
            ws.cell(row=row_idx, column=20, value=projected if projected else 'N/A')

        # Apply score color formatting
        self._apply_score_formatting(ws, len(self.results))

        # Auto-fit column widths
        column_widths = [20, 25, 18, 15, 12, 12, 12, 15, 15, 10, 50, 10, 15, 40, 40, 40, 40, 40, 40, 15]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

    def _create_alignment_matrix_sheet(self):
        """
        Creates heatmap-style matrix showing which employees' goals
        align to which strategic objectives.
        """
        ws = self.wb.create_sheet("Alignment Matrix")

        # Get all strategic objectives
        objectives = []
        perspectives = self.framework.get('strategicPerspectives', {})
        for p_name in ['financial', 'customer', 'internalProcess', 'learningGrowth']:
            p_data = perspectives.get(p_name, {})
            for obj in p_data.get('objectives', []):
                obj_text = f"{obj.get('id', 'X')}: {obj.get('objective', 'Unknown')[:35]}"
                objectives.append((p_name, obj.get('id', ''), obj_text))

        # Title
        ws['A1'] = "Strategic Objective Alignment Matrix"
        ws['A1'].font = Font(bold=True, size=14)
        ws.merge_cells(f'A1:{get_column_letter(len(self.results)+2)}1')

        # Headers: Employee names across columns
        header_fill = PatternFill('solid', fgColor=self.COLORS['header'])
        header_font = Font(bold=True, color=self.COLORS['white'])

        ws.cell(row=3, column=1, value="Perspective").font = header_font
        ws.cell(row=3, column=1).fill = header_fill
        ws.cell(row=3, column=2, value="Strategic Objective").font = header_font
        ws.cell(row=3, column=2).fill = header_fill

        for col, result in enumerate(self.results, 3):
            metadata = result.get('employeeContext', {}) or result.get('employeeMetadata', {})
            name = metadata.get('employeeName', result.get('fileName', f'Doc {col-2}'))
            cell = ws.cell(row=3, column=col, value=name[:15])
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', text_rotation=45)

        # Rows: Strategic objectives
        for row, (perspective, obj_id, obj_text) in enumerate(objectives, 4):
            # Perspective column
            ws.cell(row=row, column=1, value=perspective.capitalize()[:12])
            ws.cell(row=row, column=2, value=obj_text)

            for col, result in enumerate(self.results, 3):
                # Check if any of this employee's goals align to this objective
                aligned = False
                for goal in result.get('goals', []):
                    if obj_id in goal.get('alignedObjectives', []):
                        aligned = True
                        break

                cell = ws.cell(row=row, column=col)
                if aligned:
                    cell.value = "X"
                    cell.fill = PatternFill('solid', fgColor='90EE90')  # Light green
                    cell.alignment = Alignment(horizontal='center')
                else:
                    cell.value = ""
                cell.border = self._thin_border

        # Set column widths
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 40
        for col in range(3, len(self.results) + 3):
            ws.column_dimensions[get_column_letter(col)].width = 12

    def _create_recommendations_sheet(self):
        """Create recommendations summary sheet."""
        ws = self.wb.create_sheet("Recommendations")

        headers = [
            'Employee Name',
            'Current Score',
            'Recommendation #',
            'Revised Goal',
            'Strategic Linkages',
            'Projected Score Gain',
            'Evidence Source',
            'Implementation Notes'
        ]

        header_fill = PatternFill('solid', fgColor=self.COLORS['success'])
        header_font = Font(bold=True, color=self.COLORS['white'])

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = self._thin_border

        ws.freeze_panes = 'A2'

        row_idx = 2
        for result in self.results:
            if 'error' in result:
                continue

            doc_id = result.get('documentId', '')
            doc_recs = self.recommendations.get(doc_id, {}).get('recommendations', [])
            metadata = result.get('employeeContext', {}) or result.get('employeeMetadata', {})
            employee_name = metadata.get('employeeName', result.get('fileName', 'Unknown'))
            current_score = result.get('overallAlignmentScore', 0)

            if not doc_recs:
                # Add row indicating no recommendations
                ws.cell(row=row_idx, column=1, value=employee_name)
                ws.cell(row=row_idx, column=2, value=current_score)
                ws.cell(row=row_idx, column=3, value="N/A")
                ws.cell(row=row_idx, column=4, value="No recommendations generated")
                row_idx += 1
                continue

            for i, rec in enumerate(doc_recs, 1):
                ws.cell(row=row_idx, column=1, value=employee_name)
                ws.cell(row=row_idx, column=2, value=current_score)
                ws.cell(row=row_idx, column=3, value=i)

                # Revised goal
                revised_goal = rec.get('revisedGoal', {})
                goal_text = revised_goal.get('objective', '')
                ws.cell(row=row_idx, column=4, value=goal_text[:200])

                # Strategic linkages
                linkages = rec.get('strategicLinkages', [])
                ws.cell(row=row_idx, column=5, value=", ".join(linkages))

                # Projected score gain
                gain = rec.get('predictedAlignmentGain', 0)
                ws.cell(row=row_idx, column=6, value=f"+{gain}" if gain > 0 else str(gain))

                # Evidence
                evidence = rec.get('evidence', {})
                ws.cell(row=row_idx, column=7, value=evidence.get('source', 'N/A'))

                # Implementation notes
                ws.cell(row=row_idx, column=8, value=rec.get('implementationNotes', 'N/A'))

                row_idx += 1

        # Set column widths
        column_widths = [20, 12, 15, 50, 20, 15, 30, 40]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

    def _create_gap_analysis_sheet(self):
        """Create gap analysis sheet."""
        ws = self.wb.create_sheet("Gap Analysis")

        # Title
        ws['A1'] = "Strategic Objective Gap Analysis"
        ws['A1'].font = Font(bold=True, size=14)
        ws.merge_cells('A1:F1')

        # Calculate objective coverage
        objective_coverage = self._calculate_objective_coverage()

        headers = ['Objective ID', 'Objective', 'Perspective', 'Coverage Count', 'Employees Covering', 'Gap Status']
        header_fill = PatternFill('solid', fgColor=self.COLORS['header'])
        header_font = Font(bold=True, color=self.COLORS['white'])

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = self._thin_border

        ws.freeze_panes = 'A4'

        for row, (obj_id, data) in enumerate(objective_coverage.items(), 4):
            ws.cell(row=row, column=1, value=obj_id).border = self._thin_border
            ws.cell(row=row, column=2, value=data['objective'][:50]).border = self._thin_border
            ws.cell(row=row, column=3, value=data['perspective'].capitalize()).border = self._thin_border
            ws.cell(row=row, column=4, value=data['coverage_count']).border = self._thin_border

            covered_names = ", ".join(data['covered_by'][:5])
            if len(data['covered_by']) > 5:
                covered_names += f" (+{len(data['covered_by']) - 5} more)"
            ws.cell(row=row, column=5, value=covered_names).border = self._thin_border

            # Gap status with conditional formatting
            gap_cell = ws.cell(row=row, column=6)
            if data['coverage_count'] == 0:
                gap_cell.value = "CRITICAL GAP"
                gap_cell.fill = PatternFill('solid', fgColor=self.COLORS['danger'])
            elif data['coverage_count'] < 3:
                gap_cell.value = "PARTIAL COVERAGE"
                gap_cell.fill = PatternFill('solid', fgColor=self.COLORS['warning'])
            else:
                gap_cell.value = "ADEQUATE"
                gap_cell.fill = PatternFill('solid', fgColor=self.COLORS['background'])
            gap_cell.border = self._thin_border

        # Summary section
        summary_row = len(objective_coverage) + 6
        ws.cell(row=summary_row, column=1, value="Summary").font = Font(bold=True, size=12)

        critical_gaps = sum(1 for d in objective_coverage.values() if d['coverage_count'] == 0)
        partial_coverage = sum(1 for d in objective_coverage.values() if 0 < d['coverage_count'] < 3)
        adequate = sum(1 for d in objective_coverage.values() if d['coverage_count'] >= 3)

        ws.cell(row=summary_row + 1, column=1, value="Critical Gaps:")
        ws.cell(row=summary_row + 1, column=2, value=critical_gaps)
        ws.cell(row=summary_row + 2, column=1, value="Partial Coverage:")
        ws.cell(row=summary_row + 2, column=2, value=partial_coverage)
        ws.cell(row=summary_row + 3, column=1, value="Adequate Coverage:")
        ws.cell(row=summary_row + 3, column=2, value=adequate)

        # Set column widths
        column_widths = [15, 50, 15, 15, 40, 18]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

    def _apply_score_formatting(self, ws, num_rows: int):
        """Apply conditional formatting to score columns."""
        # Score columns: E (Alignment), F (Impact), G (Coherence), H (Role), I (Composite)
        score_columns = ['E', 'F', 'G', 'H', 'I']

        for row in range(2, num_rows + 2):
            for col in score_columns:
                cell = ws[f'{col}{row}']
                if cell.value and isinstance(cell.value, (int, float)):
                    if cell.value >= 80:
                        cell.fill = PatternFill('solid', fgColor=self.COLORS['background'])
                    elif cell.value >= 50:
                        cell.fill = PatternFill('solid', fgColor=self.COLORS['warning'])
                    else:
                        cell.fill = PatternFill('solid', fgColor=self.COLORS['danger'])

    # Canonical seniority buckets emitted by GoalsTableProcessor._infer_seniority.
    # Must stay in sync with frontend/src/lib/seniority.ts so the dashboard
    # filter and this export report identical headcounts.
    SENIORITY_LEVELS = ['senior management', 'team leader', 'individual contributor']
    SENIORITY_UNSPECIFIED = 'seniority not stated'

    def _calculate_seniority_stats(self) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics by seniority level.

        Employees with no seniority recorded are reported under their own
        'seniority not stated' bucket rather than being dropped, so the totals
        here reconcile with the dashboard's filter counts.
        """
        seniority_data = {}
        levels = self.SENIORITY_LEVELS + [self.SENIORITY_UNSPECIFIED]

        for level in levels:
            if level == self.SENIORITY_UNSPECIFIED:
                level_results = [
                    r for r in self.results
                    if 'error' not in r
                    and not ((r.get('employeeContext', {}) or r.get('employeeMetadata', {})).get('seniorityLevel') or '').strip()
                ]
            else:
                level_results = [
                    r for r in self.results
                    if ((r.get('employeeContext', {}) or r.get('employeeMetadata', {})).get('seniorityLevel') or '').lower().strip() == level
                    and 'error' not in r
                ]

            if level_results:
                avg_alignment = sum(r.get('overallAlignmentScore', 0) for r in level_results) / len(level_results)
                avg_impact = sum(r.get('overallImpactScore', 0) for r in level_results) / len(level_results)
                avg_coherence = sum(
                    r.get('overallCoherenceScore', 0) or r.get('coherenceIndex', {}).get('score', 0)
                    for r in level_results
                ) / len(level_results)
                avg_composite = (avg_alignment * 0.6) + (avg_impact * 0.4)
            else:
                avg_alignment = avg_impact = avg_coherence = avg_composite = 0

            seniority_data[level] = {
                'count': len(level_results),
                'avg_alignment': round(avg_alignment, 1),
                'avg_impact': round(avg_impact, 1),
                'avg_coherence': round(avg_coherence, 1),
                'avg_composite': round(avg_composite, 1)
            }

        return seniority_data

    def _calculate_tier_distribution(self) -> Dict[str, Dict[str, Any]]:
        """Calculate tier distribution."""
        tier_counts = {'High': 0, 'Moderate': 0, 'Low': 0}
        valid_results = [r for r in self.results if 'error' not in r]

        for result in valid_results:
            alignment = result.get('overallAlignmentScore', 0)
            impact = result.get('overallImpactScore', 0)
            composite = (alignment * 0.6) + (impact * 0.4)

            if composite >= 80:
                tier_counts['High'] += 1
            elif composite >= 50:
                tier_counts['Moderate'] += 1
            else:
                tier_counts['Low'] += 1

        total = len(valid_results) if valid_results else 1
        return {
            tier: {'count': count, 'percentage': (count / total) * 100}
            for tier, count in tier_counts.items()
        }

    def _calculate_perspective_coverage(self) -> Dict[str, float]:
        """Calculate average coverage per perspective."""
        perspectives = ['financial', 'customer', 'process', 'learning']
        coverage_totals = {p: [] for p in perspectives}

        for result in self.results:
            if 'error' in result:
                continue
            coverage = result.get('strategicCoverage', {})
            for p in perspectives:
                if p in coverage:
                    coverage_totals[p].append(coverage[p].get('percentage', 0))

        return {
            p: sum(values) / len(values) if values else 0
            for p, values in coverage_totals.items()
        }

    def _calculate_objective_coverage(self) -> Dict[str, Dict[str, Any]]:
        """Calculate coverage for each strategic objective."""
        objective_coverage = {}

        perspectives = self.framework.get('strategicPerspectives', {})
        for p_name in ['financial', 'customer', 'internalProcess', 'learningGrowth']:
            p_data = perspectives.get(p_name, {})
            for obj in p_data.get('objectives', []):
                obj_id = obj.get('id', '')
                covered_by = []

                for result in self.results:
                    if 'error' in result:
                        continue
                    metadata = result.get('employeeContext', {}) or result.get('employeeMetadata', {})
                    employee_name = metadata.get('employeeName', result.get('fileName', 'Unknown'))

                    for goal in result.get('goals', []):
                        if obj_id in goal.get('alignedObjectives', []):
                            covered_by.append(employee_name)
                            break

                objective_coverage[obj_id] = {
                    'objective': obj.get('objective', ''),
                    'perspective': p_name,
                    'coverage_count': len(set(covered_by)),
                    'covered_by': list(set(covered_by))
                }

        return objective_coverage


def generate_excel_export(
    strategic_framework: Dict[str, Any],
    analysis_results: List[Dict[str, Any]],
    recommendations: Optional[Dict[str, Dict[str, Any]]] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Convenience function to generate Excel export.

    Args:
        strategic_framework: Strategic framework data
        analysis_results: List of analysis results
        recommendations: Optional recommendations dict
        output_path: Optional output path (defaults to temp file)

    Returns:
        Path to generated Excel file
    """
    if not output_path:
        import tempfile
        output_path = tempfile.mktemp(suffix='.xlsx')

    engine = ExcelExportEngine(strategic_framework, analysis_results, recommendations)
    return engine.generate_workbook(output_path)
