import { useAnalysis, GoalRecommendation } from '../contexts/AnalysisContext';

// Mock recommendations for demonstration
const MOCK_RECOMMENDATIONS: GoalRecommendation[] = [
  {
    recommendationId: 'R1',
    revisedGoal: {
      objective: 'Lead digital transformation initiative for warehouse operations',
      keyResults: [
        'Deploy AI-powered inventory forecasting by Q2',
        'Achieve 25% reduction in stockouts',
        'Train 100% of warehouse staff on new system',
      ],
      timeline: 'Q2 2025',
      metrics: ['System uptime', 'Forecast accuracy', 'Training completion rate'],
    },
    strategicLinkages: ['P1', 'L1', 'C2'],
    predictedAlignmentGain: 15,
    evidence: {
      source: 'McKinsey Digital Operations Report 2024',
      finding: 'AI-driven forecasting reduces stockouts by 20-35%',
    },
    implementationNotes: 'Requires IT partnership and change management plan',
  },
  {
    recommendationId: 'R2',
    revisedGoal: {
      objective: 'Implement sustainability metrics in operations',
      keyResults: [
        'Reduce carbon emissions per shipment by 15%',
        'Achieve 90% waste diversion rate',
        'Complete sustainability reporting framework',
      ],
      timeline: 'Q4 2025',
      metrics: ['Carbon per unit', 'Waste diversion %', 'Reporting compliance'],
    },
    strategicLinkages: ['P2', 'F2'],
    predictedAlignmentGain: 12,
    evidence: {
      source: 'World Economic Forum Sustainability Report',
      finding: 'Operational sustainability improves margin by 3-5%',
    },
    implementationNotes: 'Align with corporate sustainability team',
  },
  {
    recommendationId: 'R3',
    revisedGoal: {
      objective: 'Establish customer feedback loop for service improvement',
      keyResults: [
        'Implement real-time delivery tracking with NPS survey',
        'Achieve response rate of 30% on delivery feedback',
        'Reduce customer complaints by 25%',
      ],
      timeline: 'Q3 2025',
      metrics: ['Survey response rate', 'NPS score', 'Complaint volume'],
    },
    strategicLinkages: ['C1', 'C2', 'P3'],
    predictedAlignmentGain: 18,
    evidence: {
      source: 'Harvard Business Review - Customer Feedback Systems',
      finding: 'Real-time feedback improves NPS by 10-15 points',
    },
    implementationNotes: 'Requires CX team collaboration and IT support',
  },
  {
    recommendationId: 'R4',
    revisedGoal: {
      objective: 'Develop continuous improvement culture through Lean Six Sigma',
      keyResults: [
        'Complete LSS Green Belt certification',
        'Lead 3 improvement projects with measurable ROI',
        'Train 5 team members in basic LSS tools',
      ],
      timeline: 'Q4 2025',
      metrics: ['Certifications', 'Project ROI', 'Team training hours'],
    },
    strategicLinkages: ['L1', 'L2', 'P3'],
    predictedAlignmentGain: 10,
    evidence: {
      source: 'ASQ Quality Progress Survey',
      finding: 'LSS projects average 4:1 ROI',
    },
    implementationNotes: 'Budget needed for certification program',
  },
  {
    recommendationId: 'R5',
    revisedGoal: {
      objective: 'Drive cost optimization through process automation',
      keyResults: [
        'Identify and automate 5 manual processes',
        'Achieve $300K in annual cost savings',
        'Improve process cycle time by 30%',
      ],
      timeline: 'Q4 2025',
      metrics: ['Processes automated', 'Cost savings', 'Cycle time'],
    },
    strategicLinkages: ['F2', 'P3', 'P1'],
    predictedAlignmentGain: 14,
    evidence: {
      source: 'Deloitte Automation Survey 2024',
      finding: 'Process automation delivers 15-25% cost reduction',
    },
    implementationNotes: 'Cross-functional project requiring RPA tools',
  },
];

