import { useAnalysis } from '../contexts/AnalysisContext';

export function DocumentScorecard() {
  const {
    selectedDocumentId,
    goalAnalyses,
    goalDocuments,
    setCurrentStep,
    selectDocument,
    calculateTier,
  } = useAnalysis();

  // Find the selected analysis (or use mock data)
  const analysis = goalAnalyses.find((a) => a.documentId === selectedDocumentId) || {
    documentId: selectedDocumentId || 'mock',
    fileName: goalDocuments.find((d) => d.documentId === selectedDocumentId)?.fileName || 'Document',
    overallAlignmentScore: 72,
    overallImpactScore: 68,
    goals: [
      {
        goalId: 'G1',
        goalText: 'Reduce warehouse processing time by 20% through lean methodology',
        alignmentScore: 85,
        impactScore: 80,
        alignedObjectives: ['P1', 'P3'],
        alignmentRationale: 'Direct support for operational efficiency and process improvement objectives',
        impactRationale: 'High strategic leverage with measurable cost reduction impact',
        gaps: [],
      },
      {
        goalId: 'G2',
        goalText: 'Implement new inventory management system by Q2',
        alignmentScore: 78,
        impactScore: 75,
        alignedObjectives: ['P1', 'L1'],
        alignmentRationale: 'Supports digital transformation initiative',
        impactRationale: 'Enables multiple downstream improvements',
        gaps: ['No direct customer impact measured'],
      },
      {
        goalId: 'G3',
        goalText: 'Achieve team engagement score of 4.2/5.0',
        alignmentScore: 65,
        impactScore: 55,
        alignedObjectives: ['L2'],
        alignmentRationale: 'Links to employee engagement objective',
        impactRationale: 'Important but indirect strategic impact',
        gaps: ['Could strengthen link to business outcomes'],
      },
      {
        goalId: 'G4',
        goalText: 'Complete Six Sigma Green Belt certification',
        alignmentScore: 58,
        impactScore: 45,
        alignedObjectives: ['L1'],
        alignmentRationale: 'Supports capability building',
        impactRationale: 'Individual development goal with limited direct strategic impact',
        gaps: ['Missing connection to specific improvement projects'],
      },
    ],
    strategicCoverage: {
      financial: { covered: 0, total: 2, percentage: 0 },
      customer: { covered: 0, total: 2, percentage: 0 },
      process: { covered: 2, total: 3, percentage: 67 },
      learning: { covered: 2, total: 2, percentage: 100 },
    },
    recommendations: [
      'Add goals addressing customer satisfaction metrics',
      'Include financial impact targets in process improvement goals',
      'Strengthen connection between certification and specific projects',
    ],
  };

  const tier = calculateTier(analysis.overallAlignmentScore, analysis.overallImpactScore);

  return (
    <div className="space-y-6" data-testid="document-scorecard">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">
              {analysis.fileName}
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              {analysis.goals.length} goals analyzed
            </p>
          </div>
          <div
            className={`
              px-4 py-2 rounded-lg text-center
              ${tier.tier === 'high'
                ? 'bg-teal-100 text-teal-800'
                : tier.tier === 'moderate'
                ? 'bg-amber-100 text-amber-800'
                : 'bg-rose-100 text-rose-800'
              }
            `}
          >
            <p className="text-2xl font-bold">{Math.round(tier.composite)}</p>
            <p className="text-xs">{tier.label}</p>
          </div>
        </div>

        {/* Score Cards */}
        <div className="grid grid-cols-2 gap-4 mt-6">
          <div className="bg-slate-50 rounded-lg p-4 text-center">
            <p className="text-sm text-slate-500">Alignment Score</p>
            <p className="text-3xl font-bold text-slate-900 mt-1">
              {analysis.overallAlignmentScore}
            </p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4 text-center">
            <p className="text-sm text-slate-500">Impact Score</p>
            <p className="text-3xl font-bold text-slate-900 mt-1">
              {analysis.overallImpactScore}
            </p>
          </div>
        </div>
      </div>

      {/* Strategic Coverage */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Strategic Coverage
        </h3>
        <div className="space-y-3">
          {Object.entries(analysis.strategicCoverage).map(([perspective, data]) => (
            <div key={perspective}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-slate-600 capitalize">{perspective}</span>
                <span className="text-sm font-medium text-slate-900">
                  {data.covered}/{data.total} ({data.percentage}%)
                </span>
              </div>
              <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    data.percentage >= 80
                      ? 'bg-teal-500'
                      : data.percentage >= 50
                      ? 'bg-amber-400'
                      : 'bg-rose-400'
                  }`}
                  style={{ width: `${data.percentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Coherence Index Analysis */}
      {analysis.coherenceIndex && (
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">
            Strategy Coherence Assessment
          </h3>

          {/* Coherence Score Banner */}
          <div className={`rounded-lg p-4 mb-4 ${
            analysis.coherenceIndex.score >= 80
              ? 'bg-teal-50 border border-teal-200'
              : analysis.coherenceIndex.score >= 50
              ? 'bg-amber-50 border border-amber-200'
              : 'bg-rose-50 border border-rose-200'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">Coherence Index</p>
                <p className={`text-3xl font-bold ${
                  analysis.coherenceIndex.score >= 80
                    ? 'text-teal-700'
                    : analysis.coherenceIndex.score >= 50
                    ? 'text-amber-700'
                    : 'text-rose-700'
                }`}>
                  {analysis.coherenceIndex.score}%
                </p>
              </div>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                analysis.coherenceIndex.score >= 80
                  ? 'bg-teal-100 text-teal-800'
                  : analysis.coherenceIndex.score >= 50
                  ? 'bg-amber-100 text-amber-800'
                  : 'bg-rose-100 text-rose-800'
              }`}>
                {analysis.coherenceIndex.verdict}
              </div>
            </div>
          </div>

          {/* Quadrant Distribution */}
          <div className="mb-4">
            <p className="text-sm font-medium text-slate-700 mb-2">Goal Classification Matrix</p>
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-teal-50 border border-teal-200 rounded p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-teal-700">Strategic Drivers</span>
                  <span className="text-lg font-bold text-teal-800">
                    {analysis.coherenceIndex.quadrantDistribution['Strategic Driver']}
                  </span>
                </div>
                <p className="text-xs text-teal-600 mt-1">Aligned + Outcome (100 pts)</p>
              </div>
              <div className="bg-amber-50 border border-amber-200 rounded p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-amber-700">Busy Work Traps</span>
                  <span className="text-lg font-bold text-amber-800">
                    {analysis.coherenceIndex.quadrantDistribution['Busy Work Trap']}
                  </span>
                </div>
                <p className="text-xs text-amber-600 mt-1">Aligned + Output (50 pts)</p>
              </div>
              <div className="bg-orange-50 border border-orange-200 rounded p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-orange-700">Rogue Projects</span>
                  <span className="text-lg font-bold text-orange-800">
                    {analysis.coherenceIndex.quadrantDistribution['Rogue Project']}
                  </span>
                </div>
                <p className="text-xs text-orange-600 mt-1">Misaligned + Outcome (25 pts)</p>
              </div>
              <div className="bg-slate-100 border border-slate-200 rounded p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-700">Distractions</span>
                  <span className="text-lg font-bold text-slate-800">
                    {analysis.coherenceIndex.quadrantDistribution['Distraction']}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1">Misaligned + Output (0 pts)</p>
              </div>
            </div>
          </div>

          {/* Pillar Coverage */}
          {analysis.coherenceIndex.pillarCoverage && (
            <div className="mb-4">
              <p className="text-sm font-medium text-slate-700 mb-2">
                Strategic Pillar Coverage: {analysis.coherenceIndex.pillarCoverage.coveragePercentage}%
              </p>
              {analysis.coherenceIndex.pillarCoverage.uncoveredPillars.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded p-3">
                  <p className="text-sm font-medium text-amber-800">Under-Supported Pillars:</p>
                  <p className="text-sm text-amber-700 mt-1">
                    {analysis.coherenceIndex.pillarCoverage.uncoveredPillars.join(', ')}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Strategic Narrative */}
      {analysis.strategicNarrative && (
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">
            Strategic Analysis Narrative
          </h3>
          <div className="space-y-4">
            {/* Alignment Section */}
            <div className="border-l-4 border-blue-500 pl-4">
              <h4 className="text-sm font-semibold text-slate-700 mb-2">Alignment Analysis</h4>
              <p className="text-sm text-slate-600 whitespace-pre-line">
                {analysis.strategicNarrative.alignmentNarrative}
              </p>
            </div>

            {/* Rigor Section */}
            <div className="border-l-4 border-purple-500 pl-4">
              <h4 className="text-sm font-semibold text-slate-700 mb-2">Rigor Analysis</h4>
              <p className="text-sm text-slate-600 whitespace-pre-line">
                {analysis.strategicNarrative.rigorNarrative}
              </p>
            </div>

            {/* Orphan Check */}
            <div className="border-l-4 border-orange-500 pl-4">
              <h4 className="text-sm font-semibold text-slate-700 mb-2">Strategic Coverage Check</h4>
              <p className="text-sm text-slate-600 whitespace-pre-line">
                {analysis.strategicNarrative.orphanCheck}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Individual Goals */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Goal Analysis
        </h3>
        <div className="space-y-4">
          {analysis.goals.map((goal) => {
            const goalTier = calculateTier(goal.alignmentScore, goal.impactScore);
            const quadrant = goal.quadrantClassification;
            return (
              <div
                key={goal.goalId}
                className={`
                  border-l-4 rounded-r-lg p-4 bg-slate-50
                  ${goalTier.tier === 'high'
                    ? 'border-teal-500'
                    : goalTier.tier === 'moderate'
                    ? 'border-amber-500'
                    : 'border-rose-500'
                  }
                `}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-xs font-mono text-slate-500">{goal.goalId}</span>
                      {quadrant && (
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                          quadrant.quadrant === 'Strategic Driver'
                            ? 'bg-teal-100 text-teal-700'
                            : quadrant.quadrant === 'Busy Work Trap'
                            ? 'bg-amber-100 text-amber-700'
                            : quadrant.quadrant === 'Rogue Project'
                            ? 'bg-orange-100 text-orange-700'
                            : 'bg-slate-200 text-slate-600'
                        }`}>
                          {quadrant.quadrant} ({quadrant.points} pts)
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium text-slate-900">
                      {goal.goalText}
                    </p>
                  </div>
                  <div className="flex items-center space-x-3 ml-4">
                    <div className="text-center">
                      <p className="text-xs text-slate-500">Align</p>
                      <p className="text-lg font-bold text-slate-900">{goal.alignmentScore}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-slate-500">Impact</p>
                      <p className="text-lg font-bold text-slate-900">{goal.impactScore}</p>
                    </div>
                  </div>
                </div>

                {/* Quadrant Details */}
                {quadrant && (
                  <div className="mt-2 flex flex-wrap gap-2 text-xs">
                    <span className={`px-2 py-1 rounded ${
                      quadrant.rigorCheck.isOutcome
                        ? 'bg-green-100 text-green-700'
                        : 'bg-slate-100 text-slate-600'
                    }`}>
                      {quadrant.rigorCheck.isOutcome ? '✓ Outcome' : '○ Output'}
                      {quadrant.rigorCheck.verbDetected && ` (${quadrant.rigorCheck.verbDetected})`}
                    </span>
                    <span className={`px-2 py-1 rounded ${
                      quadrant.alignmentCheck.isAligned
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-slate-100 text-slate-600'
                    }`}>
                      {quadrant.alignmentCheck.isAligned ? '✓ Aligned' : '○ Misaligned'}
                    </span>
                    {quadrant.alignmentCheck.alignedThemes.length > 0 && (
                      <span className="px-2 py-1 rounded bg-purple-100 text-purple-700">
                        Themes: {quadrant.alignmentCheck.alignedThemes.join(', ')}
                      </span>
                    )}
                  </div>
                )}

                <div className="mt-3 space-y-2 text-sm">
                  <div>
                    <span className="text-slate-500">Linked Objectives: </span>
                    <span className="font-mono text-slate-700">
                      {goal.alignedObjectives.join(', ') || 'None'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Alignment: </span>
                    <span className="text-slate-700">{goal.alignmentRationale}</span>
                  </div>

                  {/* Score Breakdown */}
                  {goal.alignmentScoreBreakdown && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-blue-600 hover:text-blue-700 text-xs font-medium">
                        View Score Breakdown
                      </summary>
                      <div className="mt-2 bg-slate-100 rounded p-3 space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span>Objective Mapping (40%)</span>
                          <span className="font-medium">{goal.alignmentScoreBreakdown.objectiveMappingScore}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Vision/Mission (30%)</span>
                          <span className="font-medium">{goal.alignmentScoreBreakdown.visionMissionScore}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Theme Alignment (20%)</span>
                          <span className="font-medium">{goal.alignmentScoreBreakdown.themeAlignmentScore}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Role Fit (10%)</span>
                          <span className="font-medium">{goal.alignmentScoreBreakdown.roleAppropriatenessScore}</span>
                        </div>
                      </div>
                    </details>
                  )}

                  {/* Strategic Tie-Back */}
                  {goal.strategicTieBack && goal.strategicTieBack.visionConnection && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-blue-600 hover:text-blue-700 text-xs font-medium">
                        View Strategy Tie-Back
                      </summary>
                      <div className="mt-2 bg-blue-50 rounded p-3 space-y-2 text-xs">
                        <div>
                          <span className="font-medium text-blue-800">Vision Connection: </span>
                          <span className="text-blue-700">{goal.strategicTieBack.visionConnection}</span>
                        </div>
                        {goal.strategicTieBack.strategicThemes.length > 0 && (
                          <div>
                            <span className="font-medium text-blue-800">Strategic Themes: </span>
                            <span className="text-blue-700">{goal.strategicTieBack.strategicThemes.join(', ')}</span>
                          </div>
                        )}
                      </div>
                    </details>
                  )}

                  {goal.gaps.length > 0 && (
                    <div className="bg-amber-50 text-amber-800 px-3 py-2 rounded">
                      <span className="font-medium">Gaps: </span>
                      {goal.gaps.join('; ')}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recommendations Preview */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Initial Recommendations
        </h3>
        <ul className="space-y-2">
          {analysis.recommendations.map((rec, i) => (
            <li key={i} className="flex items-start space-x-2">
              <span className="text-blue-600">•</span>
              <span className="text-slate-700">{rec}</span>
            </li>
          ))}
        </ul>
        <button
          onClick={() => setCurrentStep('recommendations')}
          className="mt-4 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          View Detailed Recommendations
        </button>
      </div>

      {/* Navigation */}
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
      </div>
    </div>
  );
}
