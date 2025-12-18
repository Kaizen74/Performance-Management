"""
PDF Export Engine
Generates PDF reports from analysis results using ReportLab.
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class PDFExportEngine:
    """
    Generates PDF reports from strategic goal alignment analysis.
    Creates a professional consultant-ready document.
    """

    # Color scheme matching frontend
    COLORS = {
        'high': colors.Color(13/255, 148/255, 136/255),      # Teal
        'moderate': colors.Color(245/255, 158/255, 11/255),  # Amber
        'low': colors.Color(225/255, 29/255, 72/255),        # Rose
        'header': colors.Color(47/255, 84/255, 150/255),     # Dark blue
        'text': colors.black,
        'light_gray': colors.Color(0.9, 0.9, 0.9),
    }

    def __init__(
        self,
        strategic_framework: Dict[str, Any],
        analysis_results: List[Dict[str, Any]],
        recommendations: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        """
        Initialize the PDF export engine.

        Args:
            strategic_framework: Strategic framework from StrategySynthesizer
            analysis_results: List of document analysis results
            recommendations: Optional dict mapping documentId to recommendations
        """
        self.framework = strategic_framework
        self.results = analysis_results
        self.recommendations = recommendations or {}
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=self.COLORS['header'],
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=self.COLORS['header']
        ))

        self.styles.add(ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=8,
            textColor=self.COLORS['header']
        ))

        self.styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8
        ))

        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray
        ))

    def generate_report(self, output_path: str) -> str:
        """
        Generate the complete PDF report.

        Args:
            output_path: Path to save the PDF file

        Returns:
            Path to the generated file
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        story = []

        # Title page
        story.extend(self._create_title_page())
        story.append(PageBreak())

        # Executive summary
        story.extend(self._create_executive_summary())
        story.append(PageBreak())

        # Strategic framework summary
        story.extend(self._create_framework_summary())
        story.append(PageBreak())

        # Analysis results
        story.extend(self._create_analysis_section())

        # Gap analysis
        story.extend(self._create_gap_analysis_section())

        # Portfolio Strategic Analysis (Coherence)
        story.extend(self._create_portfolio_strategic_analysis())

        # Recommendations overview
        if self.recommendations:
            story.append(PageBreak())
            story.extend(self._create_recommendations_section())

        doc.build(story)
        return output_path

    def _create_title_page(self) -> List:
        """Create title page content."""
        elements = []

        elements.append(Spacer(1, 2*inch))

        elements.append(Paragraph(
            "Strategic Goal Alignment Analysis",
            self.styles['CustomTitle']
        ))

        elements.append(Spacer(1, 0.5*inch))

        org_name = self.framework.get('organizationalPurpose', {}).get('vision', 'Organization')[:50]
        elements.append(Paragraph(
            f"<b>Organization:</b> {org_name}...",
            ParagraphStyle('CenterBody', parent=self.styles['CustomBodyText'], alignment=TA_CENTER)
        ))

        elements.append(Spacer(1, 0.3*inch))

        elements.append(Paragraph(
            f"<b>Report Date:</b> {datetime.now().strftime('%B %d, %Y')}",
            ParagraphStyle('CenterBody', parent=self.styles['CustomBodyText'], alignment=TA_CENTER)
        ))

        elements.append(Paragraph(
            f"<b>Documents Analyzed:</b> {len(self.results)}",
            ParagraphStyle('CenterBody', parent=self.styles['CustomBodyText'], alignment=TA_CENTER)
        ))

        elements.append(Spacer(1, 1.5*inch))

        elements.append(Paragraph(
            "Generated by Strategic Goal Alignment Analyzer (SGAA)",
            self.styles['SmallText']
        ))

        return elements

    def _create_executive_summary(self) -> List:
        """Create executive summary section."""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))

        valid_results = [r for r in self.results if 'error' not in r]

        # Key metrics
        if valid_results:
            avg_alignment = sum(r.get('overallAlignmentScore', 0) for r in valid_results) / len(valid_results)
            avg_impact = sum(r.get('overallImpactScore', 0) for r in valid_results) / len(valid_results)
        else:
            avg_alignment = avg_impact = 0

        metrics_data = [
            ['Metric', 'Value'],
            ['Total Employees Analyzed', str(len(self.results))],
            ['Average Alignment Score', f"{avg_alignment:.1f}"],
            ['Average Impact Score', f"{avg_impact:.1f}"],
        ]

        metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['header']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.gray),
        ]))
        elements.append(metrics_table)

        elements.append(Spacer(1, 0.3*inch))

        # Tier distribution
        elements.append(Paragraph("Tier Distribution", self.styles['SubSection']))

        tier_counts = {'High': 0, 'Moderate': 0, 'Low': 0}
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

        tier_data = [['Tier', 'Count', 'Description']]
        tier_colors_map = {
            'High': (self.COLORS['high'], 'Strong Strategic Fit'),
            'Moderate': (self.COLORS['moderate'], 'Partial Alignment'),
            'Low': (self.COLORS['low'], 'Requires Revision')
        }

        for tier, count in tier_counts.items():
            tier_data.append([tier, str(count), tier_colors_map[tier][1]])

        tier_table = Table(tier_data, colWidths=[1.5*inch, 1*inch, 3*inch])
        tier_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['header']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.gray),
        ]))
        elements.append(tier_table)

        elements.append(Spacer(1, 0.3*inch))

        # Key findings
        elements.append(Paragraph("Key Findings", self.styles['SubSection']))

        findings = self._generate_key_findings()
        for finding in findings:
            elements.append(Paragraph(f"- {finding}", self.styles['CustomBodyText']))

        return elements

    def _create_framework_summary(self) -> List:
        """Create strategic framework summary section."""
        elements = []

        elements.append(Paragraph("Strategic Framework Summary", self.styles['SectionHeader']))

        purpose = self.framework.get('organizationalPurpose', {})

        # Vision and Mission
        elements.append(Paragraph("Vision", self.styles['SubSection']))
        elements.append(Paragraph(
            purpose.get('vision', 'Not specified')[:300],
            self.styles['CustomBodyText']
        ))

        elements.append(Paragraph("Mission", self.styles['SubSection']))
        elements.append(Paragraph(
            purpose.get('mission', 'Not specified')[:300],
            self.styles['CustomBodyText']
        ))

        # Strategic Perspectives
        elements.append(Paragraph("Strategic Perspectives (Balanced Scorecard)", self.styles['SubSection']))

        perspectives = self.framework.get('strategicPerspectives', {})
        for p_name, display_name in [
            ('financial', 'Financial'),
            ('customer', 'Customer'),
            ('internalProcess', 'Internal Process'),
            ('learningGrowth', 'Learning & Growth')
        ]:
            p_data = perspectives.get(p_name, {})
            objectives = p_data.get('objectives', [])

            elements.append(Paragraph(f"<b>{display_name}</b> ({len(objectives)} objectives)", self.styles['CustomBodyText']))

            for obj in objectives[:3]:  # Show first 3
                obj_text = f"  - {obj.get('id', '')}: {obj.get('objective', '')[:60]}..."
                elements.append(Paragraph(obj_text, self.styles['SmallText']))

            if len(objectives) > 3:
                elements.append(Paragraph(f"  ... and {len(objectives) - 3} more", self.styles['SmallText']))

        return elements

    def _create_analysis_section(self) -> List:
        """Create detailed analysis results section."""
        elements = []

        elements.append(Paragraph("Individual Analysis Results", self.styles['SectionHeader']))

        # Summary table
        table_data = [['Employee', 'Alignment', 'Impact', 'Tier']]

        for result in self.results:
            if 'error' in result:
                continue

            metadata = result.get('employeeContext', {}) or result.get('employeeMetadata', {})
            name = metadata.get('employeeName', result.get('fileName', 'Unknown'))[:25]
            alignment = result.get('overallAlignmentScore', 0)
            impact = result.get('overallImpactScore', 0)
            composite = (alignment * 0.6) + (impact * 0.4)

            if composite >= 80:
                tier = 'High'
            elif composite >= 50:
                tier = 'Moderate'
            else:
                tier = 'Low'

            table_data.append([name, str(alignment), str(impact), tier])

        if len(table_data) > 1:
            summary_table = Table(table_data, colWidths=[3*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['header']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.gray),
            ]))
            elements.append(summary_table)
        else:
            elements.append(Paragraph("No valid analysis results available.", self.styles['CustomBodyText']))

        return elements

    def _create_gap_analysis_section(self) -> List:
        """Create gap analysis section."""
        elements = []

        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("Gap Analysis", self.styles['SectionHeader']))

        # Calculate objective coverage
        objective_coverage = self._calculate_objective_coverage()

        critical_gaps = [
            (obj_id, data) for obj_id, data in objective_coverage.items()
            if data['coverage_count'] == 0
        ]

        if critical_gaps:
            elements.append(Paragraph("Critical Gaps (No Coverage)", self.styles['SubSection']))
            for obj_id, data in critical_gaps[:5]:
                elements.append(Paragraph(
                    f"- {obj_id}: {data['objective'][:60]}... ({data['perspective']})",
                    self.styles['CustomBodyText']
                ))
            if len(critical_gaps) > 5:
                elements.append(Paragraph(f"... and {len(critical_gaps) - 5} more", self.styles['SmallText']))
        else:
            elements.append(Paragraph("No critical gaps identified - all strategic objectives have some coverage.", self.styles['CustomBodyText']))

        return elements

    def _create_portfolio_strategic_analysis(self) -> List:
        """Create portfolio strategic analysis (coherence) section."""
        elements = []

        # Calculate aggregate coherence metrics from analysis results
        portfolio_coherence = {
            'avg_score': 0,
            'total_strategic_drivers': 0,
            'total_busy_work': 0,
            'total_rogue_projects': 0,
            'total_distractions': 0,
            'analyses_with_coherence': 0,
        }

        for result in self.results:
            if 'error' in result:
                continue

            coherence_index = result.get('coherenceIndex')
            if coherence_index:
                portfolio_coherence['avg_score'] += coherence_index.get('score', 0)
                quadrant_dist = coherence_index.get('quadrantDistribution', {})
                portfolio_coherence['total_strategic_drivers'] += quadrant_dist.get('Strategic Driver', 0)
                portfolio_coherence['total_busy_work'] += quadrant_dist.get('Busy Work Trap', 0)
                portfolio_coherence['total_rogue_projects'] += quadrant_dist.get('Rogue Project', 0)
                portfolio_coherence['total_distractions'] += quadrant_dist.get('Distraction', 0)
                portfolio_coherence['analyses_with_coherence'] += 1

        # Skip section if no coherence data available
        if portfolio_coherence['analyses_with_coherence'] == 0:
            return elements

        # Calculate average
        portfolio_coherence['avg_score'] = round(
            portfolio_coherence['avg_score'] / portfolio_coherence['analyses_with_coherence']
        )

        total_goals = (
            portfolio_coherence['total_strategic_drivers'] +
            portfolio_coherence['total_busy_work'] +
            portfolio_coherence['total_rogue_projects'] +
            portfolio_coherence['total_distractions']
        )

        elements.append(PageBreak())
        elements.append(Paragraph("Portfolio Strategic Analysis", self.styles['SectionHeader']))

        # Coherence Score Summary
        elements.append(Paragraph("Portfolio Coherence Index", self.styles['SubSection']))

        avg_score = portfolio_coherence['avg_score']
        if avg_score >= 80:
            verdict = "Highly Aligned"
            verdict_color = self.COLORS['high']
        elif avg_score >= 50:
            verdict = "Operationally Weak"
            verdict_color = self.COLORS['moderate']
        else:
            verdict = "Strategic Drift"
            verdict_color = self.COLORS['low']

        coherence_data = [
            ['Metric', 'Value'],
            ['Average Coherence Score', f"{avg_score}%"],
            ['Overall Assessment', verdict],
            ['Documents Analyzed', str(portfolio_coherence['analyses_with_coherence'])],
            ['Total Goals Classified', str(total_goals)],
        ]

        coherence_table = Table(coherence_data, colWidths=[3*inch, 2*inch])
        coherence_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['header']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.gray),
        ]))
        elements.append(coherence_table)

        elements.append(Spacer(1, 0.3*inch))

        # Goal Classification Distribution
        elements.append(Paragraph("Goal Classification Distribution", self.styles['SubSection']))

        quadrant_data = [
            ['Category', 'Count', 'Percentage', 'Description'],
            [
                'Strategic Drivers',
                str(portfolio_coherence['total_strategic_drivers']),
                f"{round((portfolio_coherence['total_strategic_drivers'] / max(total_goals, 1)) * 100)}%",
                'High alignment + outcome-focused'
            ],
            [
                'Busy Work Traps',
                str(portfolio_coherence['total_busy_work']),
                f"{round((portfolio_coherence['total_busy_work'] / max(total_goals, 1)) * 100)}%",
                'Aligned but activity-focused'
            ],
            [
                'Rogue Projects',
                str(portfolio_coherence['total_rogue_projects']),
                f"{round((portfolio_coherence['total_rogue_projects'] / max(total_goals, 1)) * 100)}%",
                'Outcome-focused but misaligned'
            ],
            [
                'Distractions',
                str(portfolio_coherence['total_distractions']),
                f"{round((portfolio_coherence['total_distractions'] / max(total_goals, 1)) * 100)}%",
                'Low alignment + activity-focused'
            ],
        ]

        quadrant_table = Table(quadrant_data, colWidths=[1.5*inch, 0.8*inch, 1*inch, 2.5*inch])
        quadrant_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['header']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, 1), colors.Color(0.9, 1, 0.95)),  # Light green for Strategic Drivers
            ('BACKGROUND', (0, 2), (-1, 2), colors.Color(1, 0.98, 0.9)),  # Light amber for Busy Work
            ('BACKGROUND', (0, 3), (-1, 3), colors.Color(1, 0.95, 0.9)),  # Light orange for Rogue
            ('BACKGROUND', (0, 4), (-1, 4), colors.Color(0.95, 0.95, 0.95)),  # Light gray for Distractions
            ('ALIGN', (1, 1), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.gray),
        ]))
        elements.append(quadrant_table)

        elements.append(Spacer(1, 0.3*inch))

        # Executive Summary Narrative
        elements.append(Paragraph("Executive Summary", self.styles['SubSection']))

        strategic_pct = round((portfolio_coherence['total_strategic_drivers'] / max(total_goals, 1)) * 100)

        if avg_score >= 80:
            summary = f"Strong strategic execution posture. {strategic_pct}% of goals qualify as Strategic Drivers with clear outcome orientation and strategy linkage."
        elif avg_score >= 50:
            summary = f"Moderate strategic alignment with execution gaps. Only {strategic_pct}% of goals are Strategic Drivers. The remaining {100 - strategic_pct}% represent efficiency loss or strategic drift."
        else:
            summary = f"Critical strategic drift detected. Just {strategic_pct}% of goals drive strategic outcomes. The portfolio requires substantial revision to align with organizational priorities."

        elements.append(Paragraph(summary, self.styles['CustomBodyText']))

        elements.append(Spacer(1, 0.2*inch))

        # Risk Analysis
        risks = []
        if portfolio_coherence['total_busy_work'] > 0:
            busy_pct = round((portfolio_coherence['total_busy_work'] / max(total_goals, 1)) * 100)
            risks.append(f"Busy Work Trap ({portfolio_coherence['total_busy_work']} goals, {busy_pct}%): Goals show strategic intent but measure activities instead of outcomes.")

        if portfolio_coherence['total_rogue_projects'] > 0:
            rogue_pct = round((portfolio_coherence['total_rogue_projects'] / max(total_goals, 1)) * 100)
            risks.append(f"Rogue Projects ({portfolio_coherence['total_rogue_projects']} goals, {rogue_pct}%): Well-formed outcome goals that don't connect to current strategy.")

        if portfolio_coherence['total_distractions'] > 0:
            distraction_pct = round((portfolio_coherence['total_distractions'] / max(total_goals, 1)) * 100)
            risks.append(f"Distractions ({portfolio_coherence['total_distractions']} goals, {distraction_pct}%): Neither outcome-focused nor strategically aligned.")

        if risks:
            elements.append(Paragraph("Risk Analysis", self.styles['SubSection']))
            for risk in risks:
                elements.append(Paragraph(f"• {risk}", self.styles['CustomBodyText']))

        elements.append(Spacer(1, 0.2*inch))

        # Priority Actions
        elements.append(Paragraph("Priority Actions", self.styles['SubSection']))

        actions = []
        if portfolio_coherence['total_distractions'] > 0:
            actions.append(f"Eliminate or redesign {portfolio_coherence['total_distractions']} distraction goal(s) that consume resources without strategic value")

        if portfolio_coherence['total_busy_work'] > 2:
            actions.append(f"Convert {portfolio_coherence['total_busy_work']} output-focused goals to outcome statements with measurable success criteria")

        if portfolio_coherence['total_rogue_projects'] > 0:
            actions.append(f"Anchor {portfolio_coherence['total_rogue_projects']} rogue project(s) to specific strategic themes or reconsider strategic priorities")

        if avg_score < 70:
            actions.append("Conduct goal-writing workshops focusing on the Rigor × Alignment framework")

        if strategic_pct < 50:
            actions.append(f"Target minimum 50% Strategic Drivers in next goal-setting cycle (currently {strategic_pct}%)")

        if not actions:
            actions.append("Continue maintaining strong strategic alignment across the portfolio")

        for i, action in enumerate(actions, 1):
            elements.append(Paragraph(f"{i}. {action}", self.styles['CustomBodyText']))

        return elements

    def _create_recommendations_section(self) -> List:
        """Create recommendations overview section."""
        elements = []

        elements.append(Paragraph("Recommendations Overview", self.styles['SectionHeader']))

        elements.append(Paragraph(
            "The following recommendations have been generated to improve strategic alignment:",
            self.styles['CustomBodyText']
        ))

        for result in self.results[:5]:  # Show first 5 employees
            if 'error' in result:
                continue

            doc_id = result.get('documentId', '')
            doc_recs = self.recommendations.get(doc_id, {}).get('recommendations', [])

            if not doc_recs:
                continue

            metadata = result.get('employeeContext', {}) or result.get('employeeMetadata', {})
            name = metadata.get('employeeName', result.get('fileName', 'Unknown'))

            elements.append(Paragraph(f"<b>{name}</b>", self.styles['SubSection']))

            for rec in doc_recs[:2]:  # Show first 2 recommendations per person
                goal = rec.get('revisedGoal', {}).get('objective', '')[:80]
                gain = rec.get('predictedAlignmentGain', 0)
                elements.append(Paragraph(
                    f"- {goal}... (Projected gain: +{gain} points)",
                    self.styles['CustomBodyText']
                ))

        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(
            "For complete recommendations, please refer to the Excel export.",
            self.styles['SmallText']
        ))

        return elements

    def _generate_key_findings(self) -> List[str]:
        """Generate key findings from analysis."""
        findings = []
        valid_results = [r for r in self.results if 'error' not in r]

        if not valid_results:
            return ["No valid analyses to generate findings."]

        # Average alignment
        avg_alignment = sum(r.get('overallAlignmentScore', 0) for r in valid_results) / len(valid_results)
        if avg_alignment >= 75:
            findings.append(f"Overall strong strategic alignment (avg: {avg_alignment:.0f})")
        elif avg_alignment >= 50:
            findings.append(f"Moderate strategic alignment with room for improvement (avg: {avg_alignment:.0f})")
        else:
            findings.append(f"Significant alignment gaps require attention (avg: {avg_alignment:.0f})")

        # Tier distribution insight
        low_count = sum(
            1 for r in valid_results
            if (r.get('overallAlignmentScore', 0) * 0.6 + r.get('overallImpactScore', 0) * 0.4) < 50
        )
        if low_count > 0:
            pct = (low_count / len(valid_results)) * 100
            findings.append(f"{pct:.0f}% of employees require goal revision (Low tier)")

        # Coverage gaps
        objective_coverage = self._calculate_objective_coverage()
        critical_gaps = sum(1 for d in objective_coverage.values() if d['coverage_count'] == 0)
        if critical_gaps > 0:
            findings.append(f"{critical_gaps} strategic objectives have no employee goal coverage")

        return findings

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

                    for goal in result.get('goals', []):
                        if obj_id in goal.get('alignedObjectives', []):
                            covered_by.append(result.get('fileName', 'Unknown'))
                            break

                objective_coverage[obj_id] = {
                    'objective': obj.get('objective', ''),
                    'perspective': p_name,
                    'coverage_count': len(set(covered_by)),
                    'covered_by': list(set(covered_by))
                }

        return objective_coverage


def generate_pdf_export(
    strategic_framework: Dict[str, Any],
    analysis_results: List[Dict[str, Any]],
    recommendations: Optional[Dict[str, Dict[str, Any]]] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Convenience function to generate PDF export.

    Args:
        strategic_framework: Strategic framework data
        analysis_results: List of analysis results
        recommendations: Optional recommendations dict
        output_path: Optional output path (defaults to temp file)

    Returns:
        Path to generated PDF file
    """
    if not output_path:
        import tempfile
        output_path = tempfile.mktemp(suffix='.pdf')

    engine = PDFExportEngine(strategic_framework, analysis_results, recommendations)
    return engine.generate_report(output_path)