export function RecommendationsPanel() {
  const { selectedDocumentId, recommendations, setCurrentStep, selectDocument } = useAnalysis();

  // Use mock if no real recommendations
  const recSet = recommendations.get(selectedDocumentId || '') || {
    documentId: selectedDocumentId || 'mock',
    recommendations: MOCK_RECOMMENDATIONS,
    projectedNewAlignmentScore: 88,
    projectedNewImpactScore: 82,
  };

  return (
    <div className="space-y-6" data-testid="recommendations-panel">
      {/* Summary */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg shadow-lg p-6 text-white">
        <h2 className="text-2xl font-bold mb-2">AI-Powered Recommendations</h2>
        <p className="opacity-90 mb-4">
          {recSet.recommendations.length} strategic goal improvements identified
        </p>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white/10 rounded-lg p-4">
            <p className="text-sm opacity-75">Projected Alignment</p>
            <p className="text-3xl font-bold">{recSet.projectedNewAlignmentScore}</p>
            <p className="text-sm text-green-300">
              +{recSet.projectedNewAlignmentScore - 72} improvement
            </p>
          </div>
          <div className="bg-white/10 rounded-lg p-4">
            <p className="text-sm opacity-75">Projected Impact</p>
            <p className="text-3xl font-bold">{recSet.projectedNewImpactScore}</p>
            <p className="text-sm text-green-300">
              +{recSet.projectedNewImpactScore - 68} improvement
            </p>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="space-y-4">
        {recSet.recommendations.map((rec, index) => (
          <div
            key={rec.recommendationId}
            className="bg-white rounded-lg shadow-sm border border-slate-200 p-6"
            data-testid="recommendation-card"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold">
                  {index + 1}
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">
                    {rec.revisedGoal.objective}
                  </h3>
                  <p className="text-sm text-slate-500">
                    Timeline: {rec.revisedGoal.timeline}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-500">Alignment Gain</p>
                <p className="text-lg font-bold text-green-600">
                  +{rec.predictedAlignmentGain}
                </p>
              </div>
            </div>

            {/* Key Results */}
            <div className="mb-4">
              <p className="text-sm font-medium text-slate-700 mb-2">Key Results</p>
              <ul className="space-y-1">
                {rec.revisedGoal.keyResults.map((kr, i) => (
                  <li key={i} className="flex items-start space-x-2 text-sm">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span className="text-slate-600">{kr}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Metrics */}
            <div className="mb-4">
              <p className="text-sm font-medium text-slate-700 mb-2">Metrics</p>
              <div className="flex flex-wrap gap-2">
                {rec.revisedGoal.metrics.map((metric) => (
                  <span
                    key={metric}
                    className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs"
                  >
                    {metric}
                  </span>
                ))}
              </div>
            </div>

            {/* Strategic Linkages */}
            <div className="mb-4">
              <p className="text-sm font-medium text-slate-700 mb-2">Strategic Linkages</p>
              <div className="flex flex-wrap gap-2">
                {rec.strategicLinkages.map((link) => (
                  <span
                    key={link}
                    className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-mono"
                  >
                    {link}
                  </span>
                ))}
              </div>
            </div>

            {/* Evidence */}
            <div className="bg-slate-50 rounded-lg p-4">
              <p className="text-sm font-medium text-slate-700 mb-1">Evidence</p>
              <p className="text-sm text-slate-600 italic">"{rec.evidence.finding}"</p>
              <p className="text-xs text-slate-500 mt-1">— {rec.evidence.source}</p>
            </div>

            {/* Implementation Notes */}
            {rec.implementationNotes && (
              <div className="mt-4 pt-4 border-t border-slate-200">
                <p className="text-sm text-slate-500">
                  <span className="font-medium">Note:</span> {rec.implementationNotes}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between">
          <button
            onClick={() => {
              selectDocument(null);
              setCurrentStep('dashboard');
            }}
            className="text-slate-600 hover:text-slate-800 transition-colors"
          >
            ← Back to Dashboard
          </button>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => {
                // Copy to clipboard
                const text = recSet.recommendations
                  .map((r) => `${r.revisedGoal.objective}\n${r.revisedGoal.keyResults.join('\n')}`)
                  .join('\n\n');
                navigator.clipboard.writeText(text);
              }}
              className="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 transition-colors"
            >
              Copy Goals
            </button>
            <button
              onClick={() => setCurrentStep('export')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Export Reports
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
